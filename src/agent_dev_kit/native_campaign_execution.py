"""Bounded native target campaign execution."""

from __future__ import annotations

import asyncio
import hashlib
import os
import platform
import re
import signal
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .native_campaign_contract import (
    EVIDENCE_SCHEMA,
    MAX_OUTPUT_BYTES,
    MAX_VERSION_OUTPUT_BYTES,
    PLAN_SCHEMA,
    STAGES,
    _bundle_identity,
    native_campaign_target_layout,
    _runtime_binary,
    _sha256_file,
    _timestamp,
    _utc_now,
    _validate_assertion_command_separation,
    _validate_assertions,
    _validate_commands,
)
from .target_contracts import _native_contract_digest, load_target_contract
from .targets import _write_bundle, render_selection


def _kill_process(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except ProcessLookupError:
            return
    process.kill()


async def _drain(
    stream: asyncio.StreamReader,
    process: asyncio.subprocess.Process,
    limit: int,
) -> tuple[int, str, bytes]:
    digest = hashlib.sha256()
    total = 0
    captured = bytearray()
    while True:
        chunk = await stream.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            _kill_process(process)
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
        _kill_process(process)
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


def _semantic_assertion(
    result: Mapping[str, Any], assertion: Mapping[str, Any]
) -> tuple[bool, str]:
    stream = str(assertion["stream"])
    if stream == "stdout":
        raw = bytes(result["stdout"])
    elif stream == "stderr":
        raw = bytes(result["stderr"])
    else:
        raw = bytes(result["stdout"]) + b"\\n" + bytes(result["stderr"])
    try:
        decoded = raw.decode("utf-8", errors="strict")
        decode_status = "utf8"
    except UnicodeDecodeError:
        decoded = ""
        decode_status = "invalid-utf8"
    needle = str(assertion["contains"])
    haystack = decoded
    if assertion["case_sensitive"] is False:
        needle = needle.casefold()
        haystack = haystack.casefold()
    occurrences = haystack.count(needle) if decode_status == "utf8" else 0
    passed = occurrences > 0
    summary = {
        "stream": stream,
        "case_sensitive": bool(assertion["case_sensitive"]),
        "decode_status": decode_status,
        "matched": passed,
        "occurrences": occurrences,
        "observed_bytes": len(raw),
    }
    return passed, sha256_bytes(canonical_json_bytes(summary))


def _blocked_version_evidence(
    plan: Mapping[str, Any],
    version_probe: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": EVIDENCE_SCHEMA,
        "status": "blocked",
        "reason": "runtime-version-probe-failed",
        "campaign_id": plan["campaign_id"],
        "target": plan["target"],
        "profile": plan["profile"],
        "runtime": dict(plan["runtime"]),
        "bundle_sha256": plan["bundle_sha256"],
        "candidate_contract_normalized_sha256": plan[
            "candidate_contract_normalized_sha256"
        ],
        "version_probe": {
            key: value
            for key, value in version_probe.items()
            if key not in ("stdout", "stderr")
        },
        "stages": [],
        "privacy": dict(plan["privacy"]),
        "lifecycle_authority": "none-campaign-only",
        "release_authorized": False,
    }


def _stage_environment(
    plan: Mapping[str, Any],
    base_env: Mapping[str, str],
    project_root: Path,
    target_root: Path,
    stage: str,
) -> dict[str, str]:
    env = dict(base_env)
    env.update(
        {
            "ADK_TARGET": str(plan["target"]),
            "ADK_TARGET_PROJECT_ROOT": str(project_root),
            "ADK_TARGET_ROOT": str(target_root),
            "ADK_TARGET_SMOKE_STAGE": stage,
        }
    )
    return env


def run_campaign(
    manifest: Manifest,
    plan: Mapping[str, Any],
    candidate_contract: Mapping[str, Any],
    commands: Mapping[str, Sequence[str]],
    assertions: Mapping[str, Mapping[str, Any]],
    runtime_binary: Path,
) -> dict[str, Any]:
    if plan.get("schema") != PLAN_SCHEMA or plan.get("status") != "ready":
        raise ManifestError("native_campaign_plan_invalid")
    commands_value = _validate_commands(dict(commands))
    assertions_value = _validate_assertions(dict(assertions))
    _validate_assertion_command_separation(commands_value, assertions_value)
    runtime_binary = _runtime_binary(str(runtime_binary))
    if (
        runtime_binary.name != plan["runtime"]["binary"]
        or _sha256_file(runtime_binary) != plan["runtime"]["binary_sha256"]
    ):
        raise ManifestError("native_campaign_runtime_identity_drift")
    version_command = commands_value["version"]
    for name in ("version", *STAGES):
        if _runtime_binary(commands_value[name][0]) != runtime_binary:
            raise ManifestError(
                f"native_campaign_command_must_use_runtime_binary: {name}"
            )
        digest = sha256_bytes(canonical_json_bytes(commands_value[name]))
        if digest != plan["command_sha256"][name]:
            raise ManifestError(f"native_campaign_command_drift: {name}")
    for stage in STAGES:
        digest = sha256_bytes(canonical_json_bytes(assertions_value[stage]))
        if digest != plan["assertion_sha256"][stage]:
            raise ManifestError(f"native_campaign_assertion_drift: {stage}")
    if (
        sha256_bytes(canonical_json_bytes(candidate_contract))
        != plan["candidate_contract_sha256"]
    ):
        raise ManifestError("native_campaign_candidate_contract_drift")
    if (
        _native_contract_digest(candidate_contract)
        != plan["candidate_contract_normalized_sha256"]
    ):
        raise ManifestError("native_campaign_candidate_contract_normalized_drift")
    current = load_target_contract(manifest, str(plan["target"]))
    if (
        current.digest != plan["source_contract_sha256"]
        or manifest.version != plan["source_version"]
    ):
        raise ManifestError("native_campaign_source_drift")
    bundle_digest, bundle_files = _bundle_identity(
        manifest, str(plan["target"]), str(plan["profile"])
    )
    if bundle_digest != plan["bundle_sha256"] or bundle_files != plan["bundle_files"]:
        raise ManifestError("native_campaign_bundle_drift")

    base_env = _base_environment(str(plan["auth_mode"]))
    base_env["PATH"] = str(runtime_binary.parent) + os.pathsep + os.defpath
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
    planned_version = str(plan["runtime"]["version"])
    version_pattern = re.compile(
        r"(?<![A-Za-z0-9._+:-])"
        + re.escape(planned_version)
        + r"(?![A-Za-z0-9._+:-])"
    )
    if version_probe["exit_code"] != 0 or version_pattern.search(decoded) is None:
        return _blocked_version_evidence(plan, version_probe)

    bundle = render_selection(
        manifest,
        str(plan["target"]),
        [str(plan["profile"])],
        asset_kind="skill",
    )
    stage_records: list[dict[str, Any]] = []
    target_layout = native_campaign_target_layout(manifest, str(plan["target"]))
    with tempfile.TemporaryDirectory(prefix="adk-native-campaign-") as temporary:
        project_root = Path(temporary) / "project"
        project_root.mkdir()
        target_root = project_root / str(target_layout["project_config_dir"])
        target_root.mkdir()
        _write_bundle(target_root, bundle)
        environment_descriptor = {
            "auth_mode": plan["auth_mode"],
            "environment_keys": sorted(base_env),
            "target": plan["target"],
            "profile": plan["profile"],
            "asset_kind": "skill",
            "discovery_scope": target_layout["discovery_scope"],
            "project_config_dir": target_layout["project_config_dir"],
            "runtime_cwd": "project-root",
        }
        environment_digest = sha256_bytes(canonical_json_bytes(environment_descriptor))
        cwd_digest = sha256_bytes(str(project_root.resolve()).encode("utf-8"))
        previous_failed = False
        for stage in STAGES:
            if previous_failed:
                stage_records.append(
                    {
                        "stage": stage,
                        "status": "blocked",
                        "reason": "previous-stage-failed",
                        "command_sha256": plan["command_sha256"][stage],
                        "assertion_sha256": plan["assertion_sha256"][stage],
                        "semantic_assertion_status": "not-run",
                    }
                )
                continue
            env = _stage_environment(plan, base_env, project_root, target_root, stage)
            started_at = _utc_now()
            try:
                result = _execute(
                    commands_value[stage],
                    cwd=project_root,
                    env=env,
                    timeout_seconds=int(plan["timeout_seconds"]),
                    output_limit=MAX_OUTPUT_BYTES,
                )
                completed_at = _utc_now()
                assertion_passed = False
                assertion_result_sha256 = None
                semantic_status = "not-run"
                if result["exit_code"] == 0:
                    assertion_passed, assertion_result_sha256 = _semantic_assertion(
                        result, assertions_value[stage]
                    )
                    semantic_status = "pass" if assertion_passed else "fail"
                status = (
                    "pass"
                    if result["exit_code"] == 0 and assertion_passed
                    else "fail"
                )
                result_view = {
                    key: value
                    for key, value in result.items()
                    if key not in ("stdout", "stderr")
                }
                result_view.update(
                    {
                        "assertion_sha256": plan["assertion_sha256"][stage],
                        "semantic_assertion_status": semantic_status,
                        "assertion_result_sha256": assertion_result_sha256,
                    }
                )
                result_digest = sha256_bytes(canonical_json_bytes(result_view))
                record = {
                    "stage": stage,
                    "status": status,
                    "command_sha256": plan["command_sha256"][stage],
                    "assertion_sha256": plan["assertion_sha256"][stage],
                    "semantic_assertion_status": semantic_status,
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
                if assertion_result_sha256 is not None:
                    record["assertion_result_sha256"] = assertion_result_sha256
                if result["exit_code"] != 0:
                    record["reason"] = "runtime-exit-nonzero"
                elif not assertion_passed:
                    record["reason"] = "semantic-assertion-failed"
                stage_records.append(record)
                previous_failed = status != "pass"
            except (ManifestError, asyncio.TimeoutError) as exc:
                completed_at = _utc_now()
                stage_records.append(
                    {
                        "stage": stage,
                        "status": "fail",
                        "reason": str(exc),
                        "command_sha256": plan["command_sha256"][stage],
                        "assertion_sha256": plan["assertion_sha256"][stage],
                        "semantic_assertion_status": "not-run",
                        "started_at": _timestamp(started_at),
                        "completed_at": _timestamp(completed_at),
                    }
                )
                previous_failed = True

    complete = all(item.get("status") == "pass" for item in stage_records)
    return {
        "schema": EVIDENCE_SCHEMA,
        "status": "complete" if complete else "failed",
        "campaign_id": plan["campaign_id"],
        "target": plan["target"],
        "profile": plan["profile"],
        "runtime": dict(plan["runtime"]),
        "bundle_sha256": plan["bundle_sha256"],
        "candidate_contract_normalized_sha256": plan[
            "candidate_contract_normalized_sha256"
        ],
        "version_probe": {
            key: value
            for key, value in version_probe.items()
            if key not in ("stdout", "stderr")
        },
        "stages": stage_records,
        "privacy": dict(plan["privacy"]),
        "completed_at": _timestamp(_utc_now()),
        "lifecycle_authority": "none-campaign-only",
        "release_authorized": False,
    }
