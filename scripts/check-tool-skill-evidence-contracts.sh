#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-tool-skill-evidence-contracts.sh [--summary-json]

Checks ADK tool/skill evidence contracts:
  - tool/skill plan fields and fallback evidence
  - memory maintenance report sections
  - verification command safety policy
  - optional code intelligence provider fallback contract
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
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
checked=0

record_failure() {
  failures+=("$1")
}

require_file() {
  local rel="$1"
  checked=$((checked + 1))
  [[ -f "$ROOT_DIR/$rel" ]] || record_failure "missing file: $rel"
}

require_text() {
  local rel="$1"
  local pattern="$2"
  local label="$3"
  checked=$((checked + 1))
  if [[ ! -f "$ROOT_DIR/$rel" ]]; then
    record_failure "missing file for text check: $rel"
    return
  fi
  if ! rg -q -- "$pattern" "$ROOT_DIR/$rel"; then
    record_failure "$rel missing $label: $pattern"
  fi
}

manifest="manifests/tool_skill_evidence_contracts.json"
require_file "$manifest"
if [[ -f "$ROOT_DIR/$manifest" ]]; then
  checked=$((checked + 1))
  if ! python3 -m json.tool "$ROOT_DIR/$manifest" >/dev/null; then
    record_failure "invalid json: $manifest"
  fi
fi

for token in \
  tool_skill_evidence_plan \
  required_artifacts \
  verification_commands \
  fallback_plan \
  skipped_reasons \
  memory_maintenance_report \
  promotion_candidates \
  contradictions \
  missing_evidence \
  verification_command_safety \
  unsafe_shell_tokens \
  code_intelligence_provider_contract \
  fallback_used \
  omitted_reasons \
  source_reread_required \
  rejected_runtime_surfaces; do
  require_text "$manifest" "$token" "manifest token"
done

require_text "skills/adk-runtime-router/SKILL.md" "Tool / Skill Evidence Plan" "tool skill evidence plan"
require_text "skills/adk-runtime-router/SKILL.md" "Skipped Skills" "skipped skills field"
require_text "skills/adk-runtime-router/SKILL.md" "Fallback Evidence" "fallback evidence field"
require_text "skills/adk-verification-before-completion/SKILL.md" "Tool / Skill Evidence Plan" "verification evidence plan"
require_text "skills/adk-verification-before-completion/SKILL.md" "skipped skills" "skipped skills verification"

require_text "skills/adk-memory-curator/SKILL.md" "promotion_candidates" "promotion candidates"
require_text "skills/adk-memory-curator/SKILL.md" "contradictions" "contradictions section"
require_text "skills/adk-memory-curator/SKILL.md" "missing_evidence" "missing evidence section"
require_text "docs/runbooks/memory-governance.md" "failure replay" "failure replay candidate rule"
require_text "docs/runbooks/memory-governance.md" "contradiction_status" "contradiction status"
require_text "templates/memory/memory-candidate.md" "contradiction_status:" "memory candidate contradiction status"

require_text "docs/runbooks/security-supply-chain.md" "verification_command_safety" "verification command safety"
require_text "docs/runbooks/security-supply-chain.md" "unsafe_shell_tokens" "unsafe shell tokens"
require_text "optional-skills/adk-security-supply-chain/SKILL.md" "verification_command_safety" "security skill command safety"

require_text "skills/adk-token-context-governance/SKILL.md" "code_intelligence_provider_contract" "code intelligence provider contract"
require_text "skills/adk-token-context-governance/SKILL.md" "omitted_reasons" "omitted reasons"
require_text "skills/adk-token-context-governance/SKILL.md" "source_reread_required" "source reread required"

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"status":"%s","checked":%s,"failures":%s}\n' "$status" "$checked" "${#failures[@]}"
else
  if [[ "$status" == "pass" ]]; then
    echo "[PASS] tool/skill evidence contracts"
  else
    for failure in "${failures[@]}"; do
      echo "[FAIL] $failure" >&2
    done
  fi
fi

if [[ "$status" != "pass" ]]; then
  exit 1
fi
