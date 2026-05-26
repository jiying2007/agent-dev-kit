#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 允许工具目标名，不拦截 manifest/scripts 中的 target 标识。
# 约束仓库说明与 Agent/Skill 资产不出现外部仓库导向信息。
# 排除 reference 目录、治理文档和 skills 文档，因为这些是参考文档
PATTERN='agency-agents-zh|superpowers-zh|superpowers|OpenSpec|auto-research|platform-skill-spec|prompts/'

# 检查 docs 目录（排除 reference 子目录和治理文档）
DOCS_EXCL_REFERENCE=$(find "$ROOT_DIR/docs" -type f -name "*.md" \
  ! -path "*/reference/*" \
  ! -name "reference-adoption-matrix.md" \
  ! -name "workspace-governance.md" \
  ! -name "doc-code-consistency-audit-*.md")

if rg -n "$PATTERN" \
  "$ROOT_DIR/README.md" \
  "$ROOT_DIR/AGENTS.md" \
  $DOCS_EXCL_REFERENCE \
  "$ROOT_DIR/agents" \
  >/tmp/adk_ext_repo_refs.txt 2>/dev/null; then
  cat /tmp/adk_ext_repo_refs.txt >&2
  echo "[FAIL] external repository references found in docs/assets" >&2
  exit 1
fi

echo "[PASS] no external repository references in docs/assets"
