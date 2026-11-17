"""Statistical analysis and result validation for runtime evaluation campaigns."""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Mapping, Optional, Sequence

from .campaign_model import RESULT_SCHEMA, _digest, _runtime_entry
from .model import ManifestError


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


def _finite_nonnegative(value: Any, label: str) -> float:
    if type(value) not in (int, float):
        raise ManifestError(f"{label} is invalid")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ManifestError(f"{label} is invalid") from exc
    if number < 0 or not math.isfinite(number):
        raise ManifestError(f"{label} is invalid")
    return number


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
    elapsed_values: List[float] = []
    cost_values: List[float] = []
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
        elapsed_values.append(_finite_nonnegative(attempt.get("elapsed_ms"), "campaign attempt elapsed_ms"))
        actual_safe = attempt.get("actual_safe")
        if type(actual_safe) is not bool and not (actual_safe is None and attempt.get("error") is not None):
            raise ManifestError("campaign attempt actual_safe must be boolean unless the runtime failed")
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
            cost = _finite_nonnegative(attempt.get("cost_usd"), "Claude campaign attempt cost")
            if cost > max_claude_call_usd:
                raise ManifestError("Claude campaign attempt cost is invalid")
            cost_values.append(cost)
            if attempt.get("cost_evidence") not in ("runtime-reported", "upper-bound-estimate"):
                raise ManifestError("Claude campaign attempt cost evidence is invalid")
        elif attempt.get("cost_usd") is not None or attempt.get("cost_evidence") != "not-applicable":
            raise ManifestError("non-Claude campaign attempt has invalid cost evidence")
    final = record.get("final")
    if not isinstance(final, dict) or _digest(final) != _digest(attempts[-1]):
        raise ManifestError("campaign final result does not match last attempt")
    actual_skill = final.get("actual_skill")
    actual_safe = final.get("actual_safe")
    error = final.get("error")
    route_ok = error is None and actual_skill == expected["expected_route"]
    safe_ok = error is None and actual_safe is expected["expected_safe"]
    status = "pass" if route_ok and safe_ok else "fail"
    if final.get("route_ok") is not route_ok or final.get("safe_ok") is not safe_ok or final.get("status") != status:
        raise ManifestError("campaign final summary was not derived from raw fields")
    final_usage = final.get("usage")
    if not isinstance(final_usage, dict) or not isinstance(final_usage.get("total_tokens"), int):
        raise ManifestError("campaign result is missing token usage")
    usage_complete = all(
        isinstance(attempt.get("usage", {}).get("total_tokens"), int) for attempt in attempts
    )
    latency_complete = all(elapsed > 0 for elapsed in elapsed_values)
    total_tokens = sum(
        int(attempt["usage"]["total_tokens"])
        for attempt in attempts
        if isinstance(attempt.get("usage", {}).get("total_tokens"), int)
    )
    total_elapsed = _finite_nonnegative(sum(elapsed_values), "campaign result elapsed_ms total")
    total_cost_usd = _finite_nonnegative(sum(cost_values), "campaign result cost total")
    return {
        "runtime": runtime,
        "condition": condition,
        "trial": trial,
        "task_id": task["id"],
        "status": status,
        "passed": status == "pass",
        "route_ok": route_ok,
        "safe_ok": safe_ok,
        "elapsed_ms": total_elapsed,
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
