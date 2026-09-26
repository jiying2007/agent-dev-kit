"""Versioned direct-target contract loading and native conformance validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

from jsonschema import Draft202012Validator, FormatChecker

from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within, sha256_bytes
from .native_trust import build_managed_native_trust_verifier
from .privacy_ref import validate_no_secrets


CONTRACT_SCHEMA = "adk-target-contract/v2"
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
    assertion_digests = [item.get("assertion_sha256") for item in stages]
    assertion_result_digests = [item.get("assertion_result_sha256") for item in stages]
    if any(item.get("semantic_assertion_status") != "pass" for item in stages):
        raise ManifestError(
            "target_contract_invalid: native stages require passed semantic assertions"
        )
    if (
        len(set(command_digests)) != len(stages)
        or len(set(result_digests)) != len(stages)
        or len(set(assertion_digests)) != len(stages)
        or len(set(assertion_result_digests)) != len(stages)
    ):
        raise ManifestError(
            "target_contract_invalid: native stages require independent command, assertion and result evidence"
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
        manifest.root / "schemas" / "native-target-conformance-receipt-v2.schema.json",
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
        raise ManifestError(
            "target_contract_invalid: target source dates are invalid for {}".format(target)
        ) from exc
    if retrieved_at > date.today() or expires_at <= retrieved_at:
        raise ManifestError(
            "target_contract_invalid: target source date order is invalid for {}".format(target)
        )
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
    conformance = adapter.get("conformance", {})
    trust_verifier = None
    if isinstance(conformance, dict) and conformance.get("level") == "runtime":
        trust_policy = adapter.get("conformance_trust_policy")
        if not isinstance(trust_policy, dict):
            raise ManifestError("target_contract_untrusted: native trust policy is missing")
        trust_verifier = build_managed_native_trust_verifier(manifest, target, trust_policy)
    _validate_native_conformance_evidence(manifest, target, adapter, data, trust_verifier)
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
