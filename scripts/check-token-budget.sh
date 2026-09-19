#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0
MAX_SKILL_LINES=140
MAX_DOC_LINES=560
MAX_AGENTS_BYTES=3500
SOFT_AGENTS_BYTES=2975

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-token-budget.sh [--summary-json] [--max-skill-lines <n>] [--max-doc-lines <n>]

Checks active adk assets for token-budget regressions:
  - SKILL.md entry files stay compact; long details belong in references/.
  - active docs stay below a hard line budget; archive reports are excluded.
  - high-signal governance scripts expose --summary-json.
  - full regression runner defaults to compact bounded output.
  - context compression assets preserve raw evidence and fallback rules.
  - context budget profiles declare mode, risk, read tier and raw fallback.
  - root AGENTS and task-cost routing contracts stay bounded.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    --max-skill-lines)
      MAX_SKILL_LINES="${2:-}"
      shift 2
      ;;
    --max-doc-lines)
      MAX_DOC_LINES="${2:-}"
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

[[ "${MAX_SKILL_LINES}" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --max-skill-lines must be numeric" >&2
  exit 1
}
[[ "${MAX_DOC_LINES}" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --max-doc-lines must be numeric" >&2
  exit 1
}

failures=()
warnings=()
skill_files=0
doc_files=0
max_skill_lines=0
max_skill_file="-"
max_doc_lines=0
max_doc_file="-"
summary_scripts=0
[[ ! -e "$ROOT_DIR/scripts/convert-assets.sh" ]] || record_failure "retired export wrapper returned: scripts/convert-assets.sh"
[[ ! -e "$ROOT_DIR/scripts/validate-assets.sh" ]] || record_failure "retired validation wrapper returned: scripts/validate-assets.sh"
compact_test_runner=0
context_governance_assets=0
agents_bytes="$(wc -c <"$ROOT_DIR/AGENTS.md" | tr -d ' ')"
if [[ "$agents_bytes" -gt "$MAX_AGENTS_BYTES" ]]; then
  failures+=("root AGENTS token budget exceeded: bytes=${agents_bytes} limit=${MAX_AGENTS_BYTES}")
fi
if [[ "$agents_bytes" -gt "$SOFT_AGENTS_BYTES" ]]; then
  warnings+=("root AGENTS above 85% soft budget: bytes=${agents_bytes} soft=${SOFT_AGENTS_BYTES}")
fi
agents_estimated_tokens=$(((agents_bytes + 3) / 4))

record_failure() {
  failures+=("$1")
}

line_count() {
  wc -l <"$1" | tr -d ' '
}

check_file_budget() {
  local file="$1"
  local limit="$2"
  local kind="$3"
  local lines
  lines="$(line_count "$file")"
  case "$kind" in
    skill)
      skill_files=$((skill_files + 1))
      if [[ "$lines" -gt "$max_skill_lines" ]]; then
        max_skill_lines="$lines"
        max_skill_file="${file#$ROOT_DIR/}"
      fi
      ;;
    doc)
      doc_files=$((doc_files + 1))
      if [[ "$lines" -gt "$max_doc_lines" ]]; then
        max_doc_lines="$lines"
        max_doc_file="${file#$ROOT_DIR/}"
      fi
      ;;
  esac
  if [[ "$lines" -gt "$limit" ]]; then
    record_failure "${kind} token budget exceeded: ${file#$ROOT_DIR/} lines=${lines} limit=${limit}"
  fi
}

require_context_asset() {
  local file="$1"
  if [[ -f "$file" ]]; then
    context_governance_assets=$((context_governance_assets + 1))
  else
    record_failure "context governance asset missing: ${file#$ROOT_DIR/}"
  fi
}

require_context_text() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    return
  fi
  if ! rg -q -- "$pattern" "$file"; then
    record_failure "context governance text missing: ${file#$ROOT_DIR/} requires ${label}"
  fi
}

require_context_absent_text() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    return
  fi
  if rg -q -- "$pattern" "$file"; then
    record_failure "context governance forbidden text present: ${file#$ROOT_DIR/} forbids ${label}"
  fi
}

while IFS= read -r -d '' file; do
  check_file_budget "$file" "$MAX_SKILL_LINES" skill
done < <(find "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" -name SKILL.md -print0)

while IFS= read -r -d '' file; do
  check_file_budget "$file" "$MAX_DOC_LINES" doc
done < <(
  find "$ROOT_DIR/docs" "$ROOT_DIR/templates" -type f \
    \( -name '*.md' -o -name '*.tsv' -o -name '*.yaml' -o -name '*.yml' \) \
    -not -path '*/archive/*' \
    -print0
)

