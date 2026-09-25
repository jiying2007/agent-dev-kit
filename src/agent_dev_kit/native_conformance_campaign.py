"""Generate untrusted native target conformance candidate receipts.

The campaign executes caller-approved stage commands against an isolated ADK
export and emits a strict receipt candidate. It deliberately does not verify
external authority/provenance and therefore never certifies a target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import signal
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within, sha256_bytes
from .target_contracts import _authority_digest, _native_contract_digest, load_target_contract
from .targets import render_selection

SCHEMA = "adk-native-target-campaign-result/v1"
COMMAND_SCHEMA = "adk-native-target-campaign-commands/v1"
STAGES = ("discovery", "load", "trigger")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_commands(path: Path) -> dict[str, dict[str, tuple[str, ...]]]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 128 * 1024:
        raise ManifestError("native_campaign_commands_missing_or_unsafe")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("native_campaign_commands_invalid_json") from exc
    if not isinstance(value, dict) or value.get("schema") != COMMAND_SCHEMA:
        raise ManifestError("native_campaign_commands_schema_invalid")
    raw = value.get("stages")
    if not isinstance(raw, dict) or set(raw) != set(STAGES):
        raise ManifestError("native_campaign_commands_require_discovery_load_trigger")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    command_digests = []
    marker_sets = []
    for stage in STAGES:
        plan = raw[stage]
        if not isinstance(plan, dict) or set(plan) != {"argv", "expect_stdout_contains"}:
            raise ManifestError(f"native_campaign_stage_plan_invalid: {stage}")
        command = plan["argv"]
        markers = plan["expect_stdout_contains"]
        if (
            not isinstance(command, list)
            or not 1 <= len(command) <= 64
            or not all(isinstance(item, str) and item and len(item) <= 4096 and "\0" not in item for item in command)
        ):
            raise ManifestError(f"native_campaign_command_invalid: {stage}")
        if (
            not isinstance(markers, list)
            or not 1 <= len(markers) <= 8
            or not all(isinstance(item, str) and item and len(item.encode("utf-8")) <= 256 and "\0" not in item for item in markers)
            or len(set(markers)) != len(markers)
        ):
            raise ManifestError(f"native_campaign_semantic_markers_invalid: {stage}")
        result[stage] = {
            "argv": tuple(command),
            "expect_stdout_contains": tuple(markers),
        }
        command_digests.append(
            sha256_bytes(
                canonical_json_bytes(
                    {"argv": command, "expect_stdout_contains": markers}
                )
            )
        )
        marker_sets.append(tuple(markers))
    if len(set(command_digests)) != len(STAGES):
        raise ManifestError("native_campaign_commands_must_be_independent")
    if len(set(marker_sets)) != len(STAGES):
        raise ManifestError("native_campaign_semantic_markers_must_be_independent")
    return result

def _write_bundle(manifest: Manifest, target: str, profile: str, root: Path) -> tuple[str, int]:
    bundle = render_selection(manifest, target, [profile], asset_kind="skill")
    index = []
    for rendered in bundle.files:
        path = ensure_within(root / rendered.destination, root, "native campaign bundle")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rendered.content)
        path.chmod(rendered.mode)
        index.append(
            {
                "kind": rendered.kind,
                "name": rendered.name,
                "path": rendered.destination,
                "sha256": rendered.sha256,
                "mode": format(rendered.mode, "04o"),
            }
        )
    return sha256_bytes(canonical_json_bytes(index)), len(index)


def _prospective_contract(
    contract_data: Mapping[str, Any],
    *,
    runtime_name: str,
    runtime_sha256: str,
    runtime_version: str,
    authority_id: str,
    verification_backend: str,
) -> tuple[dict[str, Any], str]:
    value = json.loads(json.dumps(contract_data))
    adapter = value["adapter"]
    for capability in STAGES:
        adapter["capabilities"][capability] = "native-verified"
    adapter["conformance"] = {
        "level": "runtime",
        "certification": "conformance-certified",
        "native_runtime_smoke": "pass",
        "runtime_binary": runtime_name,
        "runtime_binary_sha256": runtime_sha256,
        "runtime_version": runtime_version,
        "runtime_version_pin": runtime_version,
        "last_verified_at": None,
        "evidence": [],
    }
    adapter["conformance_trust_policy"] = {
        "enabled": True,
        "trusted_authorities": [authority_id],
        "verification_backend": verification_backend,
    }
    return value, _native_contract_digest(value)


def _kill_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
    process.kill()


def _run_bounded(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    max_output_bytes: int,
) -> dict[str, Any]:
    started_at = _timestamp()
    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=os.name == "posix",
    )
    assert process.stdout is not None and process.stderr is not None
    digests = [hashlib.sha256(), hashlib.sha256()]
    counts = [0, 0]
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()

    def drain(index: int, pipe: Any) -> None:
        while True:
            chunk = pipe.read(64 * 1024)
            if not chunk:
                return
            counts[index] += len(chunk)
            digests[index].update(chunk)
            if len(buffers[index]) <= max_output_bytes:
                remaining = max_output_bytes + 1 - len(buffers[index])
                buffers[index].extend(chunk[:remaining])
            if counts[index] > max_output_bytes:
                overflow.set()
                _kill_process(process)
                return

    readers = [
        threading.Thread(target=drain, args=(0, process.stdout), daemon=True),
        threading.Thread(target=drain, args=(1, process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process(process)
        process.wait(timeout=5)
    for reader in readers:
        reader.join(timeout=2)
    process.stdout.close()
    process.stderr.close()
    completed_at = _timestamp()
    duration_ms = round((time.monotonic() - started) * 1000)
    return {
        "exit_code": process.returncode,
        "timed_out": timed_out,
        "output_budget_exceeded": overflow.is_set(),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": duration_ms,
        "stdout_bytes": counts[0],
        "stderr_bytes": counts[1],
        "stdout_sha256": digests[0].hexdigest(),
        "stderr_sha256": digests[1].hexdigest(),
        "_stdout_raw": bytes(buffers[0]),
    }

def _receipt_schema(manifest: Manifest) -> Mapping[str, Any]:
    path = manifest.root / "schemas" / "native-target-conformance-receipt-v1.schema.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("native_campaign_receipt_schema_invalid") from exc
    if not isinstance(value, dict):
        raise ManifestError("native_campaign_receipt_schema_invalid")
    return value


def run_native_candidate(
    manifest: Manifest,
    *,
    target: str,
    profile: str,
    runtime_binary: Path,
    runtime_name: str,
    runtime_version: str,
    commands_path: Path,
    authority_id: str,
    execution_authority: str,
    verification_backend: str,
    output: Path,
    timeout_seconds: int,
    max_output_bytes: int,
) -> dict[str, Any]:
    if not _ID_RE.fullmatch(runtime_name) or not _ID_RE.fullmatch(runtime_version):
        raise ManifestError("native_campaign_runtime_identity_invalid")
    if not _ID_RE.fullmatch(authority_id):
        raise ManifestError("native_campaign_authority_id_invalid")
    if execution_authority not in ("human-approved", "ci-approved"):
        raise ManifestError("native_campaign_execution_authority_invalid")
    if verification_backend not in ("external-signature-verifier", "ci-provenance-verifier"):
        raise ManifestError("native_campaign_verification_backend_invalid")
    if not 1 <= timeout_seconds <= 600:
        raise ManifestError("native_campaign_timeout_must_be_1_to_600")
    if not 1024 <= max_output_bytes <= 16 * 1024 * 1024:
        raise ManifestError("native_campaign_output_budget_invalid")
    binary = runtime_binary.expanduser().resolve()
    if not binary.is_file():
        raise ManifestError("native_campaign_runtime_binary_missing")
    binary_sha256 = _sha256_file(binary)
    commands = _load_commands(commands_path.resolve())
    contract = load_target_contract(manifest, target)
    prospective, contract_sha256 = _prospective_contract(
        contract.data,
        runtime_name=runtime_name,
        runtime_sha256=binary_sha256,
        runtime_version=runtime_version,
        authority_id=authority_id,
        verification_backend=verification_backend,
    )

    output = output.expanduser().resolve()
    if output.exists() or output.is_symlink():
        raise ManifestError("native_campaign_output_must_not_exist")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="adk-native-campaign-") as temp:
        temp_root = Path(temp).resolve()
        target_root = temp_root / "target"
        workspace = temp_root / "workspace"
        target_root.mkdir()
        workspace.mkdir()
        bundle_sha256, bundle_files = _write_bundle(manifest, target, profile, target_root)
        cwd_sha256 = sha256_bytes(str(workspace).encode("utf-8"))
        base_environment = os.environ.copy()
        base_environment.update(
            {
                "ADK_TARGET": target,
                "ADK_TARGET_ROOT": str(target_root),
                "ADK_NATIVE_CAMPAIGN": "candidate-only",
            }
        )
        stages = []
        stage_results = []
        for stage in STAGES:
            plan = commands[stage]
            command = plan["argv"]
            command_sha256 = sha256_bytes(
                canonical_json_bytes(
                    {
                        "argv": list(command),
                        "expect_stdout_contains": list(plan["expect_stdout_contains"]),
                    }
                )
            )
            environment_descriptor = {
                "target": target,
                "stage": stage,
                "runtime_binary_sha256": binary_sha256,
                "bundle_sha256": bundle_sha256,
                "contract_sha256": contract_sha256,
            }
            env = dict(base_environment)
            env["ADK_TARGET_SMOKE_STAGE"] = stage
            result = _run_bounded(
                command,
                cwd=workspace,
                env=env,
                timeout_seconds=timeout_seconds,
                max_output_bytes=max_output_bytes,
            )
            stage_results.append({"stage": stage, **result})
            if result["timed_out"]:
                return {
                    "schema": SCHEMA,
                    "status": "fail",
                    "stage": stage,
                    "reason": "runtime-timeout",
                    "certification": "not-certified",
                    "promotion_eligible": False,
                    "receipt_written": False,
                }
            if result["output_budget_exceeded"]:
                return {
                    "schema": SCHEMA,
                    "status": "fail",
                    "stage": stage,
                    "reason": "output-budget-exceeded",
                    "certification": "not-certified",
                    "promotion_eligible": False,
                    "receipt_written": False,
                }
            if result["exit_code"] != 0:
                return {
                    "schema": SCHEMA,
                    "status": "fail",
                    "stage": stage,
                    "reason": "runtime-nonzero-exit",
                    "runtime_exit_code": result["exit_code"],
                    "certification": "not-certified",
                    "promotion_eligible": False,
                    "receipt_written": False,
                }
            missing_markers = [
                marker
                for marker in plan["expect_stdout_contains"]
                if marker.encode("utf-8") not in result["_stdout_raw"]
            ]
            if missing_markers:
                return {
                    "schema": SCHEMA,
                    "status": "fail",
                    "stage": stage,
                    "reason": "semantic-marker-missing",
                    "missing_marker_count": len(missing_markers),
                    "certification": "not-certified",
                    "promotion_eligible": False,
                    "receipt_written": False,
                }
            stage_results.append(
                {
                    "stage": stage,
                    "duration_ms": result["duration_ms"],
                    "stdout_bytes": result["stdout_bytes"],
                    "stderr_bytes": result["stderr_bytes"],
                }
            )
            result_sha256 = sha256_bytes(
                canonical_json_bytes(
                    {
                        "stdout_sha256": result["stdout_sha256"],
                        "stderr_sha256": result["stderr_sha256"],
                        "stdout_bytes": result["stdout_bytes"],
                        "stderr_bytes": result["stderr_bytes"],
                    }
                )
            )
            authority = {
                "execution_authority": execution_authority,
                "authority_id": authority_id,
                "scope": stage,
            }
            authority["attestation_sha256"] = _authority_digest(authority)
            stages.append(
                {
                    "stage": stage,
                    "command_sha256": command_sha256,
                    "result_sha256": result_sha256,
                    "exit_code": 0,
                    "started_at": result["started_at"],
                    "completed_at": result["completed_at"],
                    "duration_ms": result["duration_ms"],
                    "environment": {
                        "platform": re.sub(r"[^A-Za-z0-9._:-]", "-", platform.system().lower()) or "unknown",
                        "architecture": re.sub(r"[^A-Za-z0-9._:-]", "-", platform.machine().lower()) or "unknown",
                        "cwd_sha256": cwd_sha256,
                        "environment_sha256": sha256_bytes(canonical_json_bytes(environment_descriptor)),
                        "runtime_binary_sha256": binary_sha256,
                        "bundle_sha256": bundle_sha256,
                        "contract_sha256": contract_sha256,
                    },
                    "privacy": {
                        "raw_content_stored": False,
                        "secrets_stored": False,
                        "sanitized": True,
                    },
                    "authority": authority,
                }
            )
        if len({item["result_sha256"] for item in stages}) != len(STAGES):
            raise ManifestError("native_campaign_stage_results_must_be_independent")
        verified_at = _timestamp()

    receipt = {
        "schema": "adk-native-target-conformance-receipt/v1",
        "receipt_id": "candidate:" + sha256_bytes(
            canonical_json_bytes(
                {
                    "target": target,
                    "runtime_binary_sha256": binary_sha256,
                    "runtime_version": runtime_version,
                    "bundle_sha256": bundle_sha256,
                    "contract_sha256": contract_sha256,
                    "verified_at": verified_at,
                    "stages": [
                        {
                            "stage": item["stage"],
                            "command_sha256": item["command_sha256"],
                            "result_sha256": item["result_sha256"],
                        }
                        for item in stages
                    ],
                }
            )
        )[:32],
        "target": target,
        "runtime": {
            "binary": runtime_name,
            "binary_sha256": binary_sha256,
            "version": runtime_version,
            "version_pin": runtime_version,
        },
        "bundle_sha256": bundle_sha256,
        "contract_sha256": contract_sha256,
        "verified_at": verified_at,
        "stages": stages,
    }
    validator = Draft202012Validator(_receipt_schema(manifest), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(receipt), key=lambda item: tuple(item.absolute_path))
    if errors:
        raise ManifestError("native_campaign_receipt_schema_failure: " + "; ".join(e.message for e in errors))
    payload = canonical_json_bytes(receipt)
    output.write_bytes(payload)
    output.chmod(0o600)
    receipt_sha256 = sha256_bytes(payload)
    return {
        "schema": SCHEMA,
        "status": "pass",
        "target": target,
        "profile": profile,
        "runtime": {
            "binary": runtime_name,
            "binary_sha256": binary_sha256,
            "version": runtime_version,
            "version_pin": runtime_version,
        },
        "bundle_sha256": bundle_sha256,
        "bundle_files": bundle_files,
        "prospective_contract_sha256": contract_sha256,
        "prospective_trust_policy": prospective["adapter"]["conformance_trust_policy"],
        "receipt_path": str(output),
        "receipt_sha256": receipt_sha256,
        "receipt_written": True,
        "stage_results": stage_results,
        "trust_verification": "not-run",
        "certification": "not-certified",
        "promotion_eligible": False,
        "lifecycle_authority": "none-evidence-only",
        "release_authorized": False,
        "limitations": [
            "stage commands and privacy claims are candidate evidence until verified by the configured external trust backend",
            "raw stdout/stderr are hashed and discarded by the campaign collector",
            "the campaign does not modify the target contract or user live runtime directories",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an untrusted native conformance candidate campaign")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--runtime-binary", required=True)
    parser.add_argument("--runtime-name", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--commands", required=True)
    parser.add_argument("--authority-id", required=True)
    parser.add_argument("--execution-authority", choices=("human-approved", "ci-approved"), required=True)
    parser.add_argument(
        "--verification-backend",
        choices=("external-signature-verifier", "ci-provenance-verifier"),
        required=True,
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--max-output-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = Manifest.load(Path(args.root).resolve())
        result = run_native_candidate(
            manifest,
            target=args.target,
            profile=args.profile or manifest.default_profile,
            runtime_binary=Path(args.runtime_binary),
            runtime_name=args.runtime_name,
            runtime_version=args.runtime_version,
            commands_path=Path(args.commands),
            authority_id=args.authority_id,
            execution_authority=args.execution_authority,
            verification_backend=args.verification_backend,
            output=Path(args.output),
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    except (OSError, ValueError, ManifestError, json.JSONDecodeError) as exc:
        result = {
            "schema": SCHEMA,
            "status": "fail",
            "reason": str(exc),
            "certification": "not-certified",
            "promotion_eligible": False,
            "receipt_written": False,
        }
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
