#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

require_file() {
  local file="$1"
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing memory governance asset: $file"
}

require_text() {
  local file="$1"
  local pattern="$2"
  rg -q "$pattern" "$ROOT_DIR/$file" || fail "$file missing pattern: $pattern"
}

require_file "skills/adk-after-action-review/SKILL.md"
require_file "templates/memory/after-action-review.md"
require_file "templates/memory/memory-candidate.md"
require_file "docs/runbooks/memory-governance.md"
require_file "tests/fixtures/context/protected-key-collision-negative.md"

for field in id stable_identity_key protected_entry_class scope type risk confidence status created_at last_verified next_review_by source evidence content reusable_when write_route requires_user_confirmation duplicate_key_status; do
  require_text "templates/memory/memory-candidate.md" "^${field}:"
done

for field in task success mistakes root_cause fixes lessons memory_candidates risk_decisions verification stale_or_conflict_check; do
  require_text "templates/memory/after-action-review.md" "$field"
done

require_text "skills/adk-after-action-review/SKILL.md" "templates/memory/memory-candidate.md"
require_text "skills/adk-after-action-review/SKILL.md" "requires_user_confirmation: true"
require_text "skills/adk-after-action-review/SKILL.md" "不保存完整聊天记录"
require_text "skills/adk-after-action-review/SKILL.md" "adk-incident-rca-report"

require_text "docs/runbooks/memory-governance.md" "低风险"
require_text "docs/runbooks/memory-governance.md" "中风险"
require_text "docs/runbooks/memory-governance.md" "高风险"
require_text "docs/runbooks/memory-governance.md" "不得保存完整聊天记录"
require_text "docs/runbooks/memory-governance.md" "stale"
require_text "docs/runbooks/memory-governance.md" "conflicts_with"
require_text "docs/runbooks/memory-governance.md" "user-memory"
require_text "docs/runbooks/memory-governance.md" "skill-template"
require_text "docs/runbooks/memory-governance.md" "backend capability matrix"
require_text "docs/runbooks/memory-governance.md" "temporal_strata"
require_text "docs/runbooks/memory-governance.md" "retrieval_fusion"
require_text "docs/runbooks/memory-governance.md" "deterministic_pre_filter"
require_text "docs/runbooks/memory-governance.md" "identity_keys"
require_text "docs/runbooks/memory-governance.md" "graph_topology"
require_text "docs/runbooks/memory-governance.md" "offline_sync"
require_text "docs/runbooks/memory-governance.md" "purge_semantics"
require_text "docs/runbooks/memory-governance.md" "hash-only tombstone"
require_text "docs/runbooks/memory-governance.md" "stable identity key"
require_text "docs/runbooks/memory-governance.md" "protected_entry_class"
require_text "docs/runbooks/memory-governance.md" "duplicate_key_status: collision"

for token in correction decision progress execution-log stable_identity_key duplicate_key_status contradiction_status conflict_review raw_evidence expected_failure; do
  require_text "tests/fixtures/context/protected-key-collision-negative.md" "$token"
done

if rg -q "promotion_action: auto_promote_candidate|promotion_action: promoted" "$ROOT_DIR/tests/fixtures/context/protected-key-collision-negative.md"; then
  fail "protected key collision fixture must not auto-promote duplicate keys"
fi

echo "[PASS] memory governance"
