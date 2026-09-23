"""Caller-supplied target runtime conformance planning and execution."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from .agent_platform import load_json
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .target_contracts import load_target_contract
from .targets import render_selection

CONFORMANCE_STAGES = (
    "render",
    "install",
    "discovery",
    "load",
    "positive-trigger",
    "negative-trigger",
    "permission",
    "tool-invocation",
    "handoff",
    "cancel",
    "resume",
    "trace",
    "rollback",
)


def target_conformance_plan(
    manifest: Manifest, contract: Mapping[str, Any], target: str, profile: Optional[str]
) -> Dict[str, Any]:
    target_contract = load_target_contract(manifest, target)
    bundle = render_selection(
        manifest,
        target,
        [profile or manifest.default_profile],
        asset_kind=(
            target_contract.supported_asset_kinds[0]
            if len(target_contract.supported_asset_kinds) == 1
            else None
        ),
    )
    identity = [
        {"destination": item.destination, "sha256": item.sha256, "mode": item.mode}
        for item in bundle.files
    ]
    return {
        "schema": "adk-native-conformance-plan/v1",
        "status": "ready",
        "certification": "not-certified",
        "target": target,
        "profile": profile or manifest.default_profile,
        "contract_sha256": target_contract.digest,
        "bundle_sha256": sha256_bytes(canonical_json_bytes(identity)),
        "stages": [{"stage": stage, "status": "required"} for stage in CONFORMANCE_STAGES],
        "ladder": list(contract["runtime_conformance"]["ladder"]),
        "trusted_native_evidence_authority": "target-contract-conformance-receipt",
    }


def _run_stage(
    command: Sequence[str], stage: str, env: Mapping[str, str], timeout: int
) -> Dict[str, Any]:
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(env),
            timeout=timeout,
        )
        exit_code = completed.returncode
        timed_out = False
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        timed_out = True
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
    completed_at = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "stage": stage,
        "status": "pass" if exit_code == 0 and not timed_out else "fail",
        "exit_code": exit_code,
        "timed_out": timed_out,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
        "duration_ms": round((time.monotonic() - started) * 1000.0, 3),
        "command_sha256": sha256_bytes(canonical_json_bytes(list(command))),
        "stdout_sha256": sha256_bytes(stdout),
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_bytes": len(stdout),
        "stderr_bytes": len(stderr),
    }


def run_target_conformance(
    manifest: Manifest,
    contract: Mapping[str, Any],
    target: str,
    profile: Optional[str],
    command_file: Path,
    timeout_seconds: int,
) -> Dict[str, Any]:
    plan = target_conformance_plan(manifest, contract, target, profile)
    commands = load_json(command_file, "native conformance command map").get("commands")
    if not isinstance(commands, dict):
        raise ManifestError("native conformance command map requires commands object")
    missing = [stage for stage in CONFORMANCE_STAGES if stage not in commands]
    if missing:
        return {
            **plan,
            "status": "blocked",
            "blocking_stages": missing,
            "reason": "complete stage command coverage required",
        }
    env = os.environ.copy()
    env.update(
        {
            "ADK_TARGET": target,
            "ADK_TARGET_BUNDLE_SHA256": plan["bundle_sha256"],
            "ADK_TARGET_CONTRACT_SHA256": plan["contract_sha256"],
        }
    )
    results = []
    for stage in CONFORMANCE_STAGES:
        raw = commands[stage]
        if isinstance(raw, str):
            command = shlex.split(raw)
        elif isinstance(raw, list) and all(isinstance(item, str) for item in raw):
            command = list(raw)
        else:
            command = []
        if not command:
            raise ManifestError(f"invalid native conformance command for {stage}")
        stage_env = dict(env)
        stage_env["ADK_TARGET_CONFORMANCE_STAGE"] = stage
        result = _run_stage(command, stage, stage_env, timeout_seconds)
        results.append(result)
        if result["status"] != "pass":
            break
    all_pass = len(results) == len(CONFORMANCE_STAGES) and all(
        item["status"] == "pass" for item in results
    )
    return {
        **plan,
        "schema": "adk-native-conformance-run/v1",
        "status": "pass" if all_pass else "fail",
        "certification": "caller-supplied-full-smoke" if all_pass else "not-certified",
        "conformance_level": "behavior-evaluated" if all_pass else "static-compatible",
        "native_runtime_certified": False,
        "promotion_note": (
            "runtime-certified requires trusted target-contract native conformance receipt evidence"
        ),
        "results": results,
    }
