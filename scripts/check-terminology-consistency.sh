#!/usr/bin/env bash
set -euo pipefail

# 术语一致性检查
# 来源: mattpocock-skills 的全局术语替换实践

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

ERRORS=0

echo "=== 术语一致性检查 ==="

# 检查已废弃术语
DEPRECATED_TERMS=(
    "global-dev-kit|应使用 agent-dev-kit"
    "\bgdk\b|应使用 adk"
    "workflow.*methodology|建议统一使用 methodology"
)

for entry in "${DEPRECATED_TERMS[@]}"; do
    IFS='|' read -r pattern message <<< "$entry"
    matches=$(grep -rn "$pattern" "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" "$ROOT_DIR/agents"         --include='*.md' 2>/dev/null | grep -v '.git/' | wc -l)
    if [[ "$matches" -gt 0 ]]; then
        echo -e "${YELLOW}[WARN]${NC} 发现 $matches 处 '$pattern' — $message"
        grep -rn "$pattern" "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" "$ROOT_DIR/agents"             --include='*.md' 2>/dev/null | grep -v '.git/' | head -5
        ERRORS=$((ERRORS + matches))
    fi
done

# 检查 frontmatter 中的 name 一致性
echo ""
echo "=== Frontmatter name vs 目录名一致性 ==="
for d in "$ROOT_DIR"/skills/*/; do
    dir_name=$(basename "$d")
    md_name=$(grep -m1 '^name:' "$d/SKILL.md" 2>/dev/null | sed 's/name: *//' | tr -d '"')
    if [[ "$dir_name" != "$md_name" ]]; then
        echo -e "${RED}[ERROR]${NC} 目录=$dir_name, frontmatter=$md_name"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [[ "$ERRORS" -eq 0 ]]; then
    echo -e "${GREEN}[PASS]${NC} 术语一致性检查通过"
    exit 0
else
    echo -e "${RED}[FAIL]${NC} 发现 $ERRORS 处不一致"
    exit 1
fi
