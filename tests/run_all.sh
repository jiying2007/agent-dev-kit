#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VERBOSE=0
FAIL_FAST=0
QUICK=0
TIMING_JSON=""
MAX_FAILURE_LINES="${ADK_TEST_FAILURE_LINES:-80}"
SLOW_THRESHOLD_SEC="${ADK_TEST_SLOW_THRESHOLD_SEC:-30}"

usage() {
  cat <<USAGE
Usage:
  tests/run_all.sh [--quick] [--verbose] [--fail-fast] [--max-failure-lines <n>] [--timing-json <path>] [--slow-threshold-sec <n>]

Runs the full adk regression suite.

Default output is compact: one PASS/FAIL line per test plus bounded failure logs.
Use --quick for high-signal development checks before the full release gate.
Use --verbose only when the full child-test output is needed.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --quick)
      QUICK=1
      shift
      ;;
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
    --timing-json)
      TIMING_JSON="${2:-}"
      shift 2
      ;;
    --slow-threshold-sec)
      SLOW_THRESHOLD_SEC="${2:-}"
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
[[ "$SLOW_THRESHOLD_SEC" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --slow-threshold-sec must be numeric" >&2
  exit 1
}

TESTS=(
  test_validate.sh
  test_manifest_contract.sh
  test_manifest_consumer_boundary.sh
  test_python_launcher.sh
  test_asset_content_quality.sh
  test_format.sh
  test_no_external_repo_refs.sh
  test_file_modes.sh
  test_install.sh
  test_profile_coherence.sh
  test_optional_skills.sh
  test_convert.sh
  test_runtime_boundary.sh
  test_target_contracts.sh
  test_effect_eval.sh
  test_product_maturity_v4.sh
  test_runtime_bundle.sh
  test_software_m5_ready.sh
  test_repository_runtime_evidence.sh
  test_token_budget.sh
  test_token_context_governance.sh
  test_task_cost.sh
  test_runtime_control.sh
  test_official_docs_governance.sh
  test_official_docs_timezone.sh
  test_intent_boundary_governance.sh
  test_agent_ecosystem_standards.sh
  test_agent_value.sh
  test_trace_summary.sh
  test_run_evidence.sh
  test_effect_comparator.sh
  test_runtime_capabilities.sh
  test_tool_skill_evidence_contracts.sh
  test_asset_taxonomy.sh
  test_workflow_contract.sh
  test_workflow_ir.sh
  test_workflow_closure.sh
  test_goal_contracts.sh
  test_capability_health.sh
  test_harness_readiness.sh
  test_local_ci_parity.sh
  test_performance_budgets.sh
  test_change_governance.sh
  test_evidence_index.sh
  test_evidence_graph.sh
  test_fallback_sunset_matrix.sh
  test_pilot_readiness.sh
  test_embedded_production_field_pilot.sh
  test_embedded_workflow_pilots.sh
  test_embedded_test_matrix_example.sh
  test_workflow.sh
  test_workflow_verify_fail_closed.sh
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
  test_performance_ops.sh
  test_scripts_smoke.sh
)

QUICK_TESTS=(
  test_validate.sh
  test_manifest_contract.sh
  test_manifest_consumer_boundary.sh
  test_python_launcher.sh
  test_runtime_boundary.sh
  test_target_contracts.sh
  test_effect_eval.sh
  test_runtime_bundle.sh
  test_software_m5_ready.sh
  test_repository_runtime_evidence.sh
  test_token_budget.sh
  test_runtime_control.sh
  test_intent_boundary_governance.sh
  test_official_docs_timezone.sh
  test_agent_ecosystem_standards.sh
  test_agent_value.sh
  test_trace_summary.sh
  test_run_evidence.sh
  test_effect_comparator.sh
  test_workflow_contract.sh
  test_workflow_ir.sh
  test_workflow_closure.sh
  test_workflow_verify_fail_closed.sh
  test_goal_contracts.sh
  test_evidence_graph.sh
  test_capability_health.sh
  test_harness_readiness.sh
  test_local_ci_parity.sh
  test_performance_budgets.sh
  test_skill_trigger_matrix.sh
  test_scripts_smoke.sh
)

if [[ "$QUICK" -eq 1 ]]; then
  TESTS=("${QUICK_TESTS[@]}")
fi
SUITE_MODE="full"
[[ "$QUICK" -eq 1 ]] && SUITE_MODE="quick"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0
RUN_START_NS="$(date +%s%N)"
declare -a RESULT_NAMES=()
declare -a RESULT_STATUS=()
declare -a RESULT_MS=()

json_string() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '"%s"' "$value"
}

