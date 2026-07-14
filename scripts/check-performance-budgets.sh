#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT_DIR/manifests/adk_performance_budgets.json"
SUMMARY_JSON=0
STRICT=0
TIMING_JSON=""

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-performance-budgets.sh [--summary-json] [--strict] [--timing-json <path>]

Checks ADK performance budgets:
  - budget contract JSON is valid
  - referenced scripts/tests exist
  - optional timing JSON is valid and within the configured mode budget

Default mode is report-only. Use --strict with --timing-json to fail on budget drift.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    --strict)
      STRICT=1
      shift
      ;;
    --timing-json)
      TIMING_JSON="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

failures=()
warnings=()
checked=0
mode="none"
elapsed_ms=0
budget_ms=0

record_failure() {
  failures+=("$1")
}

record_warning() {
  warnings+=("$1")
}

require_file() {
  local rel="$1"
  checked=$((checked + 1))
  [[ -f "$ROOT_DIR/$rel" ]] || record_failure "missing file: $rel"
}

extract_values() {
  local key="$1"
  rg -o "\"${key}\": \"[^\"]+\"" "$MANIFEST" | sed "s/.*\"${key}\": \"//; s/\"$//" | sort -u
}

budget_for_mode() {
  local wanted="$1"
  awk -v wanted="$wanted" '
    /"mode":/ {
      mode=$0
      sub(/.*"mode": "/, "", mode)
      sub(/".*/, "", mode)
    }
    /"max_elapsed_ms":/ {
      value=$0
      sub(/.*"max_elapsed_ms": /, "", value)
      sub(/,.*/, "", value)
      if (mode == wanted) {
        print value
        exit
      }
    }
  ' "$MANIFEST"
}

require_file "manifests/adk_performance_budgets.json"
if [[ -f "$MANIFEST" ]]; then
  checked=$((checked + 1))
  if ! python3 -m json.tool "$MANIFEST" >/dev/null; then
    record_failure "invalid json: manifests/adk_performance_budgets.json"
  fi
fi

for token in \
  local-end-to-end-performance-budgets \
  budget_id \
  mode \
  command \
  max_elapsed_ms \
  slow_threshold_sec; do
  checked=$((checked + 1))
  rg -q -- "$token" "$MANIFEST" || record_failure "performance budget missing token: $token"
done

budget_count="$(rg -c '"budget_id":' "$MANIFEST" || true)"
checked=$((checked + 1))
if [[ "$budget_count" -lt 3 ]]; then
  record_failure "expected at least 3 performance budgets, got $budget_count"
fi

while IFS= read -r script; do
  [[ -n "$script" ]] || continue
  require_file "$script"
done < <(extract_values script)

while IFS= read -r test_path; do
  [[ -n "$test_path" ]] || continue
  require_file "$test_path"
done < <(extract_values test)

if [[ -n "$TIMING_JSON" ]]; then
  checked=$((checked + 1))
  if [[ ! -f "$TIMING_JSON" ]]; then
    record_failure "timing json not found: $TIMING_JSON"
  elif ! python3 -m json.tool "$TIMING_JSON" >/dev/null; then
    record_failure "invalid timing json: $TIMING_JSON"
  else
    mode="$(rg -o '"mode": "[^"]+"' "$TIMING_JSON" | sed 's/.*"mode": "//; s/"$//' | sed -n '1p')"
    elapsed_ms="$(rg -o '"elapsed_ms": [0-9]+' "$TIMING_JSON" | sed 's/.*: //' | sed -n '1p')"
    budget_ms="$(budget_for_mode "$mode")"
    checked=$((checked + 1))
    if [[ -z "$mode" || -z "$elapsed_ms" || -z "$budget_ms" ]]; then
      record_failure "timing json mode or elapsed_ms does not match a configured budget"
    elif [[ "$elapsed_ms" -gt "$budget_ms" ]]; then
      if [[ "$STRICT" -eq 1 ]]; then
        record_failure "timing budget exceeded: mode=$mode elapsed_ms=$elapsed_ms budget_ms=$budget_ms"
      else
        record_warning "timing budget exceeded: mode=$mode elapsed_ms=$elapsed_ms budget_ms=$budget_ms"
      fi
    fi
  fi
elif [[ "$STRICT" -eq 1 ]]; then
  record_failure "--strict requires --timing-json"
fi

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
elif [[ "${#warnings[@]}" -gt 0 ]]; then
  status="warn"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"%s","budgets":%s,"checked":%s,"failures":%s,"warnings":%s,"mode":"%s","elapsed_ms":%s,"budget_ms":%s,"strict":%s}\n' \
    "$status" "$budget_count" "$checked" "${#failures[@]}" "${#warnings[@]}" "$mode" "$elapsed_ms" "$budget_ms" "$STRICT"
else
  if [[ "$status" == "pass" ]]; then
    echo "[PASS] ADK performance budgets budgets=$budget_count"
  elif [[ "$status" == "warn" ]]; then
    for warning in "${warnings[@]}"; do
      echo "[WARN] $warning" >&2
    done
  else
    for failure in "${failures[@]}"; do
      echo "[FAIL] $failure" >&2
    done
  fi
fi

if [[ "$status" == "fail" ]]; then
  exit 1
fi
