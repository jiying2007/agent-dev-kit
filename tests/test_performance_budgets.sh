#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-performance-budgets.sh"
"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json >"$TMP_DIR/perf-budget.json"
rg -q '"status":"pass"' "$TMP_DIR/perf-budget.json" || {
  echo "[FAIL] performance budget summary did not pass" >&2
  cat "$TMP_DIR/perf-budget.json" >&2
  exit 1
}

cat >"$TMP_DIR/quick-pass.json" <<'JSON'
{
  "schema_version": 1,
  "mode": "quick",
  "status": "pass",
  "total": 1,
  "pass": 1,
  "fail": 0,
  "elapsed_ms": 1000,
  "slow_threshold_sec": 10,
  "tests": [],
  "slow_tests": []
}
JSON
"$ROOT_DIR/scripts/check-performance-budgets.sh" --strict --timing-json "$TMP_DIR/quick-pass.json"

cat >"$TMP_DIR/quick-fail.json" <<'JSON'
{
  "schema_version": 1,
  "mode": "quick",
  "status": "pass",
  "total": 1,
  "pass": 1,
  "fail": 0,
  "elapsed_ms": 999999,
  "slow_threshold_sec": 10,
  "tests": [],
  "slow_tests": []
}
JSON
if "$ROOT_DIR/scripts/check-performance-budgets.sh" --strict --timing-json "$TMP_DIR/quick-fail.json" >"$TMP_DIR/fail.out" 2>"$TMP_DIR/fail.err"; then
  echo "[FAIL] strict performance budget should fail on exceeded timing" >&2
  exit 1
fi
rg -q 'timing budget exceeded' "$TMP_DIR/fail.err" || {
  echo "[FAIL] strict budget failure did not explain exceeded timing" >&2
  cat "$TMP_DIR/fail.err" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/quick-fail.json" >"$TMP_DIR/report-only.json"
python3 - "$TMP_DIR/report-only.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
assert report["status"] == "warn", report
assert report["strict"] == 0 and report["failures"] == 0, report
assert report["elapsed_ms"] == 999999 and report["budget_ms"] > 0, report
PY

python3 - "$TMP_DIR/quick-pass.json" "$TMP_DIR/full-pass.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
report.update(mode="full", elapsed_ms=331902)
with open(sys.argv[2], "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
PY
"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/full-pass.json" >"$TMP_DIR/full-budget.json"
python3 - "$TMP_DIR/full-budget.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
assert report["status"] == "pass" and report["mode"] == "full", report
assert report["elapsed_ms"] == 331902 and report["budget_ms"] == 600000, report
assert report["strict"] == 0, report
PY

if "$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/missing.json" >"$TMP_DIR/missing-budget.json"; then
  echo "[FAIL] missing timing must not be reported as a successful observation" >&2
  exit 1
fi

echo "[PASS] performance budgets"
