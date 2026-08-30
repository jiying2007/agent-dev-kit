"""Versioned direct-target contracts and the single rendering adapter registry."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .model import (
    Asset,
    Manifest,
    ManifestError,
    ProfileResolution,
    canonical_json_bytes,
    ensure_within,
    sha256_bytes,
)
from .privacy_ref import validate_no_secrets


CONTRACT_SCHEMA = "adk-target-contract/v2"
CHECK_SCHEMA = "adk-target-check/v1"
SMOKE_SCHEMA = "adk-target-smoke/v1"
ASSET_KINDS = ("agent", "skill")
MAX_SOURCE_AGE_DAYS = 90


class TargetUsageError(ManifestError):
    """A stable target/install contract usage error (CLI exit 2)."""


@dataclass(frozen=True)
class TargetContract:
    name: str
    path: Path
    data: Mapping[str, Any]

    @property
    def digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.data))

    @property
    def status(self) -> str:
        return str(self.data["status"])

    @property
    def supported_asset_kinds(self) -> Tuple[str, ...]:
        return tuple(str(item) for item in self.data["supported_asset_kinds"])

    @property
    def smoke_stages(self) -> Tuple[str, ...]:
        return tuple(str(item) for item in self.data["smoke_stages"])

    @property
    def adapter(self) -> Mapping[str, Any]:
        value = self.data.get("adapter")
        if not isinstance(value, dict):
            raise ManifestError(
                "target_contract_invalid: target={} adapter is missing".format(self.name)
            )
        return value

    def layout(self, kind: str, name: str) -> str:
        layouts = self.data["layouts"]
        if not isinstance(layouts, dict) or kind not in layouts:
            raise TargetUsageError(
                "unsupported_asset_kind: target={} kind={}".format(self.name, kind)
            )
        try:
            rendered = str(layouts[kind]).format(name=name)
        except (KeyError, ValueError) as exc:
            raise ManifestError(
                "target_contract_invalid: target={} invalid layout for {}".format(self.name, kind)
            ) from exc
        candidate = Path(rendered)
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.name:
            raise ManifestError(
                "target_contract_invalid: target={} unsafe layout {}".format(self.name, rendered)
            )
        return candidate.as_posix()


@dataclass(frozen=True)
class RenderedFile:
    kind: str
    name: str
    source: str
    destination: str
    content: bytes
    mode: int

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.content)


@dataclass(frozen=True)
class RenderedBundle:
    target: str
    contract: TargetContract
    resolution: ProfileResolution
    optional_skills: Tuple[str, ...]
    asset_kind: Optional[str]
    assets: Tuple[Asset, ...]
    files: Tuple[RenderedFile, ...]

    @property
    def agent_count(self) -> int:
        return sum(1 for item in self.assets if item.kind == "agent")

    @property
    def skill_count(self) -> int:
        return sum(1 for item in self.assets if item.kind == "skill")


def _json_object(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink():
        raise ManifestError("{} must not be a symlink: {}".format(label, path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid JSON: {}".format(label, path)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} must be a JSON object: {}".format(label, path))
    return value


def _schema_failures(value: Mapping[str, Any], schema: Mapping[str, Any]) -> List[str]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures: List[str] = []
    for error in sorted(
        validator.iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    ):
        location = "/".join(str(item) for item in error.absolute_path) or "<root>"
        failures.append("{}: {}".format(location, error.message))
    return failures


def _native_contract_digest(value: Mapping[str, Any]) -> str:
    normalized = json.loads(json.dumps(value))
    try:
        conformance = normalized["adapter"]["conformance"]
        conformance["evidence"] = []
        conformance["last_verified_at"] = None
    except (KeyError, TypeError) as exc:
        raise ManifestError("target_contract_invalid: native conformance shape is invalid") from exc
    return sha256_bytes(canonical_json_bytes(normalized))


def _receipt_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ManifestError("target_contract_invalid: {} must be a timestamp".format(field))
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ManifestError(
            "target_contract_invalid: {} must be an RFC3339 timestamp".format(field)
        ) from exc
    if parsed.tzinfo is None:
        raise ManifestError(
            "target_contract_invalid: {} must include a timezone".format(field)
        )
    return parsed.astimezone(timezone.utc)


def _authority_digest(authority: Mapping[str, Any]) -> str:
    body = {
        "execution_authority": authority.get("execution_authority"),
        "authority_id": authority.get("authority_id"),
        "scope": authority.get("scope"),
    }
    return sha256_bytes(canonical_json_bytes(body))


def _validate_native_receipt(
    receipt: Mapping[str, Any],
    *,
    target: str,
    conformance: Mapping[str, Any],
    evidence: Mapping[str, Any],
    contract_digest: str,
    trusted_authorities: Sequence[str],
    now: datetime,
) -> datetime:
    if receipt.get("target") != target:
        raise ManifestError(
            "target_contract_invalid: native receipt target mismatch for {}".format(target)
        )
    runtime = receipt.get("runtime")
    if not isinstance(runtime, dict):
        raise ManifestError("target_contract_invalid: native receipt runtime is missing")
    identity_pairs = (
        ("binary", conformance.get("runtime_binary")),
        ("binary_sha256", conformance.get("runtime_binary_sha256")),
        ("version", conformance.get("runtime_version")),
        ("version_pin", conformance.get("runtime_version_pin")),
    )
    for field, expected in identity_pairs:
        if runtime.get(field) != expected:
            raise ManifestError(
                "target_contract_invalid: native receipt runtime {} mismatch for {}".format(
                    field, target
                )
            )
    if runtime.get("version") != runtime.get("version_pin"):
        raise ManifestError(
            "target_contract_invalid: native runtime version must be exactly pinned for {}".format(
                target
            )
        )
    if receipt.get("bundle_sha256") != evidence.get("bundle_sha256"):
        raise ManifestError(
            "target_contract_invalid: native receipt bundle digest mismatch for {}".format(target)
        )
    if receipt.get("contract_sha256") != contract_digest:
        raise ManifestError(
            "target_contract_invalid: native receipt contract digest mismatch for {}".format(target)
        )
    if evidence.get("contract_sha256") != contract_digest:
        raise ManifestError(
            "target_contract_invalid: native evidence contract digest mismatch for {}".format(target)
        )

    verified_at = _receipt_timestamp(receipt.get("verified_at"), "receipt.verified_at")
    if verified_at > now:
        raise ManifestError(
            "target_contract_invalid: native receipt is dated in the future for {}".format(target)
        )
    stages = receipt.get("stages")
    if not isinstance(stages, list) or [item.get("stage") for item in stages if isinstance(item, dict)] != [
        "discovery", "load", "trigger"
    ]:
        raise ManifestError(
            "target_contract_invalid: native receipt requires ordered discovery/load/trigger stages"
        )
    command_digests = [item.get("command_sha256") for item in stages]
    result_digests = [item.get("result_sha256") for item in stages]
    if len(set(command_digests)) != len(stages) or len(set(result_digests)) != len(stages):
        raise ManifestError(
            "target_contract_invalid: native stages require independent command and result evidence"
        )

    previous_completed: Optional[datetime] = None
    for stage in stages:
        stage_name = str(stage["stage"])
        started_at = _receipt_timestamp(stage.get("started_at"), stage_name + ".started_at")
        completed_at = _receipt_timestamp(stage.get("completed_at"), stage_name + ".completed_at")
        if started_at > completed_at or completed_at > verified_at or completed_at > now:
            raise ManifestError(
                "target_contract_invalid: native stage time order is invalid for {}".format(stage_name)
            )
        if previous_completed is not None and started_at < previous_completed:
            raise ManifestError(
                "target_contract_invalid: native conformance stages overlap or are out of order"
            )
        elapsed_ms = int((completed_at - started_at).total_seconds() * 1000)
        if abs(int(stage["duration_ms"]) - elapsed_ms) > 1000:
            raise ManifestError(
                "target_contract_invalid: native stage duration does not match timestamps for {}".format(
                    stage_name
                )
            )
        environment = stage["environment"]
        expected_environment = {
            "runtime_binary_sha256": runtime["binary_sha256"],
            "bundle_sha256": receipt["bundle_sha256"],
            "contract_sha256": contract_digest,
        }
        if any(environment.get(key) != value for key, value in expected_environment.items()):
            raise ManifestError(
                "target_contract_invalid: native stage environment identity mismatch for {}".format(
                    stage_name
                )
            )
        authority = stage["authority"]
        if authority.get("authority_id") not in trusted_authorities:
            raise ManifestError(
                "target_contract_invalid: native stage authority is not trusted for {}".format(
                    stage_name
                )
            )
        if authority.get("scope") != stage_name:
            raise ManifestError(
                "target_contract_invalid: native stage authority scope mismatch for {}".format(
                    stage_name
                )
            )
        if authority.get("attestation_sha256") != _authority_digest(authority):
            raise ManifestError(
                "target_contract_invalid: native stage authority attestation mismatch for {}".format(
                    stage_name
                )
            )
        previous_completed = completed_at
    return verified_at


def _validate_native_conformance_evidence(
    manifest: Manifest,
    target: str,
    adapter: Mapping[str, Any],
    contract_data: Optional[Mapping[str, Any]] = None,
    trust_verifier: Optional[
        Callable[[Mapping[str, Any], Mapping[str, Any]], bool]
    ] = None,
) -> None:
    conformance = adapter.get("conformance", {})
    if not isinstance(conformance, dict) or conformance.get("level") != "runtime":
        return
    if contract_data is None:
        raise ManifestError("target_contract_invalid: native contract data is missing")
    trust_policy = adapter.get("conformance_trust_policy")
    if not isinstance(trust_policy, dict) or trust_policy.get("enabled") is not True:
        raise ManifestError(
            "target_contract_untrusted: native conformance trust policy is disabled for {}".format(
                target
            )
        )
    trusted_authorities = trust_policy.get("trusted_authorities")
    if not isinstance(trusted_authorities, list) or not trusted_authorities:
        raise ManifestError(
            "target_contract_untrusted: native conformance has no trusted authorities for {}".format(
                target
            )
        )
    if trust_policy.get("verification_backend") == "not-configured":
        raise ManifestError(
            "target_contract_untrusted: native verification backend is not configured for {}".format(
                target
            )
        )
    if trust_verifier is None:
        raise ManifestError(
            "target_contract_untrusted: native trust verifier is not injected for {}".format(target)
        )
    runtime_version = conformance.get("runtime_version")
    contract_digest = _native_contract_digest(contract_data)
    receipt_schema = _json_object(
        manifest.root / "schemas" / "native-target-conformance-receipt-v1.schema.json",
        "native target conformance receipt schema",
    )
    now = datetime.now(timezone.utc)
    verified_times: List[datetime] = []
    for item in conformance.get("evidence", []):
        if not isinstance(item, dict):
            raise ManifestError("target_contract_invalid: native evidence must be typed")
        if item.get("target") != target or item.get("runtime_version") != runtime_version:
            raise ManifestError(
                "target_contract_invalid: native evidence identity mismatch for {}".format(target)
            )
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ManifestError("target_contract_invalid: native evidence path is missing")
        path = ensure_within(manifest.root / raw_path, manifest.root, "native target evidence")
        if path.suffix != ".json" or path.is_symlink() or not path.is_file():
            raise ManifestError(
                "target_contract_invalid: native evidence is missing or unsafe for {}".format(target)
            )
        actual = sha256_bytes(path.read_bytes())
        if item.get("sha256") != actual:
            raise ManifestError(
                "target_contract_invalid: native evidence digest mismatch for {}".format(target)
            )
        receipt = _json_object(path, "native target conformance receipt")
        validate_no_secrets(receipt, "native target conformance receipt")
        failures = _schema_failures(receipt, receipt_schema)
        if failures:
            raise ManifestError(
                "target_contract_invalid: native receipt schema failure for {}: {}".format(
                    target, "; ".join(failures)
                )
            )
        if item.get("receipt_schema") != receipt.get("schema"):
            raise ManifestError(
                "target_contract_invalid: native receipt schema identity mismatch for {}".format(
                    target
                )
            )
        verified_times.append(
            _validate_native_receipt(
                receipt,
                target=target,
                conformance=conformance,
                evidence=item,
                contract_digest=contract_digest,
                trusted_authorities=tuple(str(value) for value in trusted_authorities),
                now=now,
            )
        )
        try:
            trusted = trust_verifier(receipt, trust_policy)
        except Exception as exc:
            raise ManifestError(
                "target_contract_untrusted: native trust verifier failed for {}".format(target)
            ) from exc
        if trusted is not True:
            raise ManifestError(
                "target_contract_untrusted: native receipt was not verified for {}".format(target)
            )
    last_verified_at = _receipt_timestamp(
        conformance.get("last_verified_at"), "conformance.last_verified_at"
    )
    if last_verified_at > now or not verified_times or max(verified_times) != last_verified_at:
        raise ManifestError(
            "target_contract_invalid: conformance last_verified_at is not receipt-backed for {}".format(
                target
            )
        )


def load_target_contract(manifest: Manifest, target: str) -> TargetContract:
    config = manifest.target(target)
    raw_path = config.get("contract")
    if not isinstance(raw_path, str) or not raw_path:
        raise ManifestError("target_contract_missing: target={}".format(target))
    path = ensure_within(manifest.root / raw_path, manifest.root, "target contract")
    if not path.is_file():
        raise ManifestError("target_contract_missing: target={} path={}".format(target, raw_path))
    schema_path = manifest.root / "manifests" / "target-contract.schema.json"
    schema = _json_object(schema_path, "target contract schema")
    data = _json_object(path, "target contract")
    failures = _schema_failures(data, schema)
    if failures:
        raise ManifestError(
            "target_contract_invalid: target={} {}".format(target, "; ".join(failures))
        )
    if data.get("schema") != CONTRACT_SCHEMA or data.get("target") != target:
        raise ManifestError("target_contract_invalid: target identity mismatch for {}".format(target))
    try:
        retrieved_at = date.fromisoformat(str(data["source"]["retrieved_at"]))
        expires_at = date.fromisoformat(str(data["source"]["expires_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ManifestError("target_contract_invalid: target source dates are invalid for {}".format(target)) from exc
    if retrieved_at > date.today() or expires_at <= retrieved_at:
        raise ManifestError("target_contract_invalid: target source date order is invalid for {}".format(target))
    if (expires_at - retrieved_at).days > MAX_SOURCE_AGE_DAYS:
        raise ManifestError(
            "target_contract_invalid: target source freshness exceeds {} days for {}".format(
                MAX_SOURCE_AGE_DAYS, target
            )
        )
    if expires_at < date.today():
        raise ManifestError(
            "target_contract_stale: target={} expires_at={}".format(target, expires_at.isoformat())
        )
    supported = tuple(str(item) for item in data["supported_asset_kinds"])
    layouts = data["layouts"]
    frontmatter = data["frontmatter"]
    if set(supported) != set(layouts) or set(supported) != set(frontmatter):
        raise ManifestError(
            "target_contract_invalid: supported kinds/layouts/frontmatter differ for {}".format(target)
        )
    invocation = data.get("skill_invocation")
    if not isinstance(invocation, dict):
        raise ManifestError(
            "target_contract_incompatible: target={} missing skill_invocation".format(target)
        )
    supported_modes = invocation["supported_modes"]
    explicit_frontmatter = invocation["explicit_only_frontmatter"]
    if "explicit-only" not in supported_modes and explicit_frontmatter:
        raise ManifestError(
            "target_contract_invalid: target={} has explicit-only mapping without support".format(target)
        )
    if "explicit-only" in supported_modes and not explicit_frontmatter:
        raise ManifestError(
            "target_contract_invalid: target={} supports explicit-only without mapping".format(target)
        )
    contract = TargetContract(target, path, data)
    adapter = contract.adapter
    _validate_native_conformance_evidence(manifest, target, adapter, data)
    capabilities = adapter.get("capabilities", {})
    for stage in contract.smoke_stages:
        if capabilities.get(stage) == "unsupported":
            raise ManifestError(
                "target_contract_invalid: target={} smoke stage {} is unsupported by adapter".format(
                    target, stage
                )
            )
    for kind in supported:
        contract.layout(kind, "contract-probe")
    return contract


def _content_path(asset: Asset) -> Path:
    return asset.path / ("AGENTS.md" if asset.kind == "agent" else "SKILL.md")


def _split_frontmatter(text: str, source: Path) -> Tuple[Mapping[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.rstrip() + "\n"
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise ManifestError("asset_frontmatter_invalid: missing closing delimiter: {}".format(source))
    try:
        metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as exc:
        raise ManifestError("asset_frontmatter_invalid: {}: {}".format(source, exc)) from exc
    if not isinstance(metadata, dict):
        raise ManifestError("asset_frontmatter_invalid: frontmatter must be an object: {}".format(source))
    body = "\n".join(lines[end + 1 :]).lstrip("\n").rstrip() + "\n"
    return metadata, body


def _provenance(manifest: Manifest, contract: TargetContract, asset: Asset, source: Path) -> Mapping[str, Any]:
    return {
        "adk": {
            "asset_kind": asset.kind,
            "manifest_version": manifest.version,
            "source": source.relative_to(manifest.root).as_posix(),
            "target": contract.name,
        }
    }


def _render_main(manifest: Manifest, contract: TargetContract, asset: Asset) -> RenderedFile:
    if asset.kind not in contract.supported_asset_kinds:
        raise TargetUsageError(
            "unsupported_asset_kind: target={} kind={} asset={}".format(
                contract.name, asset.kind, asset.name
            )
        )
    source = _content_path(asset)
    if source.is_symlink() or not source.is_file():
        raise ManifestError("asset_content_invalid: missing regular content file: {}".format(source))
    source_metadata, body = _split_frontmatter(source.read_text(encoding="utf-8"), source)
    source_name = source_metadata.get("name")
    if source_name is not None and source_name != asset.name:
        raise ManifestError(
            "asset_frontmatter_invalid: name mismatch {} != {}".format(source_name, asset.name)
        )
    record = manifest.asset_record(asset)
    description = source_metadata.get("description") or record.get("description")
    if not isinstance(description, str) or not description.strip():
        raise ManifestError(
            "asset_frontmatter_invalid: description missing for {} {}".format(asset.kind, asset.name)
        )

    kind_contract = contract.data["frontmatter"][asset.kind]
    required = [str(item) for item in kind_contract["required"]]
    metadata: Dict[str, Any] = {}
    if asset.kind == "skill" or "name" in required:
        metadata["name"] = asset.name
    metadata["description"] = description.strip()
    for key in kind_contract["preserve"]:
        value = source_metadata.get(key)
        if isinstance(value, str) and value.strip():
            metadata[str(key)] = value.strip()
    metadata.update(dict(kind_contract["static"]))
    if asset.kind == "skill":
        invocation_mode = manifest.skill_invocation_mode(asset)
        invocation_contract = contract.data["skill_invocation"]
        supported_modes = tuple(str(item) for item in invocation_contract["supported_modes"])
        if invocation_mode not in supported_modes:
            raise TargetUsageError(
                "unsupported_skill_invocation_mode: target={} skill={} mode={}".format(
                    contract.name, asset.name, invocation_mode
                )
            )
        if invocation_mode == "explicit-only":
            metadata.update(dict(invocation_contract["explicit_only_frontmatter"]))
    if asset.kind == "agent":
        permission_profile = record.get("permission_profile")
        if not isinstance(permission_profile, str) or not permission_profile:
            raise ManifestError(
                "agent_permission_profile_missing: agent={}".format(asset.name)
            )
        profiles = contract.data["permission_profiles"]
        native = profiles.get(permission_profile) if isinstance(profiles, dict) else None
        if not isinstance(native, dict):
            raise ManifestError(
                "agent_permission_profile_unsupported: target={} agent={} profile={}".format(
                    contract.name, asset.name, permission_profile
                )
            )
        metadata.update(native)
    metadata["metadata"] = _provenance(manifest, contract, asset, source)
    missing = [key for key in required if key not in metadata or metadata[key] in (None, "")]
    if missing:
        raise ManifestError(
            "target_frontmatter_invalid: target={} asset={} missing={}".format(
                contract.name, asset.name, ",".join(missing)
            )
        )
    rendered_frontmatter = yaml.safe_dump(
        metadata,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()
    content = ("---\n{}\n---\n\n{}".format(rendered_frontmatter, body)).encode("utf-8")
    return RenderedFile(
        kind=asset.kind,
        name=asset.name,
        source=source.relative_to(manifest.root).as_posix(),
        destination=contract.layout(asset.kind, asset.name),
        content=content,
        mode=0o644,
    )


def _render_support_files(
    manifest: Manifest, contract: TargetContract, asset: Asset
) -> List[RenderedFile]:
    if asset.kind != "skill":
        return []
    main_destination = Path(contract.layout(asset.kind, asset.name))
    skill_root = main_destination.parent
    rendered: List[RenderedFile] = []
    for directory_name in contract.data["support_directories"]:
        source_root = asset.path / str(directory_name)
        if not source_root.exists():
            continue
        if source_root.is_symlink() or not source_root.is_dir():
            raise ManifestError("asset_support_invalid: expected regular directory: {}".format(source_root))
        for source in sorted(source_root.rglob("*")):
            if source.is_symlink():
                raise ManifestError("asset_support_invalid: symlink forbidden: {}".format(source))
            if not source.is_file():
                continue
            ensure_within(source, asset.path, "asset support file")
            relative = source.relative_to(asset.path)
            destination = (skill_root / relative).as_posix()
            mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
            rendered.append(
                RenderedFile(
                    kind=asset.kind,
                    name=asset.name,
                    source=source.relative_to(manifest.root).as_posix(),
                    destination=destination,
                    content=source.read_bytes(),
                    mode=mode,
                )
            )
    return rendered


def render_asset(manifest: Manifest, contract: TargetContract, asset: Asset) -> Tuple[RenderedFile, ...]:
    files = [_render_main(manifest, contract, asset)]
    files.extend(_render_support_files(manifest, contract, asset))
    return tuple(files)


def render_selection(
    manifest: Manifest,
    target: str,
    profiles: Sequence[str],
    optional_skills: Sequence[str] = (),
    asset_kind: Optional[str] = None,
) -> RenderedBundle:
    if asset_kind is not None and asset_kind not in ASSET_KINDS:
        raise TargetUsageError("unknown_asset_kind: {}".format(asset_kind))
    contract = load_target_contract(manifest, target)
    resolution = manifest.resolve_profiles(profiles, optional_skills)
    assets = tuple(list(resolution.agents) + list(resolution.skills))
    if asset_kind is not None:
        assets = tuple(item for item in assets if item.kind == asset_kind)
    unsupported = sorted({item.kind for item in assets if item.kind not in contract.supported_asset_kinds})
    if unsupported:
        raise TargetUsageError(
            "unsupported_asset_kind: target={} kind={}; use --asset-kind {}".format(
                target,
                ",".join(unsupported),
                contract.supported_asset_kinds[0] if len(contract.supported_asset_kinds) == 1 else "<supported-kind>",
            )
        )
    if not assets:
        raise TargetUsageError(
            "empty_asset_selection: target={} asset_kind={}".format(target, asset_kind or "all")
        )
    files: List[RenderedFile] = []
    destinations: Dict[str, RenderedFile] = {}
    for asset in assets:
        for rendered in render_asset(manifest, contract, asset):
            if rendered.destination in destinations:
                other = destinations[rendered.destination]
                raise ManifestError(
                    "target_destination_collision: {} from {}/{} and {}/{}".format(
                        rendered.destination, other.kind, other.name, rendered.kind, rendered.name
                    )
                )
            destinations[rendered.destination] = rendered
            files.append(rendered)
    return RenderedBundle(
        target=target,
        contract=contract,
        resolution=resolution,
        optional_skills=tuple(optional_skills),
        asset_kind=asset_kind,
        assets=assets,
        files=tuple(files),
    )


def check_target(manifest: Manifest, target: str) -> Dict[str, Any]:
    contract = load_target_contract(manifest, target)
    assets: List[Asset] = []
    for kind in contract.supported_asset_kinds:
        assets.extend(manifest.all_assets(kind))
    destinations: Dict[str, str] = {}
    file_count = 0
    for asset in assets:
        for rendered in render_asset(manifest, contract, asset):
            if rendered.destination in destinations:
                raise ManifestError(
                    "target_destination_collision: {} from {} and {}".format(
                        rendered.destination, destinations[rendered.destination], asset.name
                    )
                )
            destinations[rendered.destination] = asset.name
            file_count += 1
    return {
        "status": "pass",
        "target": target,
        "contract_schema": CONTRACT_SCHEMA,
        "contract_status": contract.status,
        "contract_sha256": contract.digest,
        "source": contract.data["source"],
        "supported_asset_kinds": list(contract.supported_asset_kinds),
        "adapter": contract.adapter,
        "checked_assets": len(assets),
        "checked_files": file_count,
    }


def check_targets(manifest: Manifest, target: Optional[str] = None) -> Dict[str, Any]:
    names = [target] if target else sorted(manifest.direct_targets())
    results = {name: check_target(manifest, name) for name in names}
    return {"schema": CHECK_SCHEMA, "status": "pass", "level": "static", "targets": results}


def _write_bundle(root: Path, bundle: RenderedBundle) -> None:
    for rendered in bundle.files:
        destination = ensure_within(root / rendered.destination, root, "smoke destination")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rendered.content)
        destination.chmod(rendered.mode)


def run_target_smoke(
    manifest: Manifest,
    target: str,
    stage: str,
    runtime_command: Sequence[str],
    profile: Optional[str] = None,
    asset_kind: Optional[str] = None,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    if timeout_seconds < 1 or timeout_seconds > 600:
        raise TargetUsageError("invalid_timeout_seconds: expected 1..600")
    static = check_target(manifest, target)
    contract = load_target_contract(manifest, target)
    if stage not in contract.smoke_stages:
        raise TargetUsageError(
            "unsupported_smoke_stage: target={} stage={}".format(target, stage)
        )
    if not runtime_command:
        return {
            "schema": SMOKE_SCHEMA,
            "status": "not-run",
            "certification": "not-certified",
            "target": target,
            "stage": stage,
            "static_check": static,
            "reason": "runtime_command_required",
        }
    selected_kind = asset_kind
    if selected_kind is None and len(contract.supported_asset_kinds) == 1:
        selected_kind = contract.supported_asset_kinds[0]
    bundle = render_selection(
        manifest,
        target,
        [profile or manifest.default_profile],
        asset_kind=selected_kind,
    )
    with tempfile.TemporaryDirectory(prefix="adk-target-smoke-") as temp:
        target_root = Path(temp) / target
        _write_bundle(target_root, bundle)
        environment = os.environ.copy()
        environment.update(
            {
                "ADK_TARGET": target,
                "ADK_TARGET_ROOT": str(target_root),
                "ADK_TARGET_SMOKE_STAGE": stage,
            }
        )
        command_digest = sha256_bytes(canonical_json_bytes([str(item) for item in runtime_command]))
        started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(runtime_command),
                cwd=str(manifest.root),
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return {
                "schema": SMOKE_SCHEMA,
                "status": "fail",
                "certification": "caller-supplied-smoke",
                "target": target,
                "stage": stage,
                "error_code": "runtime_timeout",
                "timeout_seconds": timeout_seconds,
                "started_at": started_at,
                "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
                "runtime_command_sha256": command_digest,
                "static_check": static,
            }
    return {
        "schema": SMOKE_SCHEMA,
        "status": "pass" if completed.returncode == 0 else "fail",
        "certification": "caller-supplied-smoke",
        "target": target,
        "stage": stage,
        "started_at": started_at,
        "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
        "runtime_command_sha256": command_digest,
        "runtime_exit_code": completed.returncode,
        "stdout_bytes": len(completed.stdout),
        "stdout_sha256": sha256_bytes(completed.stdout),
        "stderr_bytes": len(completed.stderr),
        "stderr_sha256": sha256_bytes(completed.stderr),
        "static_check": static,
    }
