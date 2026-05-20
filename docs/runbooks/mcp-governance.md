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
4. 声明暴露清单：tool/resource/prompt 名称、用途、输入 schema、输出 schema、幂等性和风险等级。
5. 为高风险工具写出执行前策略：哪些入参允许、哪些路径可读写、哪些命令必须拒绝。
6. 在 `~/codex` 合并前运行声明清单与实际清单差异检查。
7. 在 `~/.codex` apply 后运行：
   ```bash
   codex mcp list
   ```
8. 记录差异结论：新增、移除、参数变化、权限变化。

## 4. Production Readiness Gate

MCP server 进入生产 profile 前必须证明“已声明、可加载、可拒绝、可回滚”。

| Gate | 要求 |
|---|---|
| Protocol/schema | tool/resource/prompt schema 可被解析，必填字段和错误返回稳定 |
| Inspector/smoke | 有 `codex mcp list`、MCP inspector 或等价 smoke 证据 |
| Auth/scope | OAuth/API token scope 最小化，凭证来源和轮换方式明确 |
| Exposure inventory | 暴露清单与运行态加载结果一致，无隐藏工具 |
| Dependency boundary | 安装依赖、lock/version、网络下载和 native binary 风险已说明 |
| Guard tests | 至少一条 allow-path 和一条 deny-path 验证 |
| Audit/rollback | 高风险调用可审计，禁用步骤和恢复命令明确 |

## 5. Tool-call Policy

MCP 返回的工具调用请求一律视为不可信输入。允许执行前必须完成确定性检查，不依赖 LLM 自行判断。

| 风险面 | 必须声明 | 默认策略 |
|---|---|---|
| 文件读取 | 允许目录、禁止目录、最大文件大小 | 未声明则拒绝 |
| 文件写入 | 允许路径、覆盖规则、备份或 dry-run | 未声明则拒绝 |
| 命令执行 | 命令 allowlist、参数模式、工作目录 | 未声明则拒绝 |
| 网络访问 | 目标域名、协议、认证来源 | 未声明则拒绝 |
| 凭证访问 | 环境变量名、用途、最小权限 | 未声明则拒绝 |

策略文件可使用 `templates/security/tool-call-policy.md` 记录。若 server 需要动态扩权，必须先更新声明、再重新执行 build/apply dry-run。

## 6. Runtime Trust Boundary

- `OPENAI_BASE_URL`、`ANTHROPIC_BASE_URL` 或同类 provider relay 只能指向已审查来源。
- 免费、临时、个人代理、未签名 relay 不得和写文件、执行命令、读取密钥类工具同时启用。
- LLM API 响应中的 tool call 不是权限来源；权限只来自本地声明和执行前 policy。
- 关键操作必须保留不可篡改摘要：tool name、args hash、cwd、允许原因、拒绝原因和退出码。

## 7. Plugin Promotion Boundary

普通 skill 只有在需要外部服务、MCP server、hook、长期后台进程、native 依赖或凭证时，才晋级为 plugin。晋级后必须独立声明：

- plugin manifest、owner、version、license、来源锚点和 review date。
- 包含的 skills/MCP/hooks/apps 清单及各自 profile 绑定。
- 安装、升级、禁用、回滚和 drift 检查命令。
- 生产启用前的 `~/codex` build / doctor / apply dry-run 证据。

## 8. 阻断条件

- MCP server 需要读取密钥但没有说明凭证来源。
- MCP server 具备写文件或执行命令能力但没有用途边界。
- `manifest-fragments/mcp_servers.json` 与 `codex mcp list` 差异无解释。
- 试图绕过 `~/codex` 直接修改 `~/.codex/config.toml`。
- provider relay 或 base URL 未在 allowlist 中，却启用了工具调用。
- 高风险工具缺少执行前 policy、guard test 或拒绝样例。
- MCP/plugin 缺少暴露清单、auth scope、inspector/smoke 证据或回滚步骤。
