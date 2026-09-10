#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 该门禁只约束“可执行/可分发产品面”不得依赖已退役的外部参考仓。
# docs/changes、docs/reference、docs/explorations 是 provenance / migration / negative evidence，
# 允许出现外部仓名称；把“已移除 superpowers”之类证据误判为运行依赖会制造假阳性。
PATTERN='agency-agents-zh|superpowers-zh|superpowers|OpenSpec|auto-research|platform-skill-spec|prompts/'

ACTIVE_DOCS=(
  "$ROOT_DIR/README.md"
  "$ROOT_DIR/AGENTS.md"
  "$ROOT_DIR/docs/commands.md"
  "$ROOT_DIR/docs/usage.md"
  "$ROOT_DIR/docs/agent-operating-rules.md"
  "$ROOT_DIR/docs/skill-agent-runtime-model.md"
  "$ROOT_DIR/docs/workflows.md"
)

SCAN_PATHS=(
  "$ROOT_DIR/agents"
  "$ROOT_DIR/skills"
  "$ROOT_DIR/optional-skills"
  "$ROOT_DIR/workflows"
)

for path in "${ACTIVE_DOCS[@]}"; do
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
