"""Read-only independent boundary probes; no runtime/model calls."""
from __future__ import annotations

import copy
import json
import math
from datetime import UTC, datetime

from agent_dev_kit.campaign_analysis import _validate_result
from agent_dev_kit.campaign_model import RESULT_SCHEMA, _digest


def inputs():
    task = {"id": "independent-probe", "category": "routing", "expected_skill": "adk-runtime-router", "expected_safe": True}
    plan = {
        "campaign_id": "independent-probe", "manifest_version": "11.3.14",
        "manifest_sha256": "1" * 64, "plan_sha256": "2" * 64,
        "contract_sha256": "3" * 64, "tasks_sha256": "4" * 64,
        "runtimes": [{"runtime": "claude", "runtime_version": "fixture", "requested_model": "fixture"}],
    }
    attempt = {
        "attempt": 1, "runtime_version": "fixture", "requested_model": "fixture", "reported_models": ["fixture"],
        "actual_safe": True, "actual_skill": "adk-runtime-router", "elapsed_ms": 1.0,
        "usage": {"total_tokens": 1}, "cost_usd": 0.001, "cost_evidence": "runtime-reported",
        "error": None, "route_ok": True, "safe_ok": True, "status": "pass",
    }
    record = {
        **{key: value for key, value in plan.items() if key != "runtimes"},
        "schema": RESULT_SCHEMA, "runtime": "claude", "runtime_version": "fixture", "requested_model": "fixture",
        "condition": "adk", "trial": 1, "task_id": task["id"], "task_sha256": _digest(task),
        "expected_route": task["expected_skill"], "expected_safe": True,
        "attempts": [attempt], "final": copy.deepcopy(attempt),
    }
    return record, plan, task


def probe(label, value, repeated=False):
    record, plan, task = inputs()
    record["attempts"][0]["elapsed_ms"] = value
    if repeated:
        another = copy.deepcopy(record["attempts"][0])
        another["attempt"] = 2
        record["attempts"].append(another)
    record["final"] = copy.deepcopy(record["attempts"][-1])
    record["record_sha256"] = _digest(record)
    try:
        result = _validate_result(record, plan, task, "claude", "adk", 1, int(repeated), 0.01)
    except Exception as exc:
        return {"case": label, "outcome": "exception", "type": type(exc).__name__, "message": str(exc)}
    return {"case": label, "outcome": "accepted", "elapsed_ms_repr": repr(result["elapsed_ms"]),
            "elapsed_ms_finite": math.isfinite(result["elapsed_ms"]),
            "latency_complete": result["latency_complete"], "passed": result["passed"]}


if __name__ == "__main__":
    results = [
        probe("ordinary-finite", 1),
        probe("boolean", True),
        probe("nan", float("nan")),
        probe("infinity", float("inf")),
        probe("large-json-integer", 10 ** 400),
        probe("finite-attempts-overflow-total", 1e308, repeated=True),
    ]
    print(json.dumps({"observed_at": datetime.now(UTC).isoformat(), "probes": results}, indent=2))
