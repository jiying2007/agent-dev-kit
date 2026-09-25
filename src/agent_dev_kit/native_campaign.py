"""Native target campaign planning, bounded execution, and receipt finalization.

This module never promotes an active target contract or writes trust registry
entries. It prepares a future runtime contract digest, executes privacy-safe
discovery/load/trigger commands, and emits a typed receipt only when every stage
passes. Signature/provenance registration remains a separate owner-reviewed step.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
import platform
import shutil
import signal
import stat
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within, sha256_bytes
from .target_contracts import (
    _authority_digest,
    _native_contract_digest,
    _schema_failures,
    load_target_contract,
)
from .targets import _write_bundle, render_selection

PLAN_SCHEMA = "adk-native-target-campaign-plan/v1"
EVIDENCE_SCHEMA = "adk-native-target-campaign-evidence/v1"
FINALIZE_SCHEMA = "adk-native-target-campaign-finalize/v1"
STAGES = ("discovery", "load", "trigger")
BACKENDS = ("external-signature-verifier", "ci-provenance-verifier")
AUTH_MODES = ("none", "home")
MAX_JSON_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_VERSION_OUTPUT_BYTES = 64 * 1024


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
    if not path.is_file() or path.is_symlink():
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
    if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool) or not 1 <= timeout_seconds <= 600:
        raise ManifestError("native_campaign_timeout_invalid")
    receipt_path = _safe_relative_path(receipt_path, "receipt_path")
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
    commands_value = _validate_commands(dict(commands))
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


async def _drain(stream: asyncio.StreamReader, process: asyncio.subprocess.Process, limit: int) -> tuple[int, str, bytes]:
    digest = hashlib.sha256()
    total = 0
    captured = bytearray()
    while True:
        chunk = await stream.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            process.kill()
            raise ManifestError("native_campaign_output_budget_exceeded")
        digest.update(chunk)
        captured.extend(chunk)
    return total, digest.hexdigest(), bytes(captured)


async def _execute_async(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    output_limit: int,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(cwd),
        env=dict(env),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )
    assert process.stdout is not None and process.stderr is not None
    started = time.monotonic()
    try:
        stdout_task = asyncio.create_task(_drain(process.stdout, process, output_limit))
        stderr_task = asyncio.create_task(_drain(process.stderr, process, output_limit))
        await asyncio.wait_for(process.wait(), timeout=timeout_seconds)
        stdout = await stdout_task
        stderr = await stderr_task
    except (asyncio.TimeoutError, ManifestError):
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        elif process.returncode is None:
            process.kill()
        await process.wait()
        raise
    return {
        "exit_code": int(process.returncode or 0),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "stdout_bytes": stdout[0],
        "stdout_sha256": stdout[1],
        "stdout": stdout[2],
        "stderr_bytes": stderr[0],
        "stderr_sha256": stderr[1],
        "stderr": stderr[2],
    }


def _execute(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    output_limit: int,
) -> dict[str, Any]:
    return asyncio.run(
        _execute_async(
            command,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
            output_limit=output_limit,
        )
    )


def _base_environment(auth_mode: str) -> dict[str, str]:
    env = {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if auth_mode == "home":
        home = os.environ.get("HOME")
        if not home:
            raise ManifestError("native_campaign_home_auth_requires_HOME")
        env["HOME"] = home
        cache = os.environ.get("XDG_CACHE_HOME")
        if cache:
            env["XDG_CACHE_HOME"] = cache
    for key in ("SSL_CERT_FILE", "SSL_CERT_DIR"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    return env


def run_campaign(
    manifest: Manifest,
    plan: Mapping[str, Any],
    candidate_contract: Mapping[str, Any],
    commands: Mapping[str, Sequence[str]],
    runtime_binary: Path,
) -> dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA or plan.get("status") != "ready":
        raise ManifestError("native_campaign_plan_invalid")
    commands_value = _validate_commands(dict(commands))
    runtime_binary = _runtime_binary(str(runtime_binary))
    if runtime_binary.name != plan["runtime"]["binary"] or _sha256_file(runtime_binary) != plan["runtime"]["binary_sha256"]:
        raise ManifestError("native_campaign_runtime_identity_drift")
    version_command = commands_value["version"]
    version_executable = _runtime_binary(version_command[0])
    if version_executable != runtime_binary:
        raise ManifestError("native_campaign_version_command_must_use_runtime_binary")
    for name in ("version", *STAGES):
        digest = sha256_bytes(canonical_json_bytes(commands_value[name]))
        if digest != plan["command_sha256"][name]:
            raise ManifestError(f"native_campaign_command_drift: {name}")
    if sha256_bytes(canonical_json_bytes(candidate_contract)) != plan["candidate_contract_sha256"]:
        raise ManifestError("native_campaign_candidate_contract_drift")
    if _native_contract_digest(candidate_contract) != plan["candidate_contract_normalized_sha256"]:
        raise ManifestError("native_campaign_candidate_contract_normalized_drift")
    current = load_target_contract(manifest, str(plan["target"]))
    if current.digest != plan["source_contract_sha256"] or manifest.version != plan["source_version"]:
        raise ManifestError("native_campaign_source_drift")
    bundle_digest, bundle_files = _bundle_identity(manifest, str(plan["target"]), str(plan["profile"]))
    if bundle_digest != plan["bundle_sha256"] or bundle_files != plan["bundle_files"]:
        raise ManifestError("native_campaign_bundle_drift")

    base_env = _base_environment(str(plan["auth_mode"]))
    version_probe = _execute(
        version_command,
        cwd=manifest.root,
        env=base_env,
        timeout_seconds=min(int(plan["timeout_seconds"]), 30),
        output_limit=MAX_VERSION_OUTPUT_BYTES,
    )
    combined = version_probe["stdout"] + b"\n" + version_probe["stderr"]
    try:
        decoded = combined.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ManifestError("native_campaign_version_output_not_utf8") from exc
    if version_probe["exit_code"] != 0 or str(plan["runtime"]["version"]) not in decoded:
        return {
            "schema": EVIDENCE_SCHEMA,
            "status": "blocked",
            "reason": "runtime-version-probe-failed",
            "campaign_id": plan["campaign_id"],
            "target": plan["target"],
            "profile": plan["profile"],
            "runtime": dict(plan["runtime"]),
            "bundle_sha256": plan["bundle_sha256"],
            "candidate_contract_normalized_sha256": plan["candidate_contract_normalized_sha256"],
            "version_probe": {
                key: value for key, value in version_probe.items() if key not in ("stdout", "stderr")
            },
            "stages": [],
            "privacy": dict(plan["privacy"]),
            "lifecycle_authority": "none-campaign-only",
            "release_authorized": False,
        }

    bundle = render_selection(
        manifest,
        str(plan["target"]),
        [str(plan["profile"])],
        asset_kind="skill",
    )
    stage_records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="adk-native-campaign-") as temporary:
        target_root = Path(temporary) / str(plan["target"])
        _write_bundle(target_root, bundle)
        environment_descriptor = {
            "auth_mode": plan["auth_mode"],
            "environment_keys": sorted(base_env),
            "target": plan["target"],
            "profile": plan["profile"],
            "asset_kind": "skill",
        }
        environment_digest = sha256_bytes(canonical_json_bytes(environment_descriptor))
        cwd_digest = sha256_bytes(str(target_root.resolve()).encode("utf-8"))
        previous_failed = False
        for stage in STAGES:
            if previous_failed:
                stage_records.append(
                    {
                        "stage": stage,
                        "status": "blocked",
                        "reason": "previous-stage-failed",
                        "command_sha256": plan["command_sha256"][stage],
                    }
                )
                continue
            env = dict(base_env)
            env.update(
                {
                    "ADK_TARGET": str(plan["target"]),
                    "ADK_TARGET_ROOT": str(target_root),
                    "ADK_TARGET_SMOKE_STAGE": stage,
                }
            )
            started_at = _utc_now()
            try:
                result = _execute(
                    commands_value[stage],
                    cwd=target_root,
                    env=env,
                    timeout_seconds=int(plan["timeout_seconds"]),
                    output_limit=MAX_OUTPUT_BYTES,
                )
                completed_at = _utc_now()
                result_view = {key: value for key, value in result.items() if key not in ("stdout", "stderr")}
                result_digest = sha256_bytes(canonical_json_bytes(result_view))
                status = "pass" if result["exit_code"] == 0 else "fail"
                stage_records.append(
                    {
                        "stage": stage,
                        "status": status,
                        "command_sha256": plan["command_sha256"][stage],
                        "result_sha256": result_digest,
                        "exit_code": result["exit_code"],
                        "started_at": _timestamp(started_at),
                        "completed_at": _timestamp(completed_at),
                        "duration_ms": result["duration_ms"],
                        "stdout_bytes": result["stdout_bytes"],
                        "stdout_sha256": result["stdout_sha256"],
                        "stderr_bytes": result["stderr_bytes"],
                        "stderr_sha256": result["stderr_sha256"],
                        "environment": {
                            "platform": platform.system().lower() or "unknown",
                            "architecture": platform.machine().lower() or "unknown",
                            "cwd_sha256": cwd_digest,
                            "environment_sha256": environment_digest,
                            "runtime_binary_sha256": plan["runtime"]["binary_sha256"],
                            "bundle_sha256": plan["bundle_sha256"],
                        },
                        "privacy": {
                            "raw_content_stored": False,
                            "secrets_stored": False,
                            "sanitized": True,
                        },
                    }
                )
                previous_failed = status != "pass"
            except (ManifestError, asyncio.TimeoutError) as exc:
                completed_at = _utc_now()
                stage_records.append(
                    {
                        "stage": stage,
                        "status": "fail",
                        "reason": str(exc),
                        "command_sha256": plan["command_sha256"][stage],
                        "started_at": _timestamp(started_at),
                        "completed_at": _timestamp(completed_at),
                    }
                )
                previous_failed = True

    complete = all(item.get("status") == "pass" for item in stage_records)
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "status": "complete" if complete else "failed",
        "campaign_id": plan["campaign_id"],
        "target": plan["target"],
        "profile": plan["profile"],
        "runtime": dict(plan["runtime"]),
        "bundle_sha256": plan["bundle_sha256"],
        "candidate_contract_normalized_sha256": plan["candidate_contract_normalized_sha256"],
        "version_probe": {
            key: value for key, value in version_probe.items() if key not in ("stdout", "stderr")
        },
        "stages": stage_records,
        "privacy": dict(plan["privacy"]),
        "completed_at": _timestamp(_utc_now()),
        "lifecycle_authority": "none-campaign-only",
        "release_authorized": False,
    }
    return evidence


def finalize_campaign(
    manifest: Manifest,
    plan: Mapping[str, Any],
    candidate_contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
    receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if plan.get("schema") != PLAN_SCHEMA or evidence.get("schema") != EVIDENCE_SCHEMA:
        raise ManifestError("native_campaign_finalize_input_schema_invalid")
    if evidence.get("status") != "complete":
        raise ManifestError("native_campaign_finalize_requires_complete_campaign")
    if evidence.get("campaign_id") != plan.get("campaign_id"):
        raise ManifestError("native_campaign_finalize_campaign_mismatch")
    if sha256_bytes(canonical_json_bytes(candidate_contract)) != plan["candidate_contract_sha256"]:
        raise ManifestError("native_campaign_finalize_candidate_drift")
    contract_digest = _native_contract_digest(candidate_contract)
    if contract_digest != plan["candidate_contract_normalized_sha256"]:
        raise ManifestError("native_campaign_finalize_contract_digest_mismatch")
    receipt_relative = receipt_path.resolve().relative_to(manifest.root.resolve()).as_posix()
    if receipt_relative != plan["receipt_path"]:
        raise ManifestError("native_campaign_finalize_receipt_path_mismatch")

    stages = evidence.get("stages")
    if not isinstance(stages, list) or [item.get("stage") for item in stages] != list(STAGES):
        raise ManifestError("native_campaign_finalize_stage_set_invalid")
    receipt_stages = []
    for item in stages:
        if item.get("status") != "pass" or item.get("exit_code") != 0:
            raise ManifestError("native_campaign_finalize_stage_not_passed")
        authority = {
            "execution_authority": plan["authority"]["execution_authority"],
            "authority_id": plan["authority"]["authority_id"],
            "scope": item["stage"],
        }
        authority["attestation_sha256"] = _authority_digest(authority)
        environment = dict(item["environment"])
        environment["contract_sha256"] = contract_digest
        receipt_stages.append(
            {
                "stage": item["stage"],
                "command_sha256": item["command_sha256"],
                "result_sha256": item["result_sha256"],
                "exit_code": 0,
                "started_at": item["started_at"],
                "completed_at": item["completed_at"],
                "duration_ms": item["duration_ms"],
                "environment": environment,
                "privacy": dict(item["privacy"]),
                "authority": authority,
            }
        )
    verified_at = max(item["completed_at"] for item in receipt_stages)
    body = {
        "schema": "adk-native-target-conformance-receipt/v1",
        "target": plan["target"],
        "runtime": dict(plan["runtime"]),
        "bundle_sha256": plan["bundle_sha256"],
        "contract_sha256": contract_digest,
        "verified_at": verified_at,
        "stages": receipt_stages,
    }
    receipt = dict(body)
    receipt["receipt_id"] = "native-{}-{}".format(
        plan["target"], sha256_bytes(canonical_json_bytes(body))[:20]
    )
    receipt_schema = manifest.root / "schemas" / "native-target-conformance-receipt-v1.schema.json"
    _validate_schema(receipt, receipt_schema, "native target conformance receipt")

    final_contract = copy.deepcopy(candidate_contract)
    conformance = final_contract["adapter"]["conformance"]
    receipt_payload = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    receipt_sha = hashlib.sha256(receipt_payload).hexdigest()
    conformance["last_verified_at"] = receipt["verified_at"]
    conformance["evidence"] = [
        {
            "receipt_schema": receipt["schema"],
            "path": receipt_relative,
            "sha256": receipt_sha,
            "target": plan["target"],
            "runtime_version": plan["runtime"]["version"],
            "bundle_sha256": plan["bundle_sha256"],
            "contract_sha256": contract_digest,
            "layer": "runtime",
        }
    ]
    target_schema = manifest.root / "manifests" / "target-contract.schema.json"
    _validate_schema(final_contract, target_schema, "final target contract")
    result = {
        "schema": FINALIZE_SCHEMA,
        "status": "ready-for-signature-and-registry",
        "campaign_id": plan["campaign_id"],
        "target": plan["target"],
        "receipt_id": receipt["receipt_id"],
        "receipt_path": receipt_relative,
        "receipt_sha256": receipt_sha,
        "contract_sha256": contract_digest,
        "bundle_sha256": plan["bundle_sha256"],
        "next_required_evidence": [
            "sigstore-or-reviewed-external-signature-bundle",
            "managed-trust-registry-receipt-binding",
            "production-loader-verification",
            "owner-reviewed-target-contract-promotion",
        ],
        "lifecycle_authority": "none-candidate-only",
        "release_authorized": False,
    }
    return result, receipt, final_contract


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare, run and finalize native target campaigns")
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="action", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--target", required=True)
    prepare.add_argument("--profile", default="core")
    prepare.add_argument("--runtime-binary", required=True)
    prepare.add_argument("--runtime-version", required=True)
    prepare.add_argument("--authority-id", required=True)
    prepare.add_argument("--execution-authority", choices=("human-approved", "ci-approved"), required=True)
    prepare.add_argument("--verification-backend", choices=BACKENDS, required=True)
    prepare.add_argument("--auth-mode", choices=AUTH_MODES, default="none")
    prepare.add_argument("--timeout-seconds", type=int, default=120)
    prepare.add_argument("--commands-json", required=True)
    prepare.add_argument("--receipt-path", required=True)
    prepare.add_argument("--plan-out", required=True)
    prepare.add_argument("--candidate-contract-out", required=True)
    prepare.add_argument("--summary-json", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--plan", required=True)
    run.add_argument("--candidate-contract", required=True)
    run.add_argument("--commands-json", required=True)
    run.add_argument("--runtime-binary", required=True)
    run.add_argument("--evidence-out", required=True)
    run.add_argument("--summary-json", action="store_true")

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--plan", required=True)
    finalize.add_argument("--candidate-contract", required=True)
    finalize.add_argument("--evidence", required=True)
    finalize.add_argument("--receipt-out", required=True)
    finalize.add_argument("--final-contract-out", required=True)
    finalize.add_argument("--summary-json", action="store_true")

    args = parser.parse_args(list(argv) if argv is not None else None)
    manifest = Manifest.load(Path(args.root).resolve())
    try:
        if args.action == "prepare":
            commands = _validate_commands(_load_json(Path(args.commands_json), "native campaign commands"))
            plan, candidate = prepare_campaign(
                manifest,
                target=args.target,
                profile=args.profile,
                runtime_binary=Path(args.runtime_binary),
                runtime_version=args.runtime_version,
                authority_id=args.authority_id,
                execution_authority=args.execution_authority,
                backend=args.verification_backend,
                auth_mode=args.auth_mode,
                timeout_seconds=args.timeout_seconds,
                commands=commands,
                receipt_path=args.receipt_path,
            )
            _validate_schema(
                plan,
                manifest.root / "schemas" / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            _write_json(Path(args.plan_out), plan)
            _write_json(Path(args.candidate_contract_out), candidate)
            result = {
                "schema": PLAN_SCHEMA,
                "status": "ready",
                "campaign_id": plan["campaign_id"],
                "plan": str(Path(args.plan_out).resolve()),
                "candidate_contract": str(Path(args.candidate_contract_out).resolve()),
                "candidate_contract_normalized_sha256": plan["candidate_contract_normalized_sha256"],
                "release_authorized": False,
            }
        elif args.action == "run":
            plan = _load_json(Path(args.plan), "native campaign plan")
            candidate = _load_json(Path(args.candidate_contract), "native candidate contract")
            commands = _validate_commands(_load_json(Path(args.commands_json), "native campaign commands"))
            if not isinstance(plan, dict) or not isinstance(candidate, dict):
                raise ManifestError("native_campaign_run_inputs_must_be_objects")
            _validate_schema(
                plan,
                manifest.root / "schemas" / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            evidence = run_campaign(
                manifest, plan, candidate, commands, Path(args.runtime_binary)
            )
            _validate_schema(
                evidence,
                manifest.root / "schemas" / "native-target-campaign-evidence-v1.schema.json",
                "native campaign evidence",
            )
            _write_json(Path(args.evidence_out), evidence)
            result = evidence
        else:
            plan = _load_json(Path(args.plan), "native campaign plan")
            candidate = _load_json(Path(args.candidate_contract), "native candidate contract")
            evidence = _load_json(Path(args.evidence), "native campaign evidence")
            if not all(isinstance(value, dict) for value in (plan, candidate, evidence)):
                raise ManifestError("native_campaign_finalize_inputs_must_be_objects")
            _validate_schema(
                plan,
                manifest.root / "schemas" / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            _validate_schema(
                evidence,
                manifest.root / "schemas" / "native-target-campaign-evidence-v1.schema.json",
                "native campaign evidence",
            )
            receipt_path = Path(args.receipt_out)
            active_contract = manifest.root / "manifests" / "target-contracts" / f"{plan['target']}.json"
            if Path(args.final_contract_out).resolve() == active_contract.resolve():
                raise ManifestError("native_campaign_finalize_must_not_overwrite_active_contract")
            result, receipt, final_contract = finalize_campaign(
                manifest, plan, candidate, evidence, receipt_path
            )
            _write_json(receipt_path, receipt)
            _write_json(Path(args.final_contract_out), final_contract)
        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.action == "run" and result["status"] != "complete":
            return 2
        return 0
    except (ManifestError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema": "adk-native-target-campaign-error/v1",
            "status": "fail",
            "error": str(exc),
            "release_authorized": False,
        }
        if getattr(args, "summary_json", False):
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
