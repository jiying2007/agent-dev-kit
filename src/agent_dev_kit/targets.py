"""Direct-target rendering, static checks, and runtime smoke orchestration."""

from __future__ import annotations

import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from .model import (
    Asset,
    Manifest,
    ManifestError,
    ProfileResolution,
    canonical_json_bytes,
    ensure_within,
    sha256_bytes,
)
from .target_contracts import (
    CONTRACT_SCHEMA as CONTRACT_SCHEMA,
    TargetContract as TargetContract,
    TargetUsageError as TargetUsageError,
    _authority_digest as _authority_digest,
    _native_contract_digest as _native_contract_digest,
    _validate_native_conformance_evidence as _validate_native_conformance_evidence,
    load_target_contract as load_target_contract,
)


CHECK_SCHEMA = "adk-target-check/v1"
SMOKE_SCHEMA = "adk-target-smoke/v1"
ASSET_KINDS = ("agent", "skill")


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
