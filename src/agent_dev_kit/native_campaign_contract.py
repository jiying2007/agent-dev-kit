"""Contracts and deterministic planning for native target campaigns."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .target_contracts import _native_contract_digest, _schema_failures, load_target_contract
from .targets import render_selection

PLAN_SCHEMA = "adk-native-target-campaign-plan/v1"
EVIDENCE_SCHEMA = "adk-native-target-campaign-evidence/v1"
FINALIZE_SCHEMA = "adk-native-target-campaign-finalize/v1"
STAGES = ("discovery", "load", "trigger")
BACKENDS = ("external-signature-verifier", "ci-provenance-verifier")
AUTH_MODES = ("none", "home")
MAX_JSON_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_VERSION_OUTPUT_BYTES = 64 * 1024



TARGET_LAYOUT_SCHEMA = "adk-native-campaign-target-layouts/v1"
MAX_LAYOUT_MANIFEST_BYTES = 256 * 1024


def load_native_campaign_target_layouts(manifest: Manifest) -> Mapping[str, Mapping[str, Any]]:
    path = manifest.root / "manifests" / "native_campaign_target_layouts.json"
    if path.is_symlink() or not path.is_file():
        raise ManifestError("native_campaign_target_layouts_missing_or_unsafe")
    if path.stat().st_size > MAX_LAYOUT_MANIFEST_BYTES:
        raise ManifestError("native_campaign_target_layouts_exceeds_byte_budget")
    value = _load_json(path, "native campaign target layouts")
    if not isinstance(value, dict) or set(value) != {
        "schema", "status", "reviewed_at", "expires_at", "targets"
    }:
        raise ManifestError("native_campaign_target_layouts_invalid_top_level")
    if value.get("schema") != TARGET_LAYOUT_SCHEMA or value.get("status") != "reviewed":
        raise ManifestError("native_campaign_target_layouts_invalid_schema_or_status")
    try:
        reviewed_at = datetime.fromisoformat(str(value["reviewed_at"]) + "T00:00:00+00:00")
        expires_at = datetime.fromisoformat(str(value["expires_at"]) + "T00:00:00+00:00")
    except ValueError as exc:
        raise ManifestError("native_campaign_target_layouts_invalid_dates") from exc
    now = datetime.now(timezone.utc)
    if reviewed_at > now or expires_at <= reviewed_at or (expires_at - reviewed_at).days > 90:
        raise ManifestError("native_campaign_target_layouts_invalid_freshness")
    if expires_at.date() < now.date():
        raise ManifestError("native_campaign_target_layouts_stale")

    targets = value.get("targets")
    if not isinstance(targets, dict) or set(targets) != set(manifest.direct_targets()):
        raise ManifestError("native_campaign_target_layouts_must_cover_direct_targets")
    normalized: dict[str, Mapping[str, Any]] = {}
    for target, record in sorted(targets.items()):
        if not isinstance(record, dict) or set(record) != {
            "project_config_dir", "discovery_scope", "documentation"
        }:
            raise ManifestError(f"native_campaign_target_layout_invalid: {target}")
        config_dir = record.get("project_config_dir")
        if (
            not isinstance(config_dir, str)
            or not config_dir.startswith(".")
            or "/" in config_dir
            or "\\" in config_dir
            or config_dir in (".", "..")
            or any(ch in config_dir for ch in ("\x00", "\n", "\r"))
        ):
            raise ManifestError(f"native_campaign_project_config_dir_invalid: {target}")
        if record.get("discovery_scope") != "project":
            raise ManifestError(f"native_campaign_discovery_scope_invalid: {target}")
        docs = record.get("documentation")
        if (
            not isinstance(docs, list)
            or not docs
            or len(set(docs)) != len(docs)
            or not all(isinstance(url, str) and url.startswith("https://") for url in docs)
        ):
            raise ManifestError(f"native_campaign_documentation_invalid: {target}")
        normalized[str(target)] = {
            "project_config_dir": config_dir,
            "discovery_scope": "project",
            "documentation": list(docs),
        }
    return normalized


def native_campaign_target_layout(manifest: Manifest, target: str) -> Mapping[str, Any]:
    layouts = load_native_campaign_target_layouts(manifest)
    try:
        return layouts[target]
    except KeyError as exc:
        raise ManifestError(f"native_campaign_target_layout_missing: {target}") from exc

def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path, label: str) -> Any:
    if path.is_symlink() or not path.is_file():
        raise ManifestError(f"{label} is missing or unsafe: {path}")
    if path.stat().st_size > MAX_JSON_BYTES:
        raise ManifestError(f"{label} exceeds byte budget")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"{label} is invalid JSON") from exc


def _write_json(path: Path, value: Any) -> None:
    path = path.resolve()
    if path.exists() and path.is_symlink():
        raise ManifestError(f"output path must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if len(payload.encode("utf-8")) > MAX_JSON_BYTES:
        raise ManifestError("output exceeds byte budget")
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except OSError:
            pass


def _validate_schema(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _load_json(schema_path, label + " schema")
    if not isinstance(schema, dict):
        raise ManifestError(f"{label} schema must be an object")
    failures = _schema_failures(value, schema)
    if failures:
        raise ManifestError(f"{label} schema failure: {'; '.join(failures)}")


def _safe_relative_path(value: str, label: str) -> str:
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or "\x00" in value
        or "\n" in value
        or "\r" in value
    ):
        raise ManifestError(f"{label} must be a safe relative path")
    return path.as_posix()


def _runtime_binary(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        located = shutil.which(path_value)
        if located is None:
            raise ManifestError("native_campaign_runtime_binary_not_found")
        path = Path(located)
    path = path.resolve()
    if not path.is_file():
        raise ManifestError("native_campaign_runtime_binary_not_regular")
    if not os.access(path, os.X_OK):
        raise ManifestError("native_campaign_runtime_binary_not_executable")
    return path


def _validate_commands(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict) or set(value) != {"version", *STAGES}:
        raise ManifestError("native_campaign_commands_require_version_discovery_load_trigger")
    result: dict[str, list[str]] = {}
    for name in ("version", *STAGES):
        command = value[name]
        if (
            not isinstance(command, list)
            or not command
            or len(command) > 64
            or not all(isinstance(item, str) and item and len(item) <= 4096 for item in command)
        ):
            raise ManifestError(f"native_campaign_command_invalid: {name}")
        if any(any(ch in item for ch in ("\x00", "\n", "\r")) for item in command):
            raise ManifestError(f"native_campaign_command_control_character: {name}")
        if not Path(command[0]).is_absolute():
            raise ManifestError(f"native_campaign_command_requires_absolute_runtime: {name}")
        result[name] = list(command)
    stage_digests = {
        sha256_bytes(canonical_json_bytes(result[name]))
        for name in STAGES
    }
    if len(stage_digests) != len(STAGES):
        raise ManifestError("native_campaign_stage_commands_must_be_independent")
    return result


def _bundle_identity(manifest: Manifest, target: str, profile: str) -> tuple[str, int]:
    bundle = render_selection(manifest, target, [profile], asset_kind="skill")
    records = [
        {
            "kind": item.kind,
            "name": item.name,
            "destination": item.destination,
            "sha256": item.sha256,
            "mode": item.mode,
        }
        for item in sorted(bundle.files, key=lambda candidate: candidate.destination)
    ]
    return sha256_bytes(canonical_json_bytes(records)), len(records)


def _candidate_contract(
    manifest: Manifest,
    target: str,
    runtime_binary_name: str,
    runtime_binary_sha256: str,
    runtime_version: str,
    authority_id: str,
    backend: str,
    bundle_sha256: str,
    receipt_path: str,
) -> tuple[dict[str, Any], str]:
    contract = copy.deepcopy(load_target_contract(manifest, target).data)
    for capability in ("discovery", "load", "trigger"):
        contract["adapter"]["capabilities"][capability] = "native-verified"
    contract["adapter"]["conformance"] = {
        "level": "runtime",
        "certification": "conformance-certified",
        "native_runtime_smoke": "pass",
        "runtime_binary": runtime_binary_name,
        "runtime_binary_sha256": runtime_binary_sha256,
        "runtime_version": runtime_version,
        "runtime_version_pin": runtime_version,
        "last_verified_at": "1970-01-01T00:00:00Z",
        "evidence": [
            {
                "receipt_schema": "adk-native-target-conformance-receipt/v1",
                "path": receipt_path,
                "sha256": "0" * 64,
                "target": target,
                "runtime_version": runtime_version,
                "bundle_sha256": bundle_sha256,
                "contract_sha256": "0" * 64,
                "layer": "runtime",
            }
        ],
    }
    contract["adapter"]["conformance_trust_policy"] = {
        "enabled": True,
        "trusted_authorities": [authority_id],
        "verification_backend": backend,
    }
    digest = _native_contract_digest(contract)
    contract["adapter"]["conformance"]["evidence"][0]["contract_sha256"] = digest
    return contract, digest


def prepare_campaign(
    manifest: Manifest,
    *,
    target: str,
    profile: str,
    runtime_binary: Path,
    runtime_version: str,
    authority_id: str,
    execution_authority: str,
    backend: str,
    auth_mode: str,
    timeout_seconds: int,
    commands: Mapping[str, Sequence[str]],
    receipt_path: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not runtime_version or len(runtime_version) > 128:
        raise ManifestError("native_campaign_runtime_version_invalid")
    if not authority_id or len(authority_id) > 128:
        raise ManifestError("native_campaign_authority_id_invalid")
    if execution_authority not in ("human-approved", "ci-approved"):
        raise ManifestError("native_campaign_execution_authority_invalid")
    if backend not in BACKENDS:
        raise ManifestError("native_campaign_backend_invalid")
    if auth_mode not in AUTH_MODES:
        raise ManifestError("native_campaign_auth_mode_invalid")
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or not 1 <= timeout_seconds <= 600
    ):
        raise ManifestError("native_campaign_timeout_invalid")
    receipt_path = _safe_relative_path(receipt_path, "receipt_path")
    if not receipt_path.startswith("reports/runtime/"):
        raise ManifestError("native_campaign_receipt_path_must_be_under_reports_runtime")
    runtime_binary = _runtime_binary(str(runtime_binary))
    runtime_name = runtime_binary.name
    if not runtime_name or len(runtime_name) > 128:
        raise ManifestError("native_campaign_runtime_binary_name_invalid")
    runtime_digest = _sha256_file(runtime_binary)
    static_contract = load_target_contract(manifest, target)
    bundle_digest, bundle_files = _bundle_identity(manifest, target, profile)
    candidate, normalized_digest = _candidate_contract(
        manifest,
        target,
        runtime_name,
        runtime_digest,
        runtime_version,
        authority_id,
        backend,
        bundle_digest,
        receipt_path,
    )
    _validate_schema(
        candidate,
        manifest.root / "manifests" / "target-contract.schema.json",
        "native candidate target contract",
    )
    commands_value = _validate_commands(dict(commands))
    for command_name in ("version", *STAGES):
        if _runtime_binary(commands_value[command_name][0]) != runtime_binary:
            raise ManifestError(
                f"native_campaign_command_must_use_runtime_binary: {command_name}"
            )
    command_digests = {
        name: sha256_bytes(canonical_json_bytes(commands_value[name]))
        for name in ("version", *STAGES)
    }
    plan_body = {
        "schema": PLAN_SCHEMA,
        "status": "ready",
        "target": target,
        "profile": profile,
        "asset_kind": "skill",
        "source_version": manifest.version,
        "source_contract_sha256": static_contract.digest,
        "candidate_contract_sha256": sha256_bytes(canonical_json_bytes(candidate)),
        "candidate_contract_normalized_sha256": normalized_digest,
        "bundle_sha256": bundle_digest,
        "bundle_files": bundle_files,
        "runtime": {
            "binary": runtime_name,
            "binary_sha256": runtime_digest,
            "version": runtime_version,
            "version_pin": runtime_version,
        },
        "authority": {
            "execution_authority": execution_authority,
            "authority_id": authority_id,
            "verification_backend": backend,
        },
        "auth_mode": auth_mode,
        "timeout_seconds": timeout_seconds,
        "receipt_path": receipt_path,
        "command_sha256": command_digests,
        "privacy": {
            "raw_command_stored": False,
            "raw_output_stored": False,
            "credentials_stored": False,
        },
        "lifecycle_authority": "none-campaign-only",
        "release_authorized": False,
    }
    plan = dict(plan_body)
    plan["campaign_id"] = "native-" + sha256_bytes(canonical_json_bytes(plan_body))[:24]
    return plan, candidate
