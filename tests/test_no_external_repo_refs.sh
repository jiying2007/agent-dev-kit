#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 只约束已经退役、不得进入 active product surface 的外部仓身份。
# OpenSpec 是显式受治理的 bridge/reference source；prompts/ 是通用目录名，二者都不是
# “退役外部运行依赖”。历史 change/reference/details 也属于 provenance，不参与该门禁。
PATTERN='agency-agents-zh|superpowers-zh|superpowers|auto-research|platform-skill-spec'

SCAN_PATHS=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/AGENTS.md"
)

while IFS= read -r path; do
  SCAN_PATHS+=("$path")
done < <(
  find \
    "$ROOT_DIR/agents" \
    "$ROOT_DIR/skills" \
    "$ROOT_DIR/optional-skills" \
    "$ROOT_DIR/workflows" \
    -type f \( -name 'AGENTS.md' -o -name 'SKILL.md' -o -name 'WORKFLOW.md' \) \
    -print | sort
)

for path in \
  "$ROOT_DIR/docs/commands.md" \
  "$ROOT_DIR/docs/usage.md" \
  "$ROOT_DIR/docs/agent-operating-rules.md" \
  "$ROOT_DIR/docs/skill-agent-runtime-model.md" \
  "$ROOT_DIR/docs/workflows.md"; do
  [[ -f "$path" ]] && SCAN_PATHS+=("$path")
done

TMP_RESULT="$(mktemp)"
trap 'rm -f "$TMP_RESULT"' EXIT

if rg -n "$PATTERN" "${SCAN_PATHS[@]}" >"$TMP_RESULT" 2>/dev/null; then
  sed -n '1,120p' "$TMP_RESULT" >&2
  echo "[FAIL] retired external repository reference found in active product surface" >&2
  exit 1
fi

echo "[PASS] active product surface has no retired external repository references"
