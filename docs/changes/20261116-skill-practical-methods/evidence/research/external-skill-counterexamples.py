#!/usr/bin/env python3
"""Local, deterministic demonstrations of three instruction gaps.

This is original research code, not imported Skill code or an ADK regression.
The memory case is an exact logical live-payload model, not a profiler result.
The timeout cases use integer fake time and make no network calls.
"""

import json
import subprocess
import sys


def run_case_order(order):
    state = {"mode": "default"}
    outcomes = []
    for name in order:
        if name == "polluter":
            state["mode"] = "legacy"
            outcomes.append({"case": name, "outcome": "passed"})
        elif name == "victim":
            outcomes.append({
                "case": name,
                "outcome": "passed" if state["mode"] == "default" else "failed",
                "observed_mode": state["mode"],
            })
        else:
            raise ValueError(name)
    return outcomes


def memory_model(retain_until_end):
    live = peak = total = 0
    block_bytes = 1024 * 1024
    for _ in range(64):
        live += block_bytes
        total += block_bytes
        peak = max(peak, live)
        if not retain_until_end:
            live -= block_bytes
    if retain_until_end:
        live = 0
    return {
        "allocation_count": 64,
        "free_count": 64,
        "total_payload_bytes_allocated": total,
        "final_live_payload_bytes": live,
        "peak_live_payload_bytes": peak,
    }


def stage_model(propagate_deadline):
    deadline_ms = 2000
    elapsed_ms = 0
    outcomes = []
    for stage, work_ms in (("dns", 600), ("tcp", 700), ("tls", 600), ("application", 700)):
        local_limit_ms = 1000
        permitted_ms = min(local_limit_ms, deadline_ms - elapsed_ms) if propagate_deadline else local_limit_ms
        if permitted_ms <= 0:
            outcomes.append({"stage": stage, "outcome": "not-started", "reason": "deadline"})
            break
        consumed_ms = min(work_ms, permitted_ms)
        elapsed_ms += consumed_ms
        timed_out = consumed_ms < work_ms
        outcomes.append({"stage": stage, "spent_ms": consumed_ms, "outcome": "timeout" if timed_out else "completed"})
        if timed_out:
            break
    return {"end_to_end_limit_ms": deadline_ms, "elapsed_ms": elapsed_ms, "stages": outcomes}


def retry_model(propagate_deadline):
    deadline_ms = 2000
    elapsed_ms = 0
    attempts = []
    for attempt in range(1, 4):
        if attempt > 1:
            remaining_ms = deadline_ms - elapsed_ms
            if propagate_deadline and remaining_ms <= 0:
                break
            elapsed_ms += min(500, remaining_ms) if propagate_deadline else 500
        remaining_ms = deadline_ms - elapsed_ms
        if propagate_deadline and remaining_ms <= 0:
            break
        consumed_ms = min(800, remaining_ms) if propagate_deadline else 800
        elapsed_ms += consumed_ms
        attempts.append({"attempt": attempt, "spent_ms": consumed_ms, "outcome": "transient-failure" if consumed_ms == 800 else "deadline-timeout"})
    return {"end_to_end_limit_ms": deadline_ms, "elapsed_ms": elapsed_ms, "attempts": attempts}


def nested_retry_calls(depth, owner_only):
    calls = 0

    def invoke(level):
        nonlocal calls
        count = 3 if (not owner_only or level == 0) else 1
        for _ in range(count):
            if level == depth - 1:
                calls += 1
            else:
                invoke(level + 1)

    invoke(0)
    return calls


if len(sys.argv) == 2 and sys.argv[1] == "isolated-victim":
    print(json.dumps(run_case_order(["victim"])))
    raise SystemExit(0)

isolated = []
for _ in range(8):
    result = subprocess.run(
        [sys.executable, __file__, "isolated-victim"],
        check=True, capture_output=True, text=True, timeout=5,
    )
    isolated.append(json.loads(result.stdout)[0]["outcome"])

evidence = {
    "scope": "synthetic method counterexamples; not ADK agent outcome evaluation",
    "memory": {
        "scope": "exact logical live-payload model; no Memcheck/Massif execution and no RSS measurement",
        "allocate_then_free_each": memory_model(False),
        "retain_all_then_free": memory_model(True),
    },
    "order_dependence": {
        "isolated_victim_fresh_process_outcomes": isolated,
        "same_process_polluter_then_victim": run_case_order(["polluter", "victim"]),
        "same_process_victim_then_polluter": run_case_order(["victim", "polluter"]),
    },
    "protocol": {
        "scope": "integer fake time; 1000 ms local stage limits and 2000 ms operation limit",
        "independent_stage_limits": stage_model(False),
        "propagated_deadline": stage_model(True),
        "count_limited_retries_only": retry_model(False),
        "deadline_bounded_retries": retry_model(True),
        "nested_retry_leaf_calls_3_layers_3_attempts": nested_retry_calls(3, False),
        "one_retry_owner_leaf_calls_3_layers_3_attempts": nested_retry_calls(3, True),
    },
}
checks = {
    "memory_totals_equal_but_peaks_differ": evidence["memory"]["allocate_then_free_each"]["total_payload_bytes_allocated"] == evidence["memory"]["retain_all_then_free"]["total_payload_bytes_allocated"] and evidence["memory"]["allocate_then_free_each"]["peak_live_payload_bytes"] != evidence["memory"]["retain_all_then_free"]["peak_live_payload_bytes"],
    "fresh_process_repetition_misses_order_pollution": all(x == "passed" for x in isolated) and evidence["order_dependence"]["same_process_polluter_then_victim"][-1]["outcome"] == "failed",
    "reverse_order_does_not_reproduce": all(x["outcome"] == "passed" for x in evidence["order_dependence"]["same_process_victim_then_polluter"]),
    "per_stage_bounds_do_not_imply_overall_bound": evidence["protocol"]["independent_stage_limits"]["elapsed_ms"] == 2600 and evidence["protocol"]["propagated_deadline"]["elapsed_ms"] == 2000,
    "attempt_count_does_not_imply_overall_bound": evidence["protocol"]["count_limited_retries_only"]["elapsed_ms"] == 3400 and evidence["protocol"]["deadline_bounded_retries"]["elapsed_ms"] == 2000,
    "nested_attempts_multiply": evidence["protocol"]["nested_retry_leaf_calls_3_layers_3_attempts"] == 27 and evidence["protocol"]["one_retry_owner_leaf_calls_3_layers_3_attempts"] == 3,
}
evidence["checks"] = checks
print(json.dumps(evidence, ensure_ascii=False, indent=2))
if not all(checks.values()):
    raise SystemExit(1)
