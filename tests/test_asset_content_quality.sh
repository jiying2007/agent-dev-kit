#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

BANNED_PATTERNS=(
  "明确上下文和约束"
  "产出结构化结果并给出验证标准"
  "标注风险和后续动作"
)

for pattern in "${BANNED_PATTERNS[@]}"; do
  if rg -n "$pattern" "$ROOT_DIR/agents" "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" >/tmp/adk_asset_content_quality.txt 2>/dev/null; then
    cat /tmp/adk_asset_content_quality.txt >&2
    fail "template phrase still exists: $pattern"
  fi
done

for file in "$ROOT_DIR"/agents/*/AGENTS.md; do
  [[ -f "$file" ]] || continue
  for heading in "## 核心决策规则" "## 执行流程" "## 必跑验证" "## 阻塞与升级" "## 输出契约" "## 场景输入样例" "## 输出样例"; do
    rg -q "^${heading}$" "$file" || fail "missing heading '$heading' in $file"
  done

  rg -q "\\bpass\\b" "$file" || fail "missing 'pass' example in $file"
  rg -q "needs-fix" "$file" || fail "missing 'needs-fix' example in $file"
done

for file in "$ROOT_DIR"/skills/*/SKILL.md; do
  [[ -f "$file" ]] || continue
  for heading in "## Prerequisites" "## Workflow" "## Quality Gate"; do
    rg -q "^${heading}$" "$file" || fail "missing heading '$heading' in $file"
  done

  if ! rg -q "^## Commands$|^## Evidence Template$" "$file"; then
    fail "skill missing Commands/Evidence Template section: $file"
  fi
done

for file in "$ROOT_DIR"/optional-skills/*/SKILL.md; do
  [[ -f "$file" ]] || continue
  for heading in "## Prerequisites" "## Workflow" "## Quality Gate"; do
    rg -q "^${heading}$" "$file" || fail "missing heading '$heading' in $file"
  done

  if ! rg -q "^## Commands$|^## Evidence Template$" "$file"; then
    fail "optional skill missing Commands/Evidence Template section: $file"
  fi
done

echo "[PASS] asset content quality"
