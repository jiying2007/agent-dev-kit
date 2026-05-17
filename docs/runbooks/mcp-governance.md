# MCP Governance Runbook

## 1. 目标

MCP 是 `~/codex` 运行环境的外部能力入口。agent-dev-kit 只声明可交接的 MCP 清单与审计规则，不直接向 `~/.codex` 写入 MCP 配置。

## 2. 当前策略

- `manifest.yaml:mcp_servers` 是 MCP 声明入口。
- 当前默认值为空数组，表示 adk 不隐式安装任何 MCP server。
- `convert --target codex` 必须导出 `manifest-fragments/mcp_servers.json`，由 `~/codex` 决定是否合并。

## 3. 新增 MCP 准入

1. 明确 server 名称、命令、参数、权限边界和数据访问范围。
2. 给出风险评估：网络访问、文件写入、凭证读取、执行外部命令。
3. 在 `~/codex` 合并前运行声明清单与实际清单差异检查。
4. 在 `~/.codex` apply 后运行：
   ```bash
   codex mcp list
   ```
5. 记录差异结论：新增、移除、参数变化、权限变化。

## 4. 阻断条件

- MCP server 需要读取密钥但没有说明凭证来源。
- MCP server 具备写文件或执行命令能力但没有用途边界。
- `manifest-fragments/mcp_servers.json` 与 `codex mcp list` 差异无解释。
- 试图绕过 `~/codex` 直接修改 `~/.codex/config.toml`。
