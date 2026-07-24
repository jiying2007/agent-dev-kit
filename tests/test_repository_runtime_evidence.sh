#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CONTRACT="$ROOT_DIR/manifests/repository_runtime_eval_contract.json"
REPORT="$TMP_DIR/repository-report.json"

"$ROOT_DIR/scripts/devkit.sh" eval repository plan \
  --contract "$CONTRACT" --summary-json >"$TMP_DIR/plan.json"

python3 - "$TMP_DIR/plan.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema"] == "adk-repository-runtime-eval-plan/v1", value
assert value["status"] == "ready", value
assert value["execution_enabled"] is False, value
assert value["task_count"] == 5, value
assert value["adapter_status"] == "contract-only", value
PY

python3 - "$ROOT_DIR" "$CONTRACT" "$REPORT" <<'PY'
import hashlib
import itertools
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
contract_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])
contract = json.loads(contract_path.read_text(encoding="utf-8"))
tasks_path = root / contract["tasks"]
tasks = [json.loads(line) for line in tasks_path.read_text(encoding="utf-8").splitlines() if line]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


results = []
for task, runtime, condition, trial in itertools.product(
    tasks, contract["runtimes"], contract["conditions"], range(1, contract["trials"] + 1)
):
    baseline_failure = condition == "baseline" and task["id"] == tasks[0]["id"]
    results.append({
        "task_id": task["id"],
        "runtime": runtime,
        "condition": condition,
        "trial": trial,
        "repository_revision": task["repository_revision"],
        "container_digest": task["container_digest"],
        "adapter_id": contract["runtime_adapters"][runtime]["adapter_id"],
        "isolation": {
            "verified": True,
            "strategy": contract["runtime_adapters"][runtime][
                "baseline_isolation" if condition == "baseline" else "adk_isolation"
            ],
            "disabled_surfaces": (
                ["project-instructions", "skills", "hooks", "mcp", "plugins"]
                if condition == "baseline"
                else ["hooks", "mcp", "plugins"]
            ),
            "enabled_surfaces": [] if condition == "baseline" else ["project-instructions", "skills"],
        },
        "outcome": {
            "status": "fail" if baseline_failure else "pass",
            "functional_tests_passed": not baseline_failure,
            "security_tests_passed": None if baseline_failure else True,
            "security_tests_skipped": baseline_failure,
            "verified_change": not baseline_failure,
        },
        "process": {
            "regression_cycle_count": 0,
            "blind_retry_count": 0,
            "final_verification": True,
            "phase_order_violation": False,
            "repeated_tool_call_without_new_evidence": 0,
        },
        "usage": {
            "input_tokens": 100,
            "cached_input_tokens": 10,
            "output_tokens": 50,
            "total_tokens": 150,
            "cost_usd": 0.01,
            "elapsed_ms": 1000,
            "attempts": 1,
            "tool_calls": 4,
            "timeouts": 0,
        },
        "trace": {
            "summary_ref": "evidence/{}/{}/{}/trial-{}.json".format(task["id"], runtime, condition, trial),
            "raw_trace_stored": False,
            "redacted": True,
        },
        "recorded_at": "2026-07-23T00:00:00Z",
    })

report = {
    "schema": "adk-repository-runtime-eval-report/v1",
    "status": "complete",
    "contract_sha256": hashlib.sha256(canonical(contract)).hexdigest(),
    "tasks_sha256": hashlib.sha256(tasks_path.read_bytes()).hexdigest(),
    "task_count": len(tasks),
    "runtimes": contract["runtimes"],
    "conditions": contract["conditions"],
    "trials": contract["trials"],
    "results": results,
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

"$ROOT_DIR/scripts/devkit.sh" eval repository certify \
  --contract "$CONTRACT" --report "$REPORT" --summary-json >"$TMP_DIR/certified.json"

python3 - "$TMP_DIR/certified.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["status"] == "fixture-pass", value
assert value["external_execution_boundary"] == "fixture-validation-only", value
assert value["result_count"] == 60, value
for runtime, metrics in value["runtime_metrics"].items():
    assert metrics["adk"]["success_rate"] == 1.0, metrics
    assert metrics["success_delta"] == 0.2, metrics
    assert metrics["adk"]["invalid_process_rate"] == 0.0, metrics
    assert metrics["adk"]["token_distribution"]["p95"] == 150.0, metrics
    assert metrics["adk"]["cost_per_success"] == 0.01, metrics
PY

expect_failure() {
  local name="$1"
  local expected="$2"
  local source="$TMP_DIR/${name}.json"
  if "$ROOT_DIR/scripts/devkit.sh" eval repository certify \
    --contract "$CONTRACT" --report "$source" --summary-json >"$TMP_DIR/${name}.out" 2>"$TMP_DIR/${name}.err"; then
    echo "[FAIL] repository evidence negative case unexpectedly passed: $name" >&2
    exit 1
  fi
  rg -q "$expected" "$TMP_DIR/${name}.err"
}

python3 - "$REPORT" "$TMP_DIR" <<'PY'
import copy
import json
import sys
from pathlib import Path

source = json.load(open(sys.argv[1], encoding="utf-8"))
out = Path(sys.argv[2])


def write(name, mutate):
    value = copy.deepcopy(source)
    mutate(value)
    (out / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")


write("missing-isolation", lambda value: value["results"][30]["isolation"].update(verified=False))
write("lucky-pass", lambda value: value["results"][30]["process"].update(blind_retry_count=2))
write("missing-cost", lambda value: value["results"][30]["usage"].pop("cost_usd"))
write("digest-drift", lambda value: value["results"][30].update(repository_revision="sha256:" + "f" * 64))
write("matrix-incomplete", lambda value: value["results"].pop())
write("boolean-trial", lambda value: value["results"][0].update(trial=True))


def security_failure(value):
    result = next(item for item in value["results"] if item["condition"] == "adk")
    result["outcome"].update(status="fail", functional_tests_passed=True, security_tests_passed=False, security_tests_skipped=False, verified_change=False)


write("security-failure", security_failure)
PY

expect_failure missing-isolation "customization isolation is not verified"
expect_failure lucky-pass "pass_with_invalid_process"
expect_failure missing-cost "usage is incomplete"
expect_failure digest-drift "repository revision does not match"
expect_failure matrix-incomplete "result matrix is incomplete"
expect_failure boolean-trial "result trial must be an integer"
expect_failure security-failure "candidate success rate is below threshold"

echo "[PASS] repository runtime evidence contract"
