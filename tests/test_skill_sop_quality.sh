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
require_text "docs/runbooks/memory-governance.md" "不得保存完整聊天记录"

"$ROOT_DIR/scripts/validate-assets.sh" --strict >/dev/null
"$ROOT_DIR/scripts/check-memory-governance.sh" >/dev/null

echo "[PASS] skill SOP quality"