write_timing_json() {
  [[ -n "$TIMING_JSON" ]] || return 0
  local run_end_ns elapsed_ms first i
  run_end_ns="$(date +%s%N)"
  elapsed_ms=$(( (run_end_ns - RUN_START_NS) / 1000000 ))
  mkdir -p "$(dirname "$TIMING_JSON")"
  {
    printf '{\n'
    printf '  "schema_version": 1,\n'
    printf '  "mode": %s,\n' "$([[ "$QUICK" -eq 1 ]] && json_string quick || json_string full)"
    printf '  "status": %s,\n' "$([[ "$FAIL_COUNT" -gt 0 ]] && json_string fail || json_string pass)"
    printf '  "total": %s,\n' "$TOTAL"
    printf '  "pass": %s,\n' "$PASS_COUNT"
    printf '  "fail": %s,\n' "$FAIL_COUNT"
    printf '  "elapsed_ms": %s,\n' "$elapsed_ms"
    printf '  "slow_threshold_sec": %s,\n' "$SLOW_THRESHOLD_SEC"
    printf '  "tests": [\n'
    first=1
    for i in "${!RESULT_NAMES[@]}"; do
      [[ "$first" -eq 1 ]] || printf ',\n'
      first=0
      printf '    {"name": %s, "status": %s, "elapsed_ms": %s}' \
        "$(json_string "${RESULT_NAMES[$i]}")" \
        "$(json_string "${RESULT_STATUS[$i]}")" \
        "${RESULT_MS[$i]}"
    done
    printf '\n  ],\n'
    printf '  "slow_tests": [\n'
    first=1
    for i in "${!RESULT_NAMES[@]}"; do
      if [[ "${RESULT_MS[$i]}" -ge $((SLOW_THRESHOLD_SEC * 1000)) ]]; then
        [[ "$first" -eq 1 ]] || printf ',\n'
        first=0
        printf '    {"name": %s, "elapsed_ms": %s}' \
          "$(json_string "${RESULT_NAMES[$i]}")" \
          "${RESULT_MS[$i]}"
      fi
    done
    printf '\n  ]\n'
    printf '}\n'
  } >"$TIMING_JSON"
}

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
  local start_ns end_ns elapsed_ms

  TOTAL=$((TOTAL + 1))
  start_ns="$(date +%s%N)"

  if [[ "$VERBOSE" -eq 1 ]]; then
    echo "=== RUN ${name} ==="
    if ADK_TEST_SUITE_DIR="$TMP_DIR" ADK_TEST_SUITE_MODE="$SUITE_MODE" "$path"; then
      end_ns="$(date +%s%N)"
      elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
      echo "[PASS] ${name}"
      PASS_COUNT=$((PASS_COUNT + 1))
      RESULT_NAMES+=("$name")
      RESULT_STATUS+=("pass")
      RESULT_MS+=("$elapsed_ms")
      return 0
    fi
  else
    if ADK_TEST_SUITE_DIR="$TMP_DIR" ADK_TEST_SUITE_MODE="$SUITE_MODE" "$path" >"$stdout_file" 2>"$stderr_file"; then
      end_ns="$(date +%s%N)"
      elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
      echo "[PASS] ${name}"
      PASS_COUNT=$((PASS_COUNT + 1))
      RESULT_NAMES+=("$name")
      RESULT_STATUS+=("pass")
      RESULT_MS+=("$elapsed_ms")
      return 0
    fi
  fi

  end_ns="$(date +%s%N)"
  elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))
  echo "[FAIL] ${name}" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
  RESULT_NAMES+=("$name")
  RESULT_STATUS+=("fail")
  RESULT_MS+=("$elapsed_ms")
  if [[ "$VERBOSE" -eq 0 ]]; then
    print_bounded_log "stderr" "$stderr_file" >&2
    print_bounded_log "stdout" "$stdout_file" >&2
  fi

  if [[ "$FAIL_FAST" -eq 1 ]]; then
    write_timing_json
    exit 1
  fi
}

for test_script in "${TESTS[@]}"; do
  run_test "$test_script"
done

echo "[SUMMARY] tests=${TOTAL} pass=${PASS_COUNT} fail=${FAIL_COUNT}"
write_timing_json

if [[ "$FAIL_COUNT" -gt 0 ]]; then
  exit 1
fi

echo "All tests passed"
