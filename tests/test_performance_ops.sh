#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
ROOT_TMP_FILE="$ROOT_DIR/adk-ops-report-only-test.tmp"
trap 'rm -rf "$TMP_DIR"; rm -f "$ROOT_TMP_FILE" "$ROOT_DIR/.benchmark"' EXIT

assert_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! rg -q -- "$pattern" "$file"; then
    echo "[FAIL] ${label}" >&2
    sed -n '1,80p' "$file" >&2 || true
    exit 1
  fi
}

"$ROOT_DIR/scripts/performance.sh" analyze >"$TMP_DIR/analyze.txt"
assert_contains "$TMP_DIR/analyze.txt" '性能分析报告' "performance analyze missing report title"
assert_contains "$TMP_DIR/analyze.txt" '最大文件' "performance analyze missing largest files section"

"$ROOT_DIR/scripts/performance.sh" analyze --summary-json >"$TMP_DIR/analyze.json"
assert_contains "$TMP_DIR/analyze.json" '"schema_version":1' "performance analyze json missing schema"
assert_contains "$TMP_DIR/analyze.json" '"largest_files":' "performance analyze json missing largest_files"
assert_contains "$TMP_DIR/analyze.json" '"largest_dirs":' "performance analyze json missing largest_dirs"

"$ROOT_DIR/scripts/performance.sh" report >"$TMP_DIR/report.md"
assert_contains "$TMP_DIR/report.md" '^# 性能报告' "performance report should print markdown to stdout"
if [[ -d "$ROOT_DIR/.monitoring" ]] && find "$ROOT_DIR/.monitoring" -name 'performance-report-*.md' -newer "$TMP_DIR/report.md" -print -quit | rg -q .; then
  echo "[FAIL] performance report wrote .monitoring without --out" >&2
  exit 1
fi

"$ROOT_DIR/scripts/performance.sh" report --out "$TMP_DIR/performance-report.md" >/dev/null
[[ -f "$TMP_DIR/performance-report.md" ]] || {
  echo "[FAIL] performance report --out did not write target" >&2
  exit 1
}

rm -f "$ROOT_DIR/.benchmark"
"$ROOT_DIR/scripts/performance.sh" benchmark --summary-json >"$TMP_DIR/benchmark.json" 2>"$TMP_DIR/benchmark.err"
assert_contains "$TMP_DIR/benchmark.json" '"io_status":"skipped"' "benchmark should skip io by default"
assert_contains "$TMP_DIR/benchmark.json" '"quality_status":"skipped"' "benchmark should skip quality gate by default"
[[ ! -e "$ROOT_DIR/.benchmark" ]] || {
  echo "[FAIL] benchmark created root .benchmark without --include-io" >&2
  exit 1
}

printf 'keep\n' >"$ROOT_TMP_FILE"
"$ROOT_DIR/scripts/auto-ops.sh" cleanup >"$TMP_DIR/cleanup.txt"
[[ -f "$ROOT_TMP_FILE" ]] || {
  echo "[FAIL] ops cleanup without --apply deleted a file" >&2
  exit 1
}
assert_contains "$TMP_DIR/cleanup.txt" 'report-only' "ops cleanup should be report-only by default"

if "$ROOT_DIR/scripts/auto-ops.sh" cleanup --force >"$TMP_DIR/force.out" 2>"$TMP_DIR/force.err"; then
  echo "[FAIL] ops --force without --apply should fail" >&2
  exit 1
fi
assert_contains "$TMP_DIR/force.err" '--force 必须与 --apply' "ops force failure missing reason"

"$ROOT_DIR/scripts/auto-ops.sh" weekly --summary-json >"$TMP_DIR/weekly.json"
assert_contains "$TMP_DIR/weekly.json" '"status":"pass"' "ops weekly json should pass"
assert_contains "$TMP_DIR/weekly.json" '"apply":0' "ops weekly json should default to apply=0"

echo "[PASS] performance and ops tests passed"