for script in \
  "$ROOT_DIR/scripts/check-runtime-boundary.sh" \
  "$ROOT_DIR/scripts/check-workflow-closure.sh" \
  "$ROOT_DIR/scripts/pilot-readiness.sh"; do
  summary_scripts=$((summary_scripts + 1))
  if ! rg -q -- '--summary-json' "$script"; then
    record_failure "summary-json missing: ${script#$ROOT_DIR/}"
  fi
done

if rg -q -- '--verbose' "$ROOT_DIR/tests/run_all.sh" \
  && rg -q -- 'MAX_FAILURE_LINES' "$ROOT_DIR/tests/run_all.sh"; then
  compact_test_runner=1
else
  record_failure "compact test runner missing: tests/run_all.sh must default to bounded output and expose --verbose"
fi

for asset in \
  "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" \
  "$ROOT_DIR/templates/context/tool-output-summary.md" \
  "$ROOT_DIR/templates/context/raw-evidence-index.md" \
  "$ROOT_DIR/templates/context/context-budget-profile.md" \
  "$ROOT_DIR/templates/context/task-cost-profile.md" \
  "$ROOT_DIR/templates/context/project-map.md" \
  "$ROOT_DIR/templates/context/memory-search-result.md" \
	  "$ROOT_DIR/templates/context/low-token-profile.md" \
	  "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" \
	  "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" \
	  "$ROOT_DIR/docs/runbooks/token-context-governance.md"; do
  require_context_asset "$asset"
done

