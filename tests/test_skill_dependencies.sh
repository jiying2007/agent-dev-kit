#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$(dirname "$SCRIPT_DIR")/manifest.yaml"

echo "=== Skill 依赖图测试 ==="

# 检查 depends_on 字段存在
dep_count=$(grep -c 'depends_on' "$MANIFEST" || true)
if [[ $dep_count -gt 0 ]]; then
  echo "[PASS] depends_on 字段存在 ($dep_count 个)"
else
  echo "[FAIL] depends_on 字段缺失"
  exit 1
fi

# 检查依赖图文档存在
DEP_DOC="$(dirname "$SCRIPT_DIR")/docs/skill-dependency-graph.md"
if [[ -f "$DEP_DOC" ]]; then
  echo "[PASS] skill-dependency-graph.md 存在"
else
  echo "[FAIL] skill-dependency-graph.md 缺失"
  exit 1
fi

echo ""
echo "Skill 依赖图测试通过"
exit 0
