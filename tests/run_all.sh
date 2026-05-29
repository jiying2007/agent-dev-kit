#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERBOSE=0
FAIL_FAST=0
MAX_FAILURE_LINES="${ADK_TEST_FAILURE_LINES:-80}"

usage() {
  cat <<USAGE
Usage:
  tests/run_all.sh [--verbose] [--fail-fast] [--max-failure-lines <n>]

Runs the full adk regression suite.

Default output is compact: one PASS/FAIL line per test plus bounded failure logs.
Use --verbose only when the full child-test output is needed.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose)
      VERBOSE=1
      shift
      ;;
    --fail-fast)
      FAIL_FAST=1
      shift
      ;;
    --max-failure-lines)
      MAX_FAILURE_LINES="${2:-}"
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

[[ "$MAX_FAILURE_LINES" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --max-failure-lines must be numeric" >&2
  exit 1
}

TESTS=(
  test_validate.sh
  test_asset_content_quality.sh
  test_format.sh
  test_no_external_repo_refs.sh
  test_file_modes.sh
  test_install.sh
  test_profile_coherence.sh
  test_optional_skills.sh
  test_convert.sh
  test_runtime_boundary.sh
  test_token_budget.sh
  test_token_context_governance.sh
  test_openai_developers_governance.sh
  test_workflow_closure.sh
  test_change_governance.sh
  test_evidence_index.sh
  test_fallback_sunset_matrix.sh
  test_pilot_readiness.sh
  test_embedded_production_field_pilot.sh
  test_embedded_workflow_pilots.sh
  test_embedded_test_matrix_example.sh
  test_workflow.sh
  test_openspec_bridge.sh
  test_catalog.sh
  test_skill_trigger_matrix.sh
  test_boundary_conditions_match.sh
  test_enhanced_gate_check.sh
  test_templates.sh
  test_context_md.sh
  test_boundary_conditions.sh
  test_integration.sh
  test_profile_coherence_enhanced.sh
  test_match_effectiveness.sh
  test_skill_content.sh
  test_skill_sop_quality.sh
  test_memory_governance.sh
  test_capability_uplift.sh
  test_docs_cli_alignment.sh
  test_scripts_smoke.sh
)

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

print_bounded_log() {
  local label="$1"
  local file="$2"
  if [[ -s "$file" ]]; then
    echo "  ${label} (last ${MAX_FAILURE_LINES} lines):"
    tail -n "$MAX_FAILURE_LINES" "$file" | sed 's/^/    /'
  fi
}

run_test() {
  local script="$1"
  local path="$SCRIPT_DIR/$script"
  local name="${script%.sh}"
  local stdout_file="$TMP_DIR/${name}.stdout"
  local stderr_file="$TMP_DIR/${name}.stderr"

  TOTAL=$((TOTAL + 1))

  if [[ "$VERBOSE" -eq 1 ]]; then
    echo "=== RUN ${name} ==="
    if "$path"; then
      echo "[PASS] ${name}"
      PASS_COUNT=$((PASS_COUNT + 1))
      return 0
    fi
  else
    if "$path" >"$stdout_file" 2>"$stderr_file"; then
      echo "[PASS] ${name}"
      PASS_COUNT=$((PASS_COUNT + 1))
      return 0
    fi
  fi

  echo "[FAIL] ${name}" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
  if [[ "$VERBOSE" -eq 0 ]]; then
    print_bounded_log "stderr" "$stderr_file" >&2
    print_bounded_log "stdout" "$stdout_file" >&2
  fi

  if [[ "$FAIL_FAST" -eq 1 ]]; then
    exit 1
  fi
}

for test_script in "${TESTS[@]}"; do
  run_test "$test_script"
done

echo "[SUMMARY] tests=${TOTAL} pass=${PASS_COUNT} fail=${FAIL_COUNT}"

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

echo "All tests passed"
