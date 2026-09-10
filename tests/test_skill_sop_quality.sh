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
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing required SOP asset: $file"
}

require_text() {
  local file="$1"
  local pattern="$2"
  rg -q "$pattern" "$ROOT_DIR/$file" || fail "$file missing required pattern: $pattern"
}

require_file "docs/skill-agent-runtime-model.md"
require_file "templates/planning/worker-contract.md"
require_file "docs/runbooks/memory-governance.md"
require_file "templates/memory/after-action-review.md"
require_file "templates/memory/memory-candidate.md"

require_text "docs/skill-agent-runtime-model.md" "Skill"
require_text "docs/skill-agent-runtime-model.md" "Agent"
require_text "docs/skill-agent-runtime-model.md" "Sub-agent"
require_text "docs/skill-agent-runtime-model.md" "MCP/tool"
require_text "docs/skill-agent-runtime-model.md" "Description 触发质量"
require_text "docs/skill-agent-runtime-model.md" "第三方 Skill 不直接进入生产资产链路"

for field in primary_skill supporting_skills scope_read scope_write must_not_touch verification_commands report_schema; do
  require_text "templates/planning/worker-contract.md" "$field"
done

require_text "docs/skill-format-guide.md" "Description 触发质量"
require_text "CONTEXT.md" "Sub-agent"
require_text "skills/adk-parallel-agent-governance/SKILL.md" "templates/planning/worker-contract.md"
require_text "skills/adk-after-action-review/SKILL.md" "templates/memory/memory-candidate.md"
require_text "skills/adk-code-review-loop/SKILL.md" "Snapshot ID:"
require_text "skills/adk-code-review-loop/SKILL.md" "Working Tree Overlay:"
require_text "skills/adk-code-review-loop/SKILL.md" "Reviewer Independence: independent"
require_text "skills/adk-code-review-loop/SKILL.md" "Mechanical Gate: pass"
require_text "skills/adk-code-review-loop/SKILL.md" "不得把机械门禁通过表述为语义审查通过"
require_text "skills/adk-code-review-loop/SKILL.md" "latest_worktree_reviewed"
require_text "skills/adk-interface-contract-design/SKILL.md" "受控生命周期契约"
require_text "skills/adk-interface-contract-design/SKILL.md" "唯一 owner"
require_text "skills/adk-code-review-loop/SKILL.md" "Contract Change Decision: none | design-change"
require_text "skills/adk-code-review-loop/SKILL.md" "设计变更分流"
require_text "skills/adk-code-review-loop/SKILL.md" "Review Round / Mode:"
require_text "skills/adk-code-review-loop/SKILL.md" "New Finding Class Count"
require_text "skills/adk-code-review-loop/SKILL.md" "连续两轮出现新的 blocker 或 major finding class"
require_text "skills/adk-verification-before-completion/SKILL.md" "Lifecycle Operation Evidence:"
require_text "skills/adk-verification-before-completion/SKILL.md" "Review Convergence Evidence:"
require_text "skills/adk-interface-contract-design/SKILL.md" "owner × state × event × resource × termination × invariant"
require_text "skills/adk-test-strategy/SKILL.md" "Validation Resource Matrix:"
require_text "skills/adk-planning-execution-loop/SKILL.md" "logical_task_open"
require_text "skills/adk-planning-execution-loop/SKILL.md" "连续两轮新 blocker/major finding class"
require_text "fixtures/lifecycle-review-convergence/fail/design-change-without-replan.md" "must return to contract design and replan"
require_text "fixtures/lifecycle-review-convergence/pass/synchronous-not-applicable.md" "not forced into a lifecycle contract"
require_text "docs/runbooks/memory-governance.md" "不得保存完整聊天记录"

"$ROOT_DIR/scripts/validate-assets.sh" --strict >/dev/null
"$ROOT_DIR/scripts/check-memory-governance.sh" >/dev/null

echo "[PASS] skill SOP quality"
