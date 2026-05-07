#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/skills"

echo "=== Anti-Rationalization 测试 ==="

# 所有 p0 skill 必须有"借口拦截"章节
P0_SKILLS=(
  adk-requirements-triage
  adk-task-breakdown
  adk-interface-contract-design
  adk-unit-test-embedded
  adk-static-analysis-c-cpp
  adk-systematic-debugging
  adk-verification-before-completion
  adk-commit-pr-quality-gate
)

pass=0
fail=0

for skill in "${P0_SKILLS[@]}"; do
  skill_file="$SKILLS_DIR/$skill/SKILL.md"
  if [[ ! -f "$skill_file" ]]; then
    echo "[FAIL] $skill: SKILL.md 不存在"
    fail=$((fail + 1))
    continue
  fi
  
  if grep -q '借口拦截' "$skill_file"; then
    echo "[PASS] $skill: 包含借口拦截章节"
    pass=$((pass + 1))
  else
    echo "[FAIL] $skill: 缺少借口拦截章节"
    fail=$((fail + 1))
  fi
done

echo ""
echo "结果: $pass 通过, $fail 失败"
[[ $fail -eq 0 ]] && exit 0 || exit 1
