#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 允许工具目标名，不拦截 manifest/scripts 中的 target 标识。
# 约束仓库说明与 Agent/Skill 资产不出现外部仓库导向信息。
PATTERN='agency-agents-zh|superpowers-zh|superpowers|OpenSpec|auto-research|codex-skill-spec|prompts/'

if rg -n "$PATTERN" \
  "$ROOT_DIR/README.md" \
  "$ROOT_DIR/AGENTS.md" \
  "$ROOT_DIR/docs" \
  "$ROOT_DIR/agents" \
  "$ROOT_DIR/skills" \
  "$ROOT_DIR/optional-skills" \
  >/tmp/gdk_ext_repo_refs.txt 2>/dev/null; then
  cat /tmp/gdk_ext_repo_refs.txt >&2
  echo "[FAIL] external repository references found in docs/assets" >&2
  exit 1
fi

echo "[PASS] no external repository references in docs/assets"
