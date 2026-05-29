#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

failures=()

record_failure() {
  failures+=("$1")
}

require_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    record_failure "missing file: ${file#$ROOT_DIR/}"
  fi
}

require_text() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if [[ ! -f "$file" ]]; then
    return
  fi
  if ! rtk rg -q -- "$pattern" "$file"; then
    record_failure "${file#$ROOT_DIR/} missing ${label}"
  fi
}

RUNBOOK="$ROOT_DIR/docs/runbooks/token-context-governance.md"
MEMORY_TEMPLATE="$ROOT_DIR/templates/context/memory-search-result.md"
LOW_TOKEN_TEMPLATE="$ROOT_DIR/templates/context/low-token-profile.md"
MANIFEST="$ROOT_DIR/manifests/external_agent_pattern_contracts.json"

for file in "$RUNBOOK" "$MEMORY_TEMPLATE" "$LOW_TOKEN_TEMPLATE" "$MANIFEST"; do
  require_file "$file"
done

for term in \
  'search_index' \
  'timeline_context' \
  'observation_details' \
  'templates/context/memory-search-result.md' \
  'raw fallback' \
  'owner review'; do
  require_text "$RUNBOOK" "$term" "memory search guidance: $term"
done

for field in \
  'query:' \
  'result_ids:' \
  'time_window:' \
  'project_scope:' \
  'observation_type:' \
  'redaction_status:' \
  'detail_fetch_reason:' \
  'raw_fallback:'; do
  require_text "$MEMORY_TEMPLATE" "$field" "memory template field: $field"
done

for field in \
  'trigger:' \
  'active_scope:' \
  'technical_terms_preserved:' \
  'safety_exception:' \
  'restore_condition:' \
  'user_override:'; do
  require_text "$LOW_TOKEN_TEMPLATE" "$field" "low-token template field: $field"
done

for exception in \
  'security warning' \
  'irreversible action confirmation' \
  'multi-step ambiguity' \
  'review finding precision'; do
  require_text "$RUNBOOK" "$exception" "runbook safety exception: $exception"
  require_text "$LOW_TOKEN_TEMPLATE" "$exception" "low-token template safety exception: $exception"
done

for contract_id in \
  'memory-search-progressive-disclosure-v1' \
  'low-token-communication-profile-v1'; do
  require_text "$MANIFEST" "$contract_id" "manifest contract: $contract_id"
done

if [[ "${#failures[@]}" -gt 0 ]]; then
  for failure in "${failures[@]}"; do
    echo "[FAIL] $failure" >&2
  done
  exit 1
fi

echo "[PASS] context experience patterns"
