"""Resumable, evidence-validating runtime evaluation campaigns."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .campaign_model import (
    CONTRACT_SCHEMA as CONTRACT_SCHEMA,
)
from .campaign_model import (
    MODEL_ID_RE as MODEL_ID_RE,
)
from .campaign_model import (
    PLAN_SCHEMA,
    RESULT_SCHEMA,
    _attempt_from_report,
    _digest,
    _expected_result_entries,
    _load_json_object,
    _result_path,
    _runtime_entry,
    _utc_now,
    _validate_plan_integrity,
    _write_json_atomic,
    load_campaign_contract,
)
from .campaign_model import (
    TASK_ID_RE as TASK_ID_RE,
)
from .campaign_model import (
    _canonical as _canonical,
)
from .campaign_model import (
    _validated_existing_state as _validated_existing_state_support,
)
from .campaign_model import (
    campaign_markdown as campaign_markdown,
)
from .evaluation import run_runtime, runtime_plan
from .locking import TargetLock
from .model import Manifest, ManifestError, sha256_file

REPORT_SCHEMA = "adk-runtime-eval-campaign-report/v1"


def campaign_plan(manifest: Manifest, contract_path: Path) -> Dict[str, Any]:
    contract, tasks_path, tasks = load_campaign_contract(manifest, contract_path)
    runtime_readiness = [runtime_plan(runtime, "adk", len(tasks)) for runtime in contract["runtimes"]]
    for readiness in runtime_readiness:
        executable = readiness.pop("executable", None)
        readiness["executable_name"] = Path(str(executable)).name if executable else None
        readiness["requested_model"] = contract["runtime_models"][readiness["runtime"]]
    primary_claude_calls = len(tasks) * len(contract["conditions"]) * int(contract["trials"])
    primary_worst_cost = round(primary_claude_calls * float(contract["max_claude_call_usd"]), 2)
    maximum_claude_calls = primary_claude_calls * (int(contract["retry_limit"]) + 1)
    maximum_worst_cost = round(maximum_claude_calls * float(contract["max_claude_call_usd"]), 2)
    failures: List[str] = []
    if maximum_worst_cost > float(contract["max_budget_usd"]):
        failures.append("Claude calls including retries exceed campaign budget")
    for readiness in runtime_readiness:
        if readiness.get("status") != "planned":
            failures.append("{} runtime is not ready: {}".format(readiness["runtime"], readiness.get("reason")))
    plan = {
        "schema": PLAN_SCHEMA,
        "status": "ready" if not failures else "blocked",
        "campaign_id": contract["campaign_id"],
        "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest,
        "contract_sha256": _digest(contract),
        "tasks": tasks_path.relative_to(manifest.root).as_posix(),
        "tasks_sha256": sha256_file(tasks_path),
        "task_count": len(tasks),
        "runtimes": runtime_readiness,
        "conditions": list(contract["conditions"]),
        "trials": contract["trials"],
        "primary_claude_calls": primary_claude_calls,
        "primary_worst_cost_usd": primary_worst_cost,
        "maximum_claude_calls": maximum_claude_calls,
        "maximum_worst_cost_usd": maximum_worst_cost,
        "max_claude_call_usd": contract["max_claude_call_usd"],
        "max_budget_usd": contract["max_budget_usd"],
        "permissions": "read-only/no-tools",
        "failures": failures,
    }
    plan["plan_sha256"] = _digest(plan)
    return plan


def _validated_existing_state(
    state_dir: Path,
    contract: Mapping[str, Any],
    plan: Mapping[str, Any],
    tasks: Sequence[Mapping[str, Any]],
) -> Tuple[set, float]:
    return _validated_existing_state_support(
        state_dir, contract, plan, tasks, _validate_result
    )


def _run_campaign_locked(
    manifest: Manifest,
    contract_path: Path,
    state_dir: Path,
    approved_budget_usd: float,
    resume: bool,
) -> Dict[str, Any]:
    contract, _, tasks = load_campaign_contract(manifest, contract_path)
    current_plan = campaign_plan(manifest, contract_path)
    if approved_budget_usd < float(contract["max_budget_usd"]):
        raise ManifestError("approved budget must cover contract max_budget_usd")
    if approved_budget_usd > 150:
        raise ManifestError("approved budget exceeds the owner-approved $150 ceiling")
    state_dir = state_dir.resolve()
    plan_path = state_dir / "campaign-plan.json"
    if plan_path.exists():
        plan = _load_json_object(plan_path, "campaign plan")
        _validate_plan_integrity(plan)
        for field in ("campaign_id", "manifest_sha256", "contract_sha256", "tasks_sha256"):
            if plan.get(field) != current_plan.get(field):
                raise ManifestError("campaign plan changed; use a new state directory")
        if not resume:
            raise ManifestError("campaign state exists; use --resume")
    else:
        if current_plan["status"] != "ready":
            raise ManifestError("campaign plan is blocked: {}".format("; ".join(current_plan["failures"])))
        if (state_dir / "results").exists():
            raise ManifestError("campaign results exist without a campaign plan")
        plan = current_plan
        _write_json_atomic(plan_path, plan)

    existing_results, spent = _validated_existing_state(state_dir, contract, plan, tasks)
    missing_runtimes = {
        runtime
        for path, runtime, _, _, _ in _expected_result_entries(state_dir, contract, tasks)
        if path not in existing_results
    }
    for runtime in sorted(missing_runtimes):
        frozen_runtime = _runtime_entry(plan, runtime)
        current_runtime = _runtime_entry(current_plan, runtime)
        if current_runtime.get("status") != "planned":
            raise ManifestError(
                "campaign runtime is not ready for remaining work: {}: {}".format(
                    runtime, current_runtime.get("reason")
                )
            )
        if current_runtime.get("runtime_version") != frozen_runtime.get("runtime_version"):
            raise ManifestError("campaign runtime version changed; use a new state directory: {}".format(runtime))
    completed_count = 0
    skipped_count = 0
    for runtime in contract["runtimes"]:
        for condition in contract["conditions"]:
            for trial in range(1, int(contract["trials"]) + 1):
                for task in tasks:
                    task_id = str(task["id"])
                    result_path = _result_path(state_dir, runtime, condition, trial, task_id)
                    if result_path in existing_results:
                        if not resume:
                            raise ManifestError("campaign result exists; use --resume")
                        skipped_count += 1
                        continue
                    attempts: List[Dict[str, Any]] = []
                    for attempt_number in range(1, int(contract["retry_limit"]) + 2):
                        per_call_budget = float(contract["max_claude_call_usd"])
                        if runtime == "claude" and spent + per_call_budget > float(contract["max_budget_usd"]):
                            raise ManifestError("campaign budget cannot cover the next bounded Claude call")
                        report = run_runtime(
                            manifest,
                            [task],
                            runtime,
                            condition,
                            max_claude_call_usd=per_call_budget,
                            model=str(contract["runtime_models"][runtime]),
                        )
                        attempt = _attempt_from_report(report, attempt_number)
                        if attempt.get("runtime_version") != _runtime_entry(plan, runtime).get("runtime_version"):
                            raise ManifestError("campaign runtime version changed during execution: {}".format(runtime))
                        if attempt.get("requested_model") != _runtime_entry(plan, runtime).get("requested_model"):
                            raise ManifestError("campaign runtime model changed during execution: {}".format(runtime))
                        attempts.append(attempt)
                        cost = attempt.get("cost_usd")
                        if runtime == "claude":
                            if not isinstance(cost, (int, float)) or cost < 0:
                                cost = per_call_budget
                                attempt["cost_usd"] = cost
                                attempt["cost_evidence"] = "upper-bound-estimate"
                            else:
                                if float(cost) > per_call_budget:
                                    raise ManifestError("Claude result exceeded the per-call budget")
                                attempt["cost_evidence"] = "runtime-reported"
                            spent = round(spent + float(cost), 6)
                            if spent > float(contract["max_budget_usd"]):
                                raise ManifestError("campaign budget exceeded")
                        else:
                            attempt["cost_evidence"] = "not-applicable"
                        if attempt.get("error") is None:
                            break
                    final = attempts[-1]
                    expected_route = task["category"] if condition == "baseline" else task["expected_skill"]
                    record = {
                        "schema": RESULT_SCHEMA,
                        "campaign_id": contract["campaign_id"],
                        "manifest_version": manifest.version,
                        "manifest_sha256": manifest.digest,
                        "plan_sha256": plan["plan_sha256"],
                        "contract_sha256": plan["contract_sha256"],
                        "tasks_sha256": plan["tasks_sha256"],
                        "runtime": runtime,
                        "runtime_version": _runtime_entry(plan, runtime).get("runtime_version"),
                        "requested_model": _runtime_entry(plan, runtime).get("requested_model"),
                        "condition": condition,
                        "trial": trial,
                        "task_id": task_id,
                        "task_sha256": _digest(task),
                        "expected_route": expected_route,
                        "expected_safe": task["expected_safe"],
                        "recorded_at": _utc_now(),
                        "attempts": attempts,
                        "final": final,
                    }
                    record["record_sha256"] = _digest(record)
                    _write_json_atomic(result_path, record)
                    completed_count += 1
    report = check_campaign(manifest, contract_path, state_dir, certify=True)
    report["executed"] = completed_count
    report["resumed"] = skipped_count
    report["spent_usd"] = spent
    report.pop("report_sha256", None)
    report["report_sha256"] = _digest(report)
    _write_json_atomic(state_dir / "campaign-report.json", report)
    return report


def run_campaign(
    manifest: Manifest,
    contract_path: Path,
    state_dir: Path,
    approved_budget_usd: float,
    resume: bool,
) -> Dict[str, Any]:
    resolved_state = state_dir.resolve()
    with TargetLock(resolved_state, "eval-campaign"):
        return _run_campaign_locked(
            manifest,
            contract_path,
            resolved_state,
            approved_budget_usd,
            resume,
        )


def _nearest_rank(values: Sequence[float], percentile: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * percentile) - 1)
    return round(float(ordered[index]), 3)


def _rate(items: Sequence[Mapping[str, Any]], field: str) -> float:
    return round(sum(1 for item in items if item.get(field) is True) / len(items), 4)


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> Dict[str, float]:
    if total <= 0:
        return {"lower": 0.0, "upper": 0.0}
    proportion = successes / total
    denominator = 1.0 + (z * z / total)
    center = proportion + (z * z / (2.0 * total))
    margin = z * math.sqrt((proportion * (1.0 - proportion) / total) + (z * z / (4.0 * total * total)))
    return {
        "lower": round((center - margin) / denominator, 4),
        "upper": round((center + margin) / denominator, 4),
    }


def _paired_bootstrap_lower(
    baseline: Sequence[Mapping[str, Any]], candidate: Sequence[Mapping[str, Any]], field: str, seed: int
) -> float:
    baseline_map = {(item["trial"], item["task_id"]): item for item in baseline}
    candidate_map = {(item["trial"], item["task_id"]): item for item in candidate}
    if set(baseline_map) != set(candidate_map):
        raise ManifestError("campaign conditions do not cover the same task/trial set")
    differences = [
        (1.0 if candidate_map[key].get(field) is True else 0.0)
        - (1.0 if baseline_map[key].get(field) is True else 0.0)
        for key in sorted(baseline_map)
    ]
    randomizer = random.Random(seed)
    samples: List[float] = []
    for _ in range(2000):
        samples.append(sum(randomizer.choice(differences) for _ in differences) / len(differences))
    samples.sort()
    return round(samples[max(0, math.ceil(len(samples) * 0.025) - 1)], 4)


def _validate_result(
    record: Mapping[str, Any],
    plan: Mapping[str, Any],
    task: Mapping[str, Any],
    runtime: str,
    condition: str,
    trial: int,
    retry_limit: int,
    max_claude_call_usd: float,
) -> Dict[str, Any]:
    if record.get("schema") != RESULT_SCHEMA:
        raise ManifestError("unsupported campaign result schema")
    expected = {
        "campaign_id": plan["campaign_id"],
        "manifest_version": plan["manifest_version"],
        "manifest_sha256": plan["manifest_sha256"],
        "plan_sha256": plan["plan_sha256"],
        "contract_sha256": plan["contract_sha256"],
        "tasks_sha256": plan["tasks_sha256"],
        "runtime": runtime,
        "runtime_version": _runtime_entry(plan, runtime).get("runtime_version"),
        "requested_model": _runtime_entry(plan, runtime).get("requested_model"),
        "condition": condition,
        "trial": trial,
        "task_id": task["id"],
        "task_sha256": _digest(task),
        "expected_route": task["category"] if condition == "baseline" else task["expected_skill"],
        "expected_safe": task["expected_safe"],
    }
    for field, value in expected.items():
        if record.get(field) != value:
            raise ManifestError("campaign result {} does not match plan".format(field))
    stored_digest = record.get("record_sha256")
    without_digest = dict(record)
    without_digest.pop("record_sha256", None)
    if stored_digest != _digest(without_digest):
        raise ManifestError("campaign result digest does not match content")
    attempts = record.get("attempts")
    if not isinstance(attempts, list) or not attempts or len(attempts) > retry_limit + 1:
        raise ManifestError("campaign result attempts are invalid")
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, dict) or attempt.get("attempt") != index:
            raise ManifestError("campaign result attempt order is invalid")
        if attempt.get("runtime_version") != expected["runtime_version"]:
            raise ManifestError("campaign attempt runtime version does not match frozen plan")
        if attempt.get("requested_model") != expected["requested_model"]:
            raise ManifestError("campaign attempt runtime model does not match frozen plan")
        reported_models = attempt.get("reported_models")
        if not isinstance(reported_models, list) or not all(
            isinstance(model, str) and model for model in reported_models
        ):
            raise ManifestError("campaign attempt reported_models are invalid")
        elapsed = attempt.get("elapsed_ms")
        if not isinstance(elapsed, (int, float)) or elapsed < 0:
            raise ManifestError("campaign attempt elapsed_ms is invalid")
        usage = attempt.get("usage")
        if not isinstance(usage, dict):
            raise ManifestError("campaign attempt usage is invalid")
        if any(
            not isinstance(key, str)
            or isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            for key, value in usage.items()
        ):
            raise ManifestError("campaign attempt usage values must be non-negative integers")
        if runtime == "claude":
            cost = attempt.get("cost_usd")
            if not isinstance(cost, (int, float)) or cost < 0 or cost > max_claude_call_usd:
                raise ManifestError("Claude campaign attempt cost is invalid")
            if attempt.get("cost_evidence") not in ("runtime-reported", "upper-bound-estimate"):
                raise ManifestError("Claude campaign attempt cost evidence is invalid")
        elif attempt.get("cost_usd") is not None or attempt.get("cost_evidence") != "not-applicable":
            raise ManifestError("non-Claude campaign attempt has invalid cost evidence")
    final = record.get("final")
    if not isinstance(final, dict) or final != attempts[-1]:
        raise ManifestError("campaign final result does not match last attempt")
    actual_skill = final.get("actual_skill")
    actual_safe = final.get("actual_safe")
    error = final.get("error")
    route_ok = error is None and actual_skill == expected["expected_route"]
    safe_ok = error is None and actual_safe == expected["expected_safe"]
    status = "pass" if route_ok and safe_ok else "fail"
    if final.get("route_ok") is not route_ok or final.get("safe_ok") is not safe_ok or final.get("status") != status:
        raise ManifestError("campaign final summary was not derived from raw fields")
    final_usage = final.get("usage")
    if not isinstance(final_usage, dict) or not isinstance(final_usage.get("total_tokens"), int):
        raise ManifestError("campaign result is missing token usage")
    usage_complete = all(
        isinstance(attempt.get("usage", {}).get("total_tokens"), int) for attempt in attempts
    )
    latency_complete = all(float(attempt.get("elapsed_ms", 0.0)) > 0 for attempt in attempts)
    total_tokens = sum(
        int(attempt["usage"]["total_tokens"])
        for attempt in attempts
        if isinstance(attempt.get("usage", {}).get("total_tokens"), int)
    )
    total_cost_usd = sum(
        float(attempt["cost_usd"])
        for attempt in attempts
        if isinstance(attempt.get("cost_usd"), (int, float))
    )
    return {
        "runtime": runtime,
        "condition": condition,
        "trial": trial,
        "task_id": task["id"],
        "status": status,
        "passed": status == "pass",
        "route_ok": route_ok,
        "safe_ok": safe_ok,
        "elapsed_ms": sum(float(attempt["elapsed_ms"]) for attempt in attempts),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "usage_complete": usage_complete,
        "latency_complete": latency_complete,
        "cost_usd": final.get("cost_usd"),
        "cost_evidence": final.get("cost_evidence"),
        "requested_model": final.get("requested_model"),
        "reported_models": final.get("reported_models"),
        "error": error,
        "attempt_errors": sum(1 for attempt in attempts if attempt.get("error") is not None),
        "attempts": len(attempts),
    }


def check_campaign(
    manifest: Manifest, contract_path: Path, state_dir: Path, certify: bool = False
) -> Dict[str, Any]:
    contract, _, tasks = load_campaign_contract(manifest, contract_path)
    state_dir = state_dir.resolve()
    plan = _load_json_object(state_dir / "campaign-plan.json", "campaign plan")
    _validate_plan_integrity(plan)
    expected_plan = campaign_plan(manifest, contract_path)
    for field in ("campaign_id", "manifest_sha256", "contract_sha256", "tasks_sha256", "task_count", "trials"):
        if plan.get(field) != expected_plan.get(field):
            raise ManifestError("campaign plan {} does not match current contract".format(field))

    validated: List[Dict[str, Any]] = []
    record_digests: List[str] = []
    failures: List[str] = []
    entries = _expected_result_entries(state_dir, contract, tasks)
    expected_paths = {entry[0] for entry in entries}
    results_root = state_dir / "results"
    actual_paths = set(results_root.rglob("*.json")) if results_root.is_dir() else set()
    for path in sorted(actual_paths.difference(expected_paths)):
        failures.append("unexpected result: {}".format(path.relative_to(state_dir)))
    for path, runtime, condition, trial, task in entries:
        if not path.is_file():
            failures.append("missing result: {}".format(path.relative_to(state_dir)))
            continue
        try:
            record = _load_json_object(path, "campaign result")
            validated.append(
                _validate_result(
                    record,
                    plan,
                    task,
                    runtime,
                    condition,
                    trial,
                    int(contract["retry_limit"]),
                    float(contract["max_claude_call_usd"]),
                )
            )
            record_digests.append(str(record["record_sha256"]))
        except ManifestError as exc:
            failures.append("{}: {}".format(path.relative_to(state_dir), exc))

    metrics: Dict[str, Any] = {}
    gates: Dict[str, bool] = {}
    thresholds = contract["thresholds"]
    for runtime_index, runtime in enumerate(contract["runtimes"]):
        runtime_items = [item for item in validated if item["runtime"] == runtime]
        baseline = [item for item in runtime_items if item["condition"] == "baseline"]
        candidate = [item for item in runtime_items if item["condition"] == "adk"]
        runtime_metrics: Dict[str, Any] = {"trials": {}}
        for condition, items in (("baseline", baseline), ("adk", candidate)):
            if not items:
                continue
            successes = sum(1 for item in items if item["status"] == "pass")
            routes = sum(1 for item in items if item["route_ok"])
            safe = sum(1 for item in items if item["safe_ok"])
            runtime_metrics[condition] = {
                "total": len(items),
                "success_rate": round(successes / len(items), 4),
                "route_accuracy": round(routes / len(items), 4),
                "safety_accuracy": round(safe / len(items), 4),
                "success_interval_95": _wilson(successes, len(items)),
                "route_interval_95": _wilson(routes, len(items)),
                "safety_interval_95": _wilson(safe, len(items)),
                "total_tokens": sum(item["total_tokens"] for item in items),
                "cost_usd": round(
                    sum(float(item["total_cost_usd"]) for item in items), 6
                ),
                "runtime_errors": sum(1 for item in items if item["error"] is not None),
                "attempt_errors": sum(item["attempt_errors"] for item in items),
                "retried": sum(1 for item in items if item["attempts"] > 1),
                "resource_evidence_complete": all(
                    item["usage_complete"] and item["latency_complete"] for item in items
                ),
            }
        baseline_keys = {(item["trial"], item["task_id"]) for item in baseline}
        candidate_keys = {(item["trial"], item["task_id"]) for item in candidate}
        expected_runtime_results = len(tasks) * int(contract["trials"])
        if (
            baseline
            and candidate
            and baseline_keys == candidate_keys
            and len(baseline_keys) == expected_runtime_results
        ):
            success_delta = round(runtime_metrics["adk"]["success_rate"] - runtime_metrics["baseline"]["success_rate"], 4)
            route_delta = round(runtime_metrics["adk"]["route_accuracy"] - runtime_metrics["baseline"]["route_accuracy"], 4)
            runtime_metrics["comparison"] = {
                "success_delta": success_delta,
                "route_delta": route_delta,
                "success_delta_lower_95": _paired_bootstrap_lower(
                    baseline, candidate, "passed", 3100 + runtime_index
                ),
                "route_delta_lower_95": _paired_bootstrap_lower(
                    baseline, candidate, "route_ok", 4100 + runtime_index
                ),
            }
        latency_passes = 0
        usage_passes = 0
        for trial in range(1, int(contract["trials"]) + 1):
            trial_base = [item for item in baseline if item["trial"] == trial]
            trial_adk = [item for item in candidate if item["trial"] == trial]
            trial_complete = (
                len(trial_base) == len(tasks)
                and len(trial_adk) == len(tasks)
                and all(item["usage_complete"] and item["latency_complete"] for item in trial_base + trial_adk)
            )
            base_p95 = (
                _nearest_rank([item["elapsed_ms"] for item in trial_base if item["elapsed_ms"] > 0], 0.95)
                if trial_complete
                else None
            )
            adk_p95 = (
                _nearest_rank([item["elapsed_ms"] for item in trial_adk if item["elapsed_ms"] > 0], 0.95)
                if trial_complete
                else None
            )
            base_tokens = sum(item["total_tokens"] for item in trial_base)
            adk_tokens = sum(item["total_tokens"] for item in trial_adk)
            latency_ratio = round(adk_p95 / base_p95, 4) if base_p95 and adk_p95 else None
            usage_ratio = round(adk_tokens / base_tokens, 4) if base_tokens else None
            latency_ok = latency_ratio is not None and latency_ratio <= float(thresholds["latency_ratio_max"])
            usage_ok = usage_ratio is not None and usage_ratio <= float(thresholds["usage_ratio_max"])
            latency_passes += int(latency_ok)
            usage_passes += int(usage_ok)
            runtime_metrics["trials"][str(trial)] = {
                "baseline_p95_ms": base_p95,
                "candidate_p95_ms": adk_p95,
                "latency_ratio": latency_ratio,
                "latency_ok": latency_ok,
                "baseline_tokens": base_tokens,
                "candidate_tokens": adk_tokens,
                "usage_ratio": usage_ratio,
                "usage_ok": usage_ok,
            }
        comparison = runtime_metrics.get("comparison", {})
        runtime_gates = {
            "candidate_success": runtime_metrics.get("adk", {}).get("success_rate", 0)
            >= float(thresholds["candidate_success_rate"]),
            "candidate_route": runtime_metrics.get("adk", {}).get("route_accuracy", 0)
            >= float(thresholds["candidate_route_accuracy"]),
            "candidate_safety": runtime_metrics.get("adk", {}).get("safety_accuracy", 0)
            >= float(thresholds["candidate_safety_accuracy"]),
            "success_gain": comparison.get("success_delta", -1) >= float(thresholds["minimum_success_delta"]),
            "route_gain": comparison.get("route_delta", -1) >= float(thresholds["minimum_success_delta"]),
            "success_confidence": comparison.get("success_delta_lower_95", -1) >= 0,
            "route_confidence": comparison.get("route_delta_lower_95", -1) >= 0,
            "runtime_errors": runtime_metrics.get("adk", {}).get("runtime_errors", 1) == 0,
            "resource_evidence": runtime_metrics.get("adk", {}).get("resource_evidence_complete", False)
            and runtime_metrics.get("baseline", {}).get("resource_evidence_complete", False),
            "latency_non_regression": latency_passes >= int(thresholds["required_non_regression_trials"]),
            "usage_non_regression": usage_passes >= int(thresholds["required_non_regression_trials"]),
        }
        runtime_metrics["gates"] = runtime_gates
        metrics[runtime] = runtime_metrics
        for name, value in runtime_gates.items():
            gates["{}.{}".format(runtime, name)] = value

    complete = len(validated) == len(tasks) * len(contract["runtimes"]) * len(contract["conditions"]) * int(contract["trials"])
    gates["evidence_complete"] = complete and not failures
    status = "pass" if certify and gates and all(gates.values()) else "complete" if complete and not failures else "fail"
    if certify and not all(gates.values()):
        status = "fail"
    report = {
        "schema": REPORT_SCHEMA,
        "status": status,
        "campaign_id": contract["campaign_id"],
        "manifest_version": plan["manifest_version"],
        "manifest_sha256": plan["manifest_sha256"],
        "contract_sha256": plan["contract_sha256"],
        "tasks_sha256": plan["tasks_sha256"],
        "task_count": len(tasks),
        "trials": int(contract["trials"]),
        "runtime_provenance": [
            {
                "runtime": runtime,
                "runtime_version": _runtime_entry(plan, runtime).get("runtime_version"),
                "requested_model": _runtime_entry(plan, runtime).get("requested_model"),
            }
            for runtime in contract["runtimes"]
        ],
        "certified": certify and status == "pass",
        "expected_results": len(tasks) * len(contract["runtimes"]) * len(contract["conditions"]) * int(contract["trials"]),
        "validated_results": len(validated),
        "total_cost_usd": round(sum(float(item["total_cost_usd"]) for item in validated), 6),
        "max_budget_usd": float(contract["max_budget_usd"]),
        "evidence_sha256": _digest(sorted(record_digests)),
        "thresholds": thresholds,
        "metrics": metrics,
        "gates": gates,
        "failures": failures,
    }
    report["report_sha256"] = _digest(report)
    return report
