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

echo "[PASS] performance budgets"
