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
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing codify governance asset: $file"
}

require_text() {
  local file="$1"
  local pattern="$2"
  rg -q "$pattern" "$ROOT_DIR/$file" || fail "$file missing pattern: $pattern"
}

require_file "skills/adk-after-action-review/SKILL.md"
require_file "skills/adk-verification-before-completion/SKILL.md"
require_file "templates/governance/codify-decision.md"
require_file "tests/fixtures/codify-decision/promotion_candidate_true.md"
require_file "tests/fixtures/codify-decision/promotion_candidate_false.md"

for field in delivery_goal reusable_pattern affected_asset promotion_candidate next_task_friction_reduced reduced_by reduction_evidence do_not_promote_reason owner_review rollback_path verification_evidence; do
  require_text "templates/governance/codify-decision.md" "^${field}:"
  require_text "skills/adk-after-action-review/SKILL.md" "$field"
  require_text "skills/adk-verification-before-completion/SKILL.md" "$field"
done

require_text "skills/adk-after-action-review/SKILL.md" "templates/governance/codify-decision.md"
require_text "skills/adk-verification-before-completion/SKILL.md" "templates/governance/codify-decision.md"
require_text "skills/adk-after-action-review/SKILL.md" "promotion_candidate: true"
require_text "skills/adk-verification-before-completion/SKILL.md" "promotion_candidate: true"
require_text "skills/adk-verification-before-completion/SKILL.md" "needs-fix"
require_text "templates/governance/codify-decision.md" "negative_or_disproved_path"

TRUE_FIXTURE="tests/fixtures/codify-decision/promotion_candidate_true.md"
FALSE_FIXTURE="tests/fixtures/codify-decision/promotion_candidate_false.md"

for pattern in \
  "^promotion_candidate: true" \
  "^next_task_friction_reduced: true" \
  "skill-trigger" \
  "semantic-gate" \
  "reduction_evidence:" \
  "^do_not_promote_reason: not-applicable" \
  "status: approved" \
  "rollback_path:" \
  "verification_evidence:" \
  "negative_or_disproved_path:"; do
  require_text "$TRUE_FIXTURE" "$pattern"
done

for pattern in \
  "^promotion_candidate: false" \
  "^next_task_friction_reduced: false" \
  "none" \
  "reduction_evidence:" \
  "do_not_promote_reason: one-off runtime observation" \
  "status: not-required" \
  "rollback_path:" \
  "verification_evidence:" \
  "negative_or_disproved_path:"; do
  require_text "$FALSE_FIXTURE" "$pattern"
done

echo "[PASS] codify governance"
