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
3. 声明信任边界：server 来源、版本锚点、凭证来源、允许的 base URL、允许调用的工具集合。
4. 为高风险工具写出执行前策略：哪些入参允许、哪些路径可读写、哪些命令必须拒绝。
5. 在 `~/codex` 合并前运行声明清单与实际清单差异检查。
6. 在 `~/.codex` apply 后运行：
   ```bash
   codex mcp list
   ```
7. 记录差异结论：新增、移除、参数变化、权限变化。

## 4. Tool-call Policy

MCP 返回的工具调用请求一律视为不可信输入。允许执行前必须完成确定性检查，不依赖 LLM 自行判断。

| 风险面 | 必须声明 | 默认策略 |
|---|---|---|
| 文件读取 | 允许目录、禁止目录、最大文件大小 | 未声明则拒绝 |
| 文件写入 | 允许路径、覆盖规则、备份或 dry-run | 未声明则拒绝 |
| 命令执行 | 命令 allowlist、参数模式、工作目录 | 未声明则拒绝 |
| 网络访问 | 目标域名、协议、认证来源 | 未声明则拒绝 |
| 凭证访问 | 环境变量名、用途、最小权限 | 未声明则拒绝 |

策略文件可使用 `templates/security/tool-call-policy.md` 记录。若 server 需要动态扩权，必须先更新声明、再重新执行 build/apply dry-run。

## 5. Runtime Trust Boundary

- `OPENAI_BASE_URL`、`ANTHROPIC_BASE_URL` 或同类 provider relay 只能指向已审查来源。
- 免费、临时、个人代理、未签名 relay 不得和写文件、执行命令、读取密钥类工具同时启用。
- LLM API 响应中的 tool call 不是权限来源；权限只来自本地声明和执行前 policy。
- 关键操作必须保留不可篡改摘要：tool name、args hash、cwd、允许原因、拒绝原因和退出码。

## 6. 阻断条件

- MCP server 需要读取密钥但没有说明凭证来源。
- MCP server 具备写文件或执行命令能力但没有用途边界。
- `manifest-fragments/mcp_servers.json` 与 `codex mcp list` 差异无解释。
- 试图绕过 `~/codex` 直接修改 `~/.codex/config.toml`。
- provider relay 或 base URL 未在 allowlist 中，却启用了工具调用。
- 高风险工具缺少执行前 policy、guard test 或拒绝样例。
