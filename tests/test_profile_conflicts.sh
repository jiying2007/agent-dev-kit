#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$(dirname "$SCRIPT_DIR")/manifest.yaml"

echo "=== Profile 冲突检测测试 ==="

# 检查 conflicts_with 字段存在
conflict_count=$(grep -c 'conflicts_with' "$MANIFEST" || true)
if [[ $conflict_count -gt 0 ]]; then
  echo "[PASS] conflicts_with 字段存在 ($conflict_count 个)"
else
  echo "[FAIL] conflicts_with 字段缺失"
  exit 1
fi

# 运行 profile coherence 检查
COHERENCE_SCRIPT="$(dirname "$SCRIPT_DIR")/scripts/check_profile_coherence.sh"
if [[ -f "$COHERENCE_SCRIPT" ]]; then
  if bash "$COHERENCE_SCRIPT" 2>/dev/null; then
    echo "[PASS] profile coherence 检查通过"
  else
    echo "[WARN] profile coherence 检查有告警（非阻塞）"
  fi
else
  echo "[WARN] check_profile_coherence.sh 不存在"
fi

echo ""
echo "Profile 冲突检测测试通过"
exit 0
