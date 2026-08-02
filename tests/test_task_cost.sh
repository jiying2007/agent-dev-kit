#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

run_case() {
  local name="$1"
  shift
  ADK_PYTHON_BIN=python3 bash "${ROOT}/scripts/devkit.sh" task-cost \
    --task "private-task-${name}" --summary-json "$@" >"${TMP_DIR}/${name}.json"
}

run_case micro --changed-files 1
run_case standard --changed-files 2 --project-facts
run_case complex --changed-files 5 --shared-contract
run_case high-risk --task-type release --external-write

python3 - "${TMP_DIR}" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
expected = {
    "micro": ("micro", 0, "skip", "L0"),
    "standard": ("standard", 1, "conditional", "L1"),
    "complex": ("complex", 1, "required", "L1"),
    "high-risk": ("high-risk", 1, "required", "L2"),
}
for name, values in expected.items():
    payload = json.loads((root / (name + ".json")).read_text(encoding="utf-8"))
    budget = payload["execution_budget"]
    assert payload["task_cost"] == values[0]
    assert budget["primary_skill_budget"] == values[1]
    assert budget["hub_preflight"] == values[2]
    assert budget["read_tier"] == values[3]
    assert payload["source_text_stored"] is False
    assert len(payload["task_sha256"]) == 64
    assert ("private-task-" + name) not in json.dumps(payload, ensure_ascii=False)
assert json.loads((root / "high-risk.json").read_text())["execution_budget"]["raw_required"] is True
PY

if ADK_PYTHON_BIN=python3 bash "${ROOT}/scripts/devkit.sh" task-cost \
  --task "micro-overbudget" --changed-files 1 --skill one >"${TMP_DIR}/overbudget.out" 2>&1; then
  echo "[FAIL] micro task unexpectedly accepted a skill" >&2
  exit 1
fi

echo "[PASS] task-cost receipts enforce deterministic execution budgets"
