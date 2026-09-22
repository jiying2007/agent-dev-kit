"""Repository-evaluation result validation and deterministic certification."""

from __future__ import annotations

import math
import statistics
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .model import Manifest, ManifestError, sha256_file
from .repository_evaluation_contract import (
    CUSTOMIZATION_SURFACES,
    PROCESS_FIELDS,
    USAGE_FIELDS,
    _digest,
    _load_object,
    _require_string,
    load_repository_contract,
)


REPORT_SCHEMA = "adk-repository-runtime-eval-report/v1"
CERTIFICATION_SCHEMA = "adk-repository-runtime-eval-certification/v1"


def _nearest_rank(values: Sequence[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return round(float(ordered[index]), 6)


def _distribution(values: Sequence[float]) -> Dict[str, float]:
    if not values:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0, "coefficient_of_variation": 0.0}
    mean = statistics.fmean(values)
    variation = statistics.pstdev(values) / mean if len(values) > 1 and mean else 0.0
    return {
        "p50": _nearest_rank(values, 0.50),
        "p95": _nearest_rank(values, 0.95),
        "max": round(max(values), 6),
        "coefficient_of_variation": round(variation, 6),
    }


def _validate_result(
    result: Mapping[str, Any],
    task: Mapping[str, Any],
    adapter: Mapping[str, Any],
    condition: str,
) -> Dict[str, Any]:
    task_id = str(task["id"])
    if result.get("repository_revision") != task["repository_revision"]:
        raise ManifestError("repository revision does not match task provenance: {}".format(task_id))
    if result.get("container_digest") != task["container_digest"]:
        raise ManifestError("container digest does not match task provenance: {}".format(task_id))
    if result.get("adapter_id") != adapter["adapter_id"]:
        raise ManifestError("repository result adapter does not match contract: {}".format(task_id))
    isolation = result.get("isolation")
    if not isinstance(isolation, dict) or isolation.get("verified") is not True:
        raise ManifestError("customization isolation is not verified: {}".format(task_id))
    strategy_field = "baseline_isolation" if condition == "baseline" else "adk_isolation"
    if isolation.get("strategy") != adapter[strategy_field]:
        raise ManifestError("customization isolation strategy does not match contract: {}".format(task_id))
    disabled = set(isolation.get("disabled_surfaces", []))
    enabled = set(isolation.get("enabled_surfaces", []))
    if condition == "baseline":
        if disabled != CUSTOMIZATION_SURFACES or enabled:
            raise ManifestError("baseline customization surfaces are not fully isolated: {}".format(task_id))
    else:
        if enabled != set(adapter["adk_enabled_surfaces"]):
            raise ManifestError("ADK customization surfaces do not match the reviewed profile: {}".format(task_id))
        if not set(adapter["always_disabled_surfaces"]) <= disabled or enabled & disabled:
            raise ManifestError("ADK disabled customization surfaces are invalid: {}".format(task_id))
    outcome = result.get("outcome")
    if not isinstance(outcome, dict) or outcome.get("status") not in {"pass", "fail"}:
        raise ManifestError("repository outcome is invalid: {}".format(task_id))
    functional = outcome.get("functional_tests_passed")
    security = outcome.get("security_tests_passed")
    skipped = outcome.get("security_tests_skipped")
    verified = outcome.get("verified_change")
    if not isinstance(functional, bool) or not isinstance(skipped, bool) or not isinstance(verified, bool):
        raise ManifestError("repository outcome booleans are incomplete: {}".format(task_id))
    if functional is False:
        if security is not None or skipped is not True or outcome["status"] != "fail" or verified is not False:
            raise ManifestError("security oracle must be skipped after functional failure: {}".format(task_id))
    else:
        if not isinstance(security, bool) or skipped is not False:
            raise ManifestError("security oracle result is required after functional success: {}".format(task_id))
        expected_pass = security is True and verified is True
        if (outcome["status"] == "pass") != expected_pass:
            raise ManifestError("repository outcome status is inconsistent: {}".format(task_id))
    process = result.get("process")
    if not isinstance(process, dict) or set(process) != PROCESS_FIELDS:
        raise ManifestError("repository process evidence is incomplete: {}".format(task_id))
    for field in (
        "regression_cycle_count",
        "blind_retry_count",
        "repeated_tool_call_without_new_evidence",
    ):
        value = process[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ManifestError("repository process counter is invalid: {}".format(task_id))
    if not isinstance(process["final_verification"], bool) or not isinstance(process["phase_order_violation"], bool):
        raise ManifestError("repository process flags are invalid: {}".format(task_id))
    invalid_process = (
        process["regression_cycle_count"] > 0
        or process["blind_retry_count"] > 0
        or process["final_verification"] is False
        or process["phase_order_violation"] is True
        or process["repeated_tool_call_without_new_evidence"] > 0
    )
    if outcome["status"] == "pass" and invalid_process:
        raise ManifestError("pass_with_invalid_process: {}".format(task_id))
    usage = result.get("usage")
    if not isinstance(usage, dict) or set(usage) != USAGE_FIELDS:
        raise ManifestError("repository usage is incomplete: {}".format(task_id))
    integer_fields = (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "total_tokens",
        "attempts",
        "tool_calls",
        "timeouts",
    )
    for field in integer_fields:
        value = usage[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ManifestError("repository usage value is invalid: {}.{}".format(task_id, field))
    if usage["attempts"] < 1 or usage["cached_input_tokens"] > usage["input_tokens"]:
        raise ManifestError("repository usage attempt/cache evidence is invalid: {}".format(task_id))
    if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"]:
        raise ManifestError("repository total token evidence is inconsistent: {}".format(task_id))
    for field in ("cost_usd", "elapsed_ms"):
        value = usage[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
            raise ManifestError("repository usage value is invalid: {}.{}".format(task_id, field))
    trace = result.get("trace")
    if not isinstance(trace, dict) or trace.get("raw_trace_stored") is not False or trace.get("redacted") is not True:
        raise ManifestError("repository trace boundary is invalid: {}".format(task_id))
    summary_ref = _require_string(trace, "summary_ref", "repository trace {}".format(task_id))
    summary_path = Path(summary_ref)
    if summary_path.is_absolute() or ".." in summary_path.parts:
        raise ManifestError("repository trace summary_ref must be a safe relative path: {}".format(task_id))
    _require_string(result, "recorded_at", "repository result {}".format(task_id))
    return {
        "passed": outcome["status"] == "pass",
        "invalid_process": invalid_process,
        "total_tokens": float(usage["total_tokens"]),
        "cost_usd": float(usage["cost_usd"]),
        "elapsed_ms": float(usage["elapsed_ms"]),
        "trial": int(result["trial"]),
    }


def _condition_metrics(items: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    successes = sum(1 for item in items if item["passed"])
    success_rate = round(successes / len(items), 6) if items else 0.0
    invalid_rate = round(sum(1 for item in items if item["invalid_process"]) / len(items), 6) if items else 0.0
    total_cost = sum(float(item["cost_usd"]) for item in items)
    return {
        "count": len(items),
        "successes": successes,
        "success_rate": success_rate,
        "invalid_process_rate": invalid_rate,
        "token_distribution": _distribution([float(item["total_tokens"]) for item in items]),
        "cost_distribution": _distribution([float(item["cost_usd"]) for item in items]),
        "elapsed_distribution_ms": _distribution([float(item["elapsed_ms"]) for item in items]),
        "cost_per_success": round(total_cost / successes, 6) if successes else None,
    }


def certify_repository_report(manifest: Manifest, contract_path: Path, report_path: Path) -> Dict[str, Any]:
    contract, tasks_path, tasks = load_repository_contract(manifest, contract_path)
    report = _load_object(report_path.resolve(), "repository evaluation report")
    if report.get("schema") != REPORT_SCHEMA or report.get("status") != "complete":
        raise ManifestError("repository evaluation report is not a complete v1 report")
    if report.get("contract_sha256") != _digest(contract):
        raise ManifestError("repository evaluation contract digest does not match report")
    if report.get("tasks_sha256") != sha256_file(tasks_path):
        raise ManifestError("repository evaluation task digest does not match report")
    expected_header = {
        "task_count": len(tasks),
        "runtimes": contract["runtimes"],
        "conditions": contract["conditions"],
        "trials": contract["trials"],
    }
    if any(report.get(key) != value for key, value in expected_header.items()):
        raise ManifestError("repository evaluation report header does not match contract")
    results = report.get("results")
    if not isinstance(results, list):
        raise ManifestError("repository evaluation results are missing")
    tasks_by_id = {str(task["id"]): task for task in tasks}
    expected = {
        (task_id, runtime, condition, trial)
        for task_id in tasks_by_id
        for runtime in contract["runtimes"]
        for condition in contract["conditions"]
        for trial in range(1, int(contract["trials"]) + 1)
    }
    seen = set()
    validated: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for result in results:
        if not isinstance(result, dict):
            raise ManifestError("repository evaluation result must be an object")
        trial_value = result.get("trial")
        if isinstance(trial_value, bool) or not isinstance(trial_value, int):
            raise ManifestError("repository evaluation result trial must be an integer")
        identity = (
            result.get("task_id"),
            result.get("runtime"),
            result.get("condition"),
            trial_value,
        )
        if identity not in expected or identity in seen:
            raise ManifestError("repository evaluation result identity is invalid or duplicated")
        seen.add(identity)
        task_id, runtime, condition, _ = identity
        value = _validate_result(
            result,
            tasks_by_id[str(task_id)],
            contract["runtime_adapters"][str(runtime)],
            str(condition),
        )
        validated.setdefault((str(runtime), str(condition)), []).append(value)
    if seen != expected:
        raise ManifestError("repository evaluation result matrix is incomplete")
    thresholds = contract["thresholds"]
    runtime_metrics: Dict[str, Any] = {}
    for runtime in contract["runtimes"]:
        baseline_items = validated[(runtime, "baseline")]
        candidate_items = validated[(runtime, "adk")]
        baseline = _condition_metrics(baseline_items)
        candidate = _condition_metrics(candidate_items)
        success_delta = round(candidate["success_rate"] - baseline["success_rate"], 6)
        if candidate["success_rate"] < float(thresholds["candidate_success_rate"]):
            raise ManifestError("candidate success rate is below threshold: {}".format(runtime))
        if success_delta < float(thresholds["minimum_success_delta"]):
            raise ManifestError("candidate success delta is below threshold: {}".format(runtime))
        if candidate["invalid_process_rate"] > float(thresholds["maximum_invalid_process_rate"]):
            raise ManifestError("candidate invalid process rate exceeds threshold: {}".format(runtime))
        if candidate["cost_per_success"] is None or candidate["cost_per_success"] > float(
            thresholds["maximum_cost_per_success_usd"]
        ):
            raise ManifestError("candidate cost per success exceeds threshold: {}".format(runtime))
        baseline_p95 = float(baseline["token_distribution"]["p95"])
        candidate_p95 = float(candidate["token_distribution"]["p95"])
        token_ratio = round(candidate_p95 / baseline_p95, 6) if baseline_p95 else None
        if token_ratio is None or token_ratio > float(thresholds["maximum_token_p95_ratio"]):
            raise ManifestError("candidate token p95 ratio exceeds threshold: {}".format(runtime))
        non_regression_trials = 0
        for trial in range(1, int(contract["trials"]) + 1):
            baseline_trial = [item for item in baseline_items if item["trial"] == trial]
            candidate_trial = [item for item in candidate_items if item["trial"] == trial]
            base_rate = sum(1 for item in baseline_trial if item["passed"]) / len(baseline_trial)
            candidate_rate = sum(1 for item in candidate_trial if item["passed"]) / len(candidate_trial)
            if candidate_rate >= base_rate:
                non_regression_trials += 1
        if non_regression_trials < int(thresholds["required_non_regression_trials"]):
            raise ManifestError("candidate non-regression trial count is below threshold: {}".format(runtime))
        runtime_metrics[runtime] = {
            "baseline": baseline,
            "adk": candidate,
            "success_delta": success_delta,
            "token_p95_ratio": token_ratio,
            "non_regression_trials": non_regression_trials,
        }
    fixture_only = all(
        task["source_kind"] == "clean-room-fixture" and task["execution_status"] == "fixture-only"
        for task in tasks
    )
    if not fixture_only:
        unavailable = [
            runtime
            for runtime, adapter in contract["runtime_adapters"].items()
            if adapter["status"] != "available"
        ]
        if unavailable:
            raise ManifestError(
                "real repository certification requires available version-pinned adapters: {}".format(
                    ",".join(sorted(unavailable))
                )
            )
    certification = {
        "schema": CERTIFICATION_SCHEMA,
        "status": "fixture-pass" if fixture_only else "pass",
        "contract_id": contract["contract_id"],
        "contract_sha256": _digest(contract),
        "tasks_sha256": sha256_file(tasks_path),
        "task_count": len(tasks),
        "result_count": len(results),
        "runtime_metrics": runtime_metrics,
        "external_execution_boundary": "fixture-validation-only" if fixture_only else "report-validation-only",
        "raw_trace_stored": False,
    }
    certification["certification_sha256"] = _digest(certification)
    return certification
