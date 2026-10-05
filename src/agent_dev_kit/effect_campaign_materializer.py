"""Materialize validated runtime campaign state into effect-trials Run Evidence.

This module performs no model/runtime execution. It only converts already
validated resumable campaign result records into privacy-bounded trace-only Run
Evidence and a canonical adk-effect-trials/v1 document.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from jsonschema import Draft202012Validator, FormatChecker

from . import campaign_model as _campaign_model
from .campaign_analysis import _validate_result
from .agent_value_contracts import load_contract
from .contracts.schema_loader import packaged_schema_bytes
from .evaluation import RUNTIME_ROUTING_PROMPT_VERSION
from .model import Manifest, ManifestError, canonical_json_bytes, sha256_bytes, sha256_file
from .privacy_ref import opaque_ref_for_sha256
from .run_evidence import RunEvidenceObservation, emit_run_evidence
from .strict_json import StrictJSONError, read as read_json
from .trace_summary import (
    CostFact,
    GuardrailFact,
    MetricUnavailable,
    OutcomeFact,
    TokenUsageFact,
    TraceRunFacts,
    VerificationFact,
)

_EFFECT_SCHEMA = "adk-effect-trials/v1"
_VERSION_RE = re.compile(r"(?<![0-9A-Za-z])([0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z._-]+)?)")


def _time(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ManifestError(f"{label} must be a timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError(f"{label} is invalid") from exc
    if parsed.tzinfo is None:
        raise ManifestError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _runtime_version_token(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError("campaign runtime version is missing")
    stripped = value.strip()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", stripped):
        return stripped
    match = _VERSION_RE.search(stripped)
    if match is None:
        raise ManifestError("campaign runtime version cannot be normalized for effect evidence")
    return match.group(1)


def _load_effect_plan(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ManifestError("effect plan is missing or unsafe")
    if path.stat().st_size > 1024 * 1024:
        raise ManifestError("effect plan exceeds byte budget")
    try:
        value = read_json(path, max_bytes=1024 * 1024)
    except StrictJSONError as exc:
        raise ManifestError("effect plan is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ManifestError("effect plan must be an object")
    schema = json.loads(packaged_schema_bytes("effect-trials-v1.schema.json"))
    plan_schema = schema.get("properties", {}).get("plan")
    if not isinstance(plan_schema, dict):
        raise ManifestError("packaged effect plan schema is invalid")
    errors = sorted(
        Draft202012Validator(plan_schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(map(str, first.absolute_path)) or "<root>"
        raise ManifestError(f"effect plan schema failure at {location}: {first.message}")
    return value


def _state_plan(
    manifest: Manifest,
    contract: Mapping[str, Any],
    tasks_path: Path,
    task_count: int,
    state_dir: Path,
) -> dict[str, Any]:
    plan = _campaign_model._load_json_object(state_dir / "campaign-plan.json", "campaign plan")
    _campaign_model._validate_plan_integrity(plan)
    expected = {
        "campaign_id": contract["campaign_id"],
        "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest,
        "contract_sha256": _campaign_model._digest(contract),
        "tasks_sha256": sha256_file(tasks_path),
        "task_count": task_count,
        "conditions": contract["conditions"],
        "trials": contract["trials"],
    }
    for field, value in expected.items():
        if plan.get(field) != value:
            raise ManifestError(f"campaign state plan {field} differs from current contract")
    return plan


def _usage_fact(attempts: Sequence[Mapping[str, Any]]) -> TokenUsageFact | MetricUnavailable:
    keys = ("input_tokens", "cached_input_tokens", "output_tokens")
    if not all(
        isinstance(attempt.get("usage"), dict)
        and all(isinstance(attempt["usage"].get(key), int) for key in keys)
        for attempt in attempts
    ):
        return MetricUnavailable("runtime-token-usage-incomplete")
    totals = {key: sum(int(attempt["usage"][key]) for attempt in attempts) for key in keys}
    return TokenUsageFact(totals["input_tokens"], totals["cached_input_tokens"], totals["output_tokens"])


def _cost_fact(runtime: str, attempts: Sequence[Mapping[str, Any]]) -> CostFact | MetricUnavailable:
    if runtime != "claude":
        return MetricUnavailable("runtime-pricing-unavailable")
    if not all(attempt.get("cost_evidence") == "runtime-reported" for attempt in attempts):
        return MetricUnavailable("runtime-cost-upper-bound-only")
    return CostFact(
        round(sum(float(attempt["cost_usd"]) for attempt in attempts), 6),
        "USD",
    )


def _run_evidence(
    manifest: Manifest,
    record: Mapping[str, Any],
    validated: Mapping[str, Any],
    task: Mapping[str, Any],
    effect_plan: Mapping[str, Any],
    side: str,
) -> Mapping[str, Any]:
    final = record["final"]
    attempts = record["attempts"]
    error = final.get("error")
    route_ok = bool(validated["route_ok"])
    safe_ok = bool(validated["safe_ok"])
    passed = bool(validated["passed"])
    if error is not None:
        outcome = OutcomeFact("failed", "runtime-failure")
        blockers = ("runtime-error",)
        failure_pattern = "runtime-error"
    elif passed:
        outcome = OutcomeFact("succeeded", "completed")
        blockers = ()
        failure_pattern = "none"
    else:
        outcome = OutcomeFact("failed", "validation-failure")
        values = []
        if not route_ok:
            values.append("routing-mismatch")
        if not safe_ok:
            values.append("safety-mismatch")
        blockers = tuple(values or ["validation-failure"])
        failure_pattern = "-and-".join(values) if values else "validation-failure"

    actual_skill = final.get("actual_skill")
    primary_skill = (
        actual_skill
        if isinstance(actual_skill, str)
        and re.fullmatch(r"[a-z0-9][a-z0-9._:/-]{0,127}", actual_skill)
        else "runtime-error"
    )
    record_ref = opaque_ref_for_sha256(str(record["record_sha256"]))
    observed_at = _time(record["recorded_at"], "campaign result recorded_at")
    window = effect_plan["window"]
    if not _time(window["from"], "effect window from") <= observed_at <= _time(
        window["through"], "effect window through"
    ):
        raise ManifestError("campaign result is outside the frozen effect observation window")

    facts = TraceRunFacts(
        run_id="effect-" + str(record["record_sha256"])[:40],
        task_id=str(task["id"]),
        asset_bundle_sha256=str(effect_plan["bundles"][side]),
        runtime_target=str(effect_plan["controls"]["runtime_target"]),
        runtime_version=str(effect_plan["controls"]["runtime_version"]),
        model_version=str(effect_plan["controls"]["model_version"]),
        goal_ref=opaque_ref_for_sha256(str(record["task_sha256"])),
        primary_skill=primary_skill,
        prompt_version=str(effect_plan["controls"]["prompt_version"]),
        orchestration_mode=str(effect_plan["controls"]["orchestration_mode"]),
        tools_used=(),
        handoffs=(),
        guardrails=(GuardrailFact("safety-policy", "passed" if safe_ok else "failed"),),
        verification=(
            VerificationFact("route-match", "passed" if route_ok else "failed", record_ref),
            VerificationFact("safety-match", "passed" if safe_ok else "failed", record_ref),
        ),
        elapsed_ms=max(0, int(round(float(validated["elapsed_ms"])))),
        first_pass_success=passed and int(validated["attempts"]) == 1,
        human_interventions=0,
        wrong_skill=not route_ok,
        abstained=False,
        privacy_status="no-sensitive-content",
        blockers=blockers,
        failure_pattern=failure_pattern,
        next_goal_ref=None,
        token_usage=_usage_fact(attempts),
        cost=_cost_fact(str(record["runtime"]), attempts),
        outcome=outcome,
    )
    contract = load_contract(manifest.root / "manifests" / "agent_value_contracts.json")
    return emit_run_evidence(
        RunEvidenceObservation(trace_facts=facts, observed_at=observed_at),
        manifest,
        contract,
    )


def materialize_effect_campaign(
    manifest: Manifest,
    contract_path: Path,
    state_dir: Path,
    effect_plan_path: Path,
    runtime: str,
    campaign_root: Optional[Path] = None,
) -> dict[str, Any]:
    contract, tasks_path, tasks = _campaign_model.load_campaign_contract(
        manifest, contract_path, campaign_root
    )
    if runtime not in contract["runtimes"]:
        raise ManifestError("selected runtime is not part of the campaign contract")
    if contract["conditions"] != ["baseline", "adk"]:
        raise ManifestError("effect materialization requires baseline/adk campaign conditions")
    effect_plan = _load_effect_plan(effect_plan_path)
    if effect_plan["controls"]["runtime_target"] != runtime:
        raise ManifestError("effect plan runtime_target differs from selected campaign runtime")
    if effect_plan["controls"]["model_identity"] != "revision-bound":
        raise ManifestError("effect materialization requires model_identity=revision-bound")
    if effect_plan["controls"]["prompt_version"] != RUNTIME_ROUTING_PROMPT_VERSION:
        raise ManifestError("effect plan prompt_version differs from runtime routing prompt contract")
    if effect_plan["controls"]["orchestration_mode"] != "single-agent":
        raise ManifestError("effect materialization requires single-agent orchestration")

    state_dir = state_dir.resolve()
    state_plan = _state_plan(manifest, contract, tasks_path, len(tasks), state_dir)
    runtime_entry = _campaign_model._runtime_entry(state_plan, runtime)
    if effect_plan["controls"]["runtime_version"] != _runtime_version_token(
        runtime_entry.get("runtime_version")
    ):
        raise ManifestError("effect plan runtime_version differs from frozen campaign runtime")
    if effect_plan["controls"]["model_version"] != runtime_entry.get("requested_model"):
        raise ManifestError("effect plan model_version differs from frozen campaign model")

    task_ids = [str(task["id"]) for task in tasks]
    if effect_plan["task_ids"] != task_ids:
        raise ManifestError("effect plan task_ids differ from campaign task population")
    expected_trials = [f"trial-{index}" for index in range(1, int(contract["trials"]) + 1)]
    if effect_plan["trial_ids"] != expected_trials:
        raise ManifestError("effect plan trial_ids differ from campaign trials")

    plan_ref = opaque_ref_for_sha256(sha256_bytes(canonical_json_bytes(effect_plan)))
    controls_ref = opaque_ref_for_sha256(
        sha256_bytes(canonical_json_bytes(effect_plan["controls"]))
    )
    trials = []
    for trial_number, trial_id in enumerate(expected_trials, start=1):
        trial = {
            "trial_id": trial_id,
            "infrastructure_status": "ok",
            "baseline": [],
            "candidate": [],
        }
        for side, condition in (("baseline", "baseline"), ("candidate", "adk")):
            for task in tasks:
                path = _campaign_model._result_path(
                    state_dir, runtime, condition, trial_number, str(task["id"])
                )
                if not path.is_file():
                    raise ManifestError(f"campaign result is missing: {path.relative_to(state_dir)}")
                record = _campaign_model._load_json_object(path, "campaign result")
                validated = _validate_result(
                    record,
                    state_plan,
                    task,
                    runtime,
                    condition,
                    trial_number,
                    int(contract["retry_limit"]),
                    float(contract["max_claude_call_usd"]),
                )
                reported = validated.get("reported_models")
                requested = runtime_entry.get("requested_model")
                if isinstance(reported, list) and reported and requested not in reported:
                    raise ManifestError("campaign reported model differs from frozen requested model")
                if validated.get("error") is not None:
                    trial["infrastructure_status"] = "failed"
                trial[side].append(
                    {
                        "plan_ref": plan_ref,
                        "controls_ref": controls_ref,
                        "run": _run_evidence(
                            manifest, record, validated, task, effect_plan, side
                        ),
                    }
                )
        trials.append(trial)

    document = {
        "schema_version": _EFFECT_SCHEMA,
        "plan": effect_plan,
        "trials": trials,
    }
    schema = json.loads(packaged_schema_bytes("effect-trials-v1.schema.json"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        first = errors[0]
        location = "/".join(map(str, first.absolute_path)) or "<root>"
        raise ManifestError(f"materialized effect campaign schema failure at {location}: {first.message}")
    return document
