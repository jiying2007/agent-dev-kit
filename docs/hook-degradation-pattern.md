# Hook 降级保护模式

> 来源: agent-skills PR #101 的 JSON 转义修复 + 降级保护

## 问题

Hook 脚本依赖外部工具（如 `jq`），当工具不存在时 hook 崩溃，导致整个会话启动失败。

## 解决方案

### 1. 依赖检查 + 优雅降级

```bash
# 正确: 检查依赖，不存在则跳过
if ! command -v jq &>/dev/null; then
    echo "[INFO] jq not found, skipping metadata injection"
    exit 0
fi

# 错误: 直接使用，不存在则崩溃
echo "$data" | jq '.key'
```

### 2. JSON 安全构造

```bash
# 正确: 使用 jq -cn --arg 处理转义
jq -cn --arg text "$skill_content" '{"content": $text}'

# 错误: heredoc 拼接，引号和控制字符会破坏 JSON
cat << EOF
{"content": "$skill_content"}
EOF
```

### 3. Hook 脚本模板

```bash
#!/usr/bin/env bash
set -euo pipefail

# 依赖检查
REQUIRED_TOOLS=(jq curl)
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
        echo "[WARN] $tool not found, hook degraded gracefully"
        exit 0
    fi
done

# 主逻辑（安全执行）
main() {
    # ... hook logic ...
    return 0
}

main "$@"