require_context_text "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" 'raw_evidence' 'raw_evidence'
require_context_text "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" 'fallback_condition' 'fallback_condition'
require_context_text "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" 'Budget Modes' 'budget modes section'
require_context_text "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" '审计' 'audit mode'
require_context_text "$ROOT_DIR/skills/adk-token-context-governance/SKILL.md" '高风险' 'high-risk raw-read rule'
require_context_text "$ROOT_DIR/templates/context/tool-output-summary.md" 'read_tier:' 'read_tier field'
require_context_text "$ROOT_DIR/templates/context/tool-output-summary.md" 'raw_evidence:' 'raw_evidence field'
require_context_text "$ROOT_DIR/templates/context/tool-output-summary.md" 'confidence:' 'confidence field'
require_context_text "$ROOT_DIR/templates/context/tool-output-summary.md" 'fallback_condition:' 'fallback_condition field'
require_context_text "$ROOT_DIR/templates/context/raw-evidence-index.md" 'raw_path' 'raw_path column'
require_context_text "$ROOT_DIR/templates/context/raw-evidence-index.md" 'summary_path' 'summary_path column'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'task_type:' 'task_type field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'risk_level:' 'risk_level field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'read_tier:' 'read_tier field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'budget_profile:' 'budget_profile field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'compress_allowed:' 'compress_allowed field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'raw_required:' 'raw_required field'
require_context_text "$ROOT_DIR/templates/context/context-budget-profile.md" 'audit' 'audit mode'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'task_cost:' 'task cost field'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'micro' 'micro task tier'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'high-risk' 'high-risk task tier'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'primary_skill_budget:' 'primary skill budget'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'hub_preflight:' 'Hub preflight policy'
require_context_text "$ROOT_DIR/templates/context/task-cost-profile.md" 'verification_tier:' 'verification tier'
require_context_text "$ROOT_DIR/templates/context/project-map.md" 'Generated / Do Not Read Fully' 'generated exclusion section'
require_context_text "$ROOT_DIR/templates/context/project-map.md" 'High-Risk Raw-Read Areas' 'high-risk raw-read section'
require_context_text "$ROOT_DIR/templates/context/project-map.md" 'Last Verified' 'last verified section'
require_context_text "$ROOT_DIR/templates/context/memory-search-result.md" 'detail_fetch_reason:' 'memory detail fetch reason'
require_context_text "$ROOT_DIR/templates/context/memory-search-result.md" 'owner_approval_for_persistent_memory:' 'persistent memory approval'
require_context_text "$ROOT_DIR/templates/context/low-token-profile.md" 'safety_exception:' 'low token safety exception'
require_context_text "$ROOT_DIR/templates/context/low-token-profile.md" 'restore_condition:' 'low token restore condition'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'L0' 'read tier L0'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'L1' 'read tier L1'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'L2' 'read tier L2'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'L3' 'read tier L3'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" '高风险' 'high-risk raw-read guidance'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" '原文' 'raw evidence guidance'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'docker logs --tail' 'bounded docker logs guidance'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" '不得压缩' 'no-compression boundary'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" '上下文预算模式' 'context budget modes'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'CTX_PRESSURE' 'handoff pressure guidance'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'incremental compression' 'incremental compression boundary'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'whole-context compression' 'whole-context compression boundary'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'deterministic pre-filter' 'deterministic pre-filter'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" 'stable key' 'stable key preservation'
require_context_text "$ROOT_DIR/docs/runbooks/token-context-governance.md" '被保护条目' 'protected entry summary'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'expected_failure:' 'protected key collision expected failure'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'protected_entry_class: correction' 'correction protected key'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'protected_entry_class: decision' 'decision protected key'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'protected_entry_class: progress' 'progress protected key'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'protected_entry_class: execution-log' 'execution-log protected key'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'duplicate_key_status: collision' 'duplicate key collision marker'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'contradiction_status: conflict_review' 'conflict review marker'
require_context_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'raw_evidence:' 'raw fallback for protected collision'
require_context_absent_text "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md" 'promotion_action: auto_promote_candidate|promotion_action: promoted' 'auto promotion for protected key collision'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'expected_failure:' 'archive lifecycle expected failure'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'lifecycle_state: research' 'research lifecycle state'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'requested_promotion: engineering' 'engineering promotion request'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'requested_promotion: archive' 'archive promotion request'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'raw_evidence:' 'archive lifecycle raw evidence gate'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'owner_review:' 'archive lifecycle owner review gate'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'rollback_path:' 'archive lifecycle rollback gate'
require_context_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'promotion_action: blocked' 'blocked promotion action'
require_context_absent_text "$ROOT_DIR/tests/fixtures/memory/archive-lifecycle-promotion-negative.md" 'promotion_action: auto_promote_candidate|promotion_action: promoted' 'auto promotion for archive lifecycle'

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
fi
budget_status="within-soft-limit"
[[ "${#warnings[@]}" -eq 0 ]] || budget_status="warning"
[[ "${#failures[@]}" -eq 0 ]] || budget_status="hard-limit-failed"

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"status":"%s","budget_status":"%s","estimate_method":"utf8-bytes-ceil-div-4","agents_bytes":%s,"agents_soft_limit":%s,"agents_limit":%s,"agents_estimated_tokens":%s,"skill_files":%s,"max_skill_lines":%s,"max_skill_file":"%s","doc_files":%s,"max_doc_lines":%s,"max_doc_file":"%s","summary_scripts":%s,"compact_test_runner":%s,"context_governance_assets":%s,"warnings":%s,"failures":%s}\n' \
    "$status" \
    "$budget_status" \
    "$agents_bytes" \
    "$SOFT_AGENTS_BYTES" \
    "$MAX_AGENTS_BYTES" \
    "$agents_estimated_tokens" \
    "$skill_files" \
    "$max_skill_lines" \
    "$max_skill_file" \
    "$doc_files" \
    "$max_doc_lines" \
    "$max_doc_file" \
    "$summary_scripts" \
    "$compact_test_runner" \
    "$context_governance_assets" \
    "${#warnings[@]}" \
    "${#failures[@]}"
else
  echo "[INFO] agents_bytes=${agents_bytes} soft=${SOFT_AGENTS_BYTES} hard=${MAX_AGENTS_BYTES} estimated_tokens=${agents_estimated_tokens} budget_status=${budget_status}"
  if [[ "${#warnings[@]}" -gt 0 ]]; then
    printf '[WARN] %s\n' "${warnings[@]}" >&2
  fi
  echo "[INFO] skill_files=${skill_files} max_skill_lines=${max_skill_lines} max_skill_file=${max_skill_file} limit=${MAX_SKILL_LINES}"
  echo "[INFO] doc_files=${doc_files} max_doc_lines=${max_doc_lines} max_doc_file=${max_doc_file} limit=${MAX_DOC_LINES}"
  echo "[INFO] summary_json_scripts=${summary_scripts}"
  echo "[INFO] compact_test_runner=${compact_test_runner}"
  echo "[INFO] context_governance_assets=${context_governance_assets}"
  if [[ "${#failures[@]}" -gt 0 ]]; then
    echo "[FAIL] token budget check failed" >&2
    printf '  - %s\n' "${failures[@]}" >&2
    exit 1
  fi
  echo "[PASS] token budget checks passed"
fi

if [[ "${#failures[@]}" -gt 0 ]]; then
  exit 1
fi
