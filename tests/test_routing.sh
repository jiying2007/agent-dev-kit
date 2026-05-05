#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$(dirname "$SCRIPT_DIR")/manifest.yaml"

echo "=== 路由表测试 ==="

# 检查 routing 字段存在
if ! grep -q '^routing:' "$MANIFEST"; then
  echo "[FAIL] manifest.yaml 缺少 routing 字段"
  exit 1
fi
echo "[PASS] routing 字段存在"

# 检查 intent_zh 存在
zh_count=$(grep -c 'intent_zh' "$MANIFEST" || true)
if [[ $zh_count -gt 0 ]]; then
  echo "[PASS] intent_zh 字段存在 ($zh_count 条)"
else
  echo "[FAIL] intent_zh 字段缺失"
  exit 1
fi

# 检查 primary_skill 存在
ps_count=$(grep -c 'primary_skill' "$MANIFEST" || true)
if [[ $ps_count -gt 0 ]]; then
  echo "[PASS] primary_skill 字段存在 ($ps_count 条)"
else
  echo "[FAIL] primary_skill 字段缺失"
  exit 1
fi

echo ""
echo "路由表测试通过"
exit 0
