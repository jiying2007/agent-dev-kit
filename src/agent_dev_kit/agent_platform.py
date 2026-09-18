"""Stable Agent Platform primitives.

This module stays control-plane only: it derives effective assets, validates
portable/evidence contracts, and evaluates caller-supplied runtime smokes. A
caller smoke never becomes trusted native-runtime certification.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes
from .target_contracts import load_target_contract
from .targets import render_selection

CONTRACT_PATH = "manifests/agent_platform_contracts.json"
TRACE_SCHEMA_PATH = "schemas/adk-agent-trace-v1.schema.json"
VERIFIER_SCHEMA_PATH = "schemas/independent-verifier-receipt-v1.schema.json"
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


def load_json(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ManifestError(f"{label} missing or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"{label} invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{label} must be a JSON object: {path}")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def load_contract(root: Path) -> Mapping[str, Any]:
    value = load_json(root / CONTRACT_PATH, "agent platform contract")
    if value.get("schema") != "adk-agent-platform-contracts/v1":
        raise ManifestError("agent platform contract schema mismatch")
    return value


def maturity_report(manifest: Manifest, contract: Mapping[str, Any]) -> Dict[str, Any]:
    semantics = contract["maturity_semantics"]
    return {
        "schema": "adk-maturity-semantics-report/v1",
        "status": "pass",
        "adk_version": manifest.version,
        "product_qualification": {
            "authority": semantics["product_qualification"]["authority"],
            "scope": semantics["product_qualification"]["scope"],
            "adk_self_certifies": False,
        },
        "component_release_maturity": semantics["component_release_maturity"],
        "runtime_conformance_ladder": semantics["runtime_conformance_ladder"],
    }


def resolve_effective_profile(
    manifest: Manifest,
    contract: Mapping[str, Any],
    *,
    profiles: Sequence[str],
    optional_skills: Sequence[str],
    target: Optional[str],
    permission_profile: Optional[str],
    project_capabilities: Sequence[str],
    session_capabilities: Sequence[str],
) -> Dict[str, Any]:
    resolution = manifest.resolve_profiles(profiles, optional_skills)
    target_contract = load_target_contract(manifest, target) if target else None
    supported = set(target_contract.supported_asset_kinds) if target_contract else {"agent", "skill"}
    agents: List[Dict[str, Any]] = []
    omitted_agents: List[Dict[str, Any]] = []
    for asset in resolution.agents:
        permission = manifest.asset_record(asset).get("permission_profile")
        item = {"name": asset.name, "permission_profile": permission, "digest": asset.digest}
        reason = None
        if "agent" not in supported:
            reason = "target-does-not-support-agent"
        elif permission_profile and permission not in (permission_profile, "read-only"):
            reason = "permission-profile-mismatch"
        if reason:
            omitted_agents.append({**item, "reason": reason})
        else:
            agents.append(item)
    skills: List[Dict[str, Any]] = []
    omitted_skills: List[Dict[str, Any]] = []
    for asset in resolution.skills:
        item = {"name": asset.name, "optional": asset.optional, "digest": asset.digest}
        if "skill" in supported:
            skills.append(item)
        else:
            omitted_skills.append({**item, "reason": "target-does-not-support-skill"})
    report: Dict[str, Any] = {
        "schema": "adk-effective-profile/v1",
        "profiles": list(resolution.profiles),
        "target": target,
        "permission_profile": permission_profile,
        "project_capabilities": sorted(set(project_capabilities)),
        "session_capabilities": sorted(set(session_capabilities)),
        "effective_capabilities": sorted(set(project_capabilities).union(session_capabilities)),
        "agents": agents,
        "skills": skills,
        "omitted_agents": omitted_agents,
        "omitted_skills": omitted_skills,
        "resolver_policy": contract["capability_resolver"]["policy_id"],
    }
    report["resolution_sha256"] = sha256_bytes(canonical_json_bytes(report))
    report["status"] = "pass"
    return report


def _frontmatter(path: Path) -> Mapping[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ManifestError(f"portable skill source has no frontmatter: {path}")
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if end is None:
        raise ManifestError(f"portable skill source has unterminated frontmatter: {path}")
    value = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(value, dict):
        raise ManifestError(f"portable skill frontmatter must be an object: {path}")
    return value


def portable_skill_audit(manifest: Manifest, contract: Mapping[str, Any]) -> Dict[str, Any]:
    policy = contract["portable_skill"]
    allowed = set(policy["standard_top_level_fields"]).union(policy["internal_extension_fields"])
    failures: List[str] = []
    extensions = 0
    assets = manifest.all_assets("skill")
    for asset in assets:
        metadata = _frontmatter(asset.path / "SKILL.md")
        if metadata.get("name") != asset.name:
            failures.append(f"{asset.name}: name mismatch")
        if not isinstance(metadata.get("description"), str) or not metadata["description"].strip():
            failures.append(f"{asset.name}: description missing")
        unknown = sorted(set(metadata).difference(allowed))
        if unknown:
            failures.append(f"{asset.name}: unknown internal frontmatter {unknown}")
        extensions += len(set(metadata).intersection(policy["internal_extension_fields"]))
    return {
        "schema": "adk-portable-skill-audit/v1",
        "status": "pass" if not failures else "fail",
        "checked_skills": len(assets),
        "internal_extension_fields_seen": extensions,
        "portable_projection_policy": policy["projection_policy"],
        "failures": failures,
    }


def _schema_validation(
    root: Path, schema_path: str, value_path: Path, label: str
) -> Tuple[Mapping[str, Any], List[str]]:
    schema = load_json(root / schema_path, f"{label} schema")
    value = load_json(value_path, label)
    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    failures = [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in errors
    ]
    return value, failures


def validate_trace(root: Path, path: Path) -> Dict[str, Any]:
    value, failures = _schema_validation(root, TRACE_SCHEMA_PATH, path, "agent trace")
    return {
        "schema": "adk-agent-trace-validation/v1",
        "status": "pass" if not failures else "fail",
        "trace_sha256": sha256_bytes(path.read_bytes()),
        "span_count": len(value.get("spans", [])) if isinstance(value.get("spans"), list) else 0,
        "failures": failures,
    }


def validate_independent_verifier(root: Path, path: Path) -> Dict[str, Any]:
    value, failures = _schema_validation(root, VERIFIER_SCHEMA_PATH, path, "independent verifier receipt")
    if value.get("builder_context_id") == value.get("verifier_context_id"):
        failures.append("builder_context_id and verifier_context_id must differ")
    if value.get("verifier_write_capability") is not False:
        failures.append("verifier_write_capability must be false")
    if value.get("evidence_opened") is not True:
        failures.append("evidence_opened must be true")
    return {
        "schema": "adk-independent-verifier-validation/v1",
        "status": "pass" if not failures else "fail",
        "receipt_sha256": sha256_bytes(path.read_bytes()),
        "failures": sorted(set(failures)),
    }


def loop_decision(
    contract: Mapping[str, Any],
    *,
    iterations: int,
    wall_time_seconds: float,
    cost_usd: float,
    tokens: int,
    consecutive_no_progress: int,
    evaluator_pass: bool,
    approval_escape: bool,
) -> Dict[str, Any]:
    policy = contract["loop_policy"]["defaults"]
    reasons = []
    if iterations >= policy["max_iterations"]:
        reasons.append("iteration-budget")
    if wall_time_seconds >= policy["max_wall_time_seconds"]:
        reasons.append("wall-time-budget")
    if cost_usd >= policy["max_cost_usd"]:
        reasons.append("cost-budget")
    if tokens >= policy["max_tokens"]:
        reasons.append("token-budget")
    if consecutive_no_progress >= policy["no_progress_limit"]:
        reasons.append("no-progress-limit")
    if evaluator_pass:
        decision = "complete"
    elif approval_escape:
        decision = "hold-owner"
        reasons.append("approval-escape")
    elif reasons:
        decision = "stop-needs-evidence"
    else:
        decision = "continue"
    return {
        "schema": "adk-loop-decision/v1",
        "status": "pass",
        "decision": decision,
        "reasons": sorted(set(reasons)),
        "fresh_context_required": policy["fresh_context"],
        "checkpoint_policy": policy["checkpoint_policy"],
    }


def _asset_refs(manifest: Manifest) -> Tuple[Set[str], Set[str]]:
    agent_refs: Set[str] = set()
    skill_refs: Set[str] = set()
    profiles = manifest.data.get("profiles", {})
    if isinstance(profiles, dict):
        for value in profiles.values():
            if isinstance(value, dict):
                agent_refs.update(str(item) for item in value.get("include_agents", []) if isinstance(item, str))
                skill_refs.update(str(item) for item in value.get("include_skills", []) if isinstance(item, str))
    for record in manifest.data.get("agents", []):
        if isinstance(record, dict):
            for field in ("default_skills", "skills"):
                skill_refs.update(str(item) for item in record.get(field, []) if isinstance(item, str))
    return agent_refs, skill_refs


def asset_usage_report(
    manifest: Manifest, contract: Mapping[str, Any], telemetry_path: Optional[Path]
) -> Dict[str, Any]:
    telemetry: Mapping[str, Any] = load_json(telemetry_path, "asset usage telemetry") if telemetry_path else {}
    rows = telemetry.get("assets", {}) if isinstance(telemetry.get("assets", {}), dict) else {}
    agent_refs, skill_refs = _asset_refs(manifest)
    entries = [("agent", asset, agent_refs) for asset in manifest.all_assets("agent")]
    entries.extend(
        ("optional_skill" if asset.optional else "skill", asset, skill_refs)
        for asset in manifest.all_assets("skill")
    )
    reports: List[Dict[str, Any]] = []
    dead: List[str] = []
    for kind, asset, refs in entries:
        key = f"{kind}:{asset.name}"
        row = rows.get(key, {}) if isinstance(rows.get(key, {}), dict) else {}
        advertised = int(row.get("advertised_count", 0))
        activated = int(row.get("activated_count", 0))
        completion = float(row.get("completion_rate", 0.0))
        quality = float(row.get("quality_delta", 0.0))
        referenced = asset.name in refs
        decision = "not-measured" if telemetry_path is None else "keep"
        if telemetry_path is not None and not referenced and advertised == 0 and activated == 0:
            decision = "review-dead"
            dead.append(key)
        elif telemetry_path is not None and advertised >= contract["asset_usage"]["min_advertisements_for_prune"]:
            if activated == 0:
                decision = "review-archive"
            elif (
                quality < contract["asset_usage"]["min_quality_delta"]
                or completion < contract["asset_usage"]["min_completion_rate"]
            ):
                decision = "review-merge-or-demote"
        reports.append(
            {
                "asset": key,
                "referenced": referenced,
                "advertised_count": advertised,
                "activated_count": activated,
                "activation_rate": activated / advertised if advertised else None,
                "completion_rate": completion if telemetry_path else None,
                "quality_delta": quality if telemetry_path else None,
                "decision": decision,
            }
        )
    return {
        "schema": "adk-asset-usage-report/v1",
        "status": "pass" if telemetry_path else "not-measured",
        "assets": reports,
        "dead_candidates": sorted(dead),
        "auto_archive_allowed": False,
    }


def aci_benchmark(contract: Mapping[str, Any], metrics_path: Path) -> Dict[str, Any]:
    metrics = load_json(metrics_path, "ACI metrics")
    failures = []
    for key, rule in contract["aci_benchmark"]["thresholds"].items():
        if key not in metrics:
            failures.append(f"missing metric: {key}")
            continue
        value = float(metrics[key])
        if "max" in rule and value > float(rule["max"]):
            failures.append(f"{key}={value} exceeds max={rule['max']}")
        if "min" in rule and value < float(rule["min"]):
            failures.append(f"{key}={value} below min={rule['min']}")
    return {
        "schema": "adk-aci-benchmark/v1",
        "status": "pass" if not failures else "fail",
        "metrics": dict(metrics),
        "failures": failures,
    }


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


def _run_stage(command: Sequence[str], stage: str, env: Mapping[str, str], timeout: int) -> Dict[str, Any]:
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


def hooks_report(contract: Mapping[str, Any]) -> Dict[str, Any]:
    hook_ir = contract["hook_lifecycle_ir"]
    return {
        "schema": "adk-hook-lifecycle-ir-report/v1",
        "status": "pass",
        "events": hook_ir["events"],
        "allowed_effects": hook_ir["allowed_effects"],
        "forbidden_effects": hook_ir["forbidden_effects"],
    }
