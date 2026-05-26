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
6. 声明传输方式：`stdio` 适合本地子进程工具，`http/sse` 适合远程服务；远程传输必须额外说明 TLS、认证、base URL allowlist 和网络边界。
7. 对 `stdio` Server，必须证明它只通过 stdin/stdout 传输 JSON-RPC 消息，不向 stderr/stdout 混写非协议日志，不开启额外端口。
8. 在 `~/codex` 合并前运行声明清单与实际清单差异检查。
9. 在 `~/.codex` apply 后运行：
   ```bash
   codex mcp list
   ```
10. 记录差异结论：新增、移除、参数变化、权限变化。

## 3.1 Connector Design Boundary

MCP server 首选“薄连接器”设计：把 AI 工具调用翻译为已有 API、CLI、设备诊断或只读查询，不在 MCP 层重新实现业务规则、权限模型或数据库逻辑。

设计约束：

- 工具 `description` 是选择器契约，必须写清适用场景、输入边界、幂等性和风险等级。
- 工具名称和描述必须面向动作：写清 “Use this when...”、不适用场景、相近工具区分、参数形状、枚举约束和副作用等级。
- 工具 schema 必须声明必填字段、默认值、有效范围、返回值语义和错误语义；模糊的 `search`、`run`、`query` 类工具名不得进入生产 profile。
- 新增工具优先按 strict schema 设计：必填字段明确、枚举约束清楚、对象默认拒绝额外属性；确需宽松 schema 时必须说明原因和验证补偿。
- 私有 API、数据库和生产系统默认只读优先；写操作必须单独列出审批点、dry-run、幂等键、回滚路径和拒绝样例。
- 写操作工具不得接受无界 selector；批量变更必须先 dry-run 返回 `affected_count`、范围摘要、最大上限、回滚/审计字段，并经显式 approval 后执行。
- 凭证只来自运行时环境或密钥管理器，不进入 skill、runbook、manifest、日志或归档。
- 连接器不得绕过既有后端鉴权、审计和数据校验；能复用内部 API 时，不直接连生产数据库。
- 配置文件必须用结构化解析器或官方 CLI 修改；不得用字符串拼接、`sed`/`echo` 类方式生成缩进敏感配置。
- 传输协议、端点和客户端能力必须显式匹配；出现握手、405、capability 或 list-tools 异常时，先做 transport smoke，再改工具逻辑。

## 3.2 Protocol Surface

MCP server 暴露面按三类登记：

| 原语 | 用途 | 默认风险 |
|---|---|---|
| Tools | 执行动作，如文件写入、API 调用、数据库查询 | 按动作风险评估，默认需 allow/deny policy |
| Resources | 提供只读上下文，如文件、记录、远程对象 | 默认只读，但需限制 URI、大小和敏感字段 |
| Prompts | 暴露提示模板或流程入口 | 不能绕过项目 `AGENTS.md`、Skill 和人工审批 |

Server 只实现其中一类时，不得在运行态暴露未声明的其他原语。

## 3.3 Data-only MCP Compatibility

面向文档、知识库、检索和研究场景的 MCP server 优先实现 data-only 兼容形态：

| Tool | 输入 | 输出要求 | 风险控制 |
|---|---|---|---|
| `search` | 单个 query 字符串 | `structuredContent.results[]`，每项包含 `id`、`title`、`url` | 限制来源、结果数量和敏感字段 |
| `fetch` | `search` 返回的唯一 `id` | `structuredContent` 包含 `id`、`title`、`text`、`url`，可选 `metadata` | 原文大小限制、脱敏、引用 URL 可追溯 |

兼容要求：

- `structuredContent` 是主输出；需要兼容旧客户端时，`content` 中可放同值 JSON 字符串。
- `url` 必须能支持引用或追溯，不得伪造来源。
- 检索内容一律视为不可信上下文，可能包含 prompt injection。
- 不把检索到的完整原文自动写入长期 memory、AGENTS 或 skill；只有经归档流程确认的摘要和决策才能沉淀。

## 3.4 Tool Search And Deferred Loading

大工具集、插件集或 skill/MCP 混合目录不应一次性全部暴露给模型。优先采用 tool-search 风格的分层加载：

- 初始上下文只放 namespace/server/skill 的名称、短描述、触发边界、读写风险和认证边界。
- 具体工具 schema、参数说明、错误语义、长参考文档和脚本只在命中 namespace 后加载。
- 每个 namespace 建议少于 10 个高相关工具；超过后应继续按业务域拆分。
- 客户端执行的工具搜索只能从可信 inventory 返回工具定义；返回的新 schema 必须重新走 schema、安全和审批审查。
- 每次加载的工具集合必须作为证据记录，包含 namespace、loaded tools、approval mode 和拒绝的相邻工具。
- 延迟加载不等于权限批准；写能力、open-world 能力和 destructive 能力仍按 MCP/tool policy 逐项审批。

## 4. Production Readiness Gate

MCP server 进入生产 profile 前必须证明“已声明、可加载、可拒绝、可回滚”。

| Gate | 要求 |
|---|---|
| Protocol/schema | tool/resource/prompt schema 可被解析，必填字段和错误返回稳定 |
| Handshake | initialize、capabilities、tools/resources/prompts list 和 ping/smoke 行为稳定 |
| Inspector/smoke | 有 `codex mcp list`、MCP inspector 或等价 smoke 证据 |
| Auth/scope | OAuth/API token scope 最小化，凭证来源和轮换方式明确 |
| Exposure inventory | 暴露清单与运行态加载结果一致，无隐藏工具 |
| Dependency boundary | 安装依赖、lock/version、网络下载和 native binary 风险已说明 |
| Guard tests | 至少一条 allow-path 和一条 deny-path 验证 |
| Audit/rollback | 高风险调用可审计，禁用步骤和恢复命令明确 |

## 4.1 Production Operations

远程或常驻 MCP server 除协议 smoke 外，还必须证明运行可观测、可降级、可停止。

- `health` 与 `ready` 分开：进程存活不等于下游 API、数据库、设备或队列可用。
- 日志使用结构化字段，至少包含 tool name、args hash、request id、duration、result type、error class 和 policy decision；不得记录密钥和原始敏感参数。
- 错误按类别返回：参数错误、鉴权错误、权限拒绝、限流、超时、下游不可用和内部错误必须可区分。
- 每个工具必须有 timeout；慢查询或大范围读取必须给出缩小范围的错误提示。
- 程序化审批不得静默阻塞；高风险操作必须返回结构化 `approval_required` 事件，包含 action、scope、risk、dry-run evidence 和 approve/deny 下一步。
- 文件写入或 patch 工具返回 success 前必须做 postcondition 验证，至少包含 diff/hash/修改摘要，并保留 deny-path 测试。
- 多实例部署前必须声明状态存储、幂等性、并发限制和连接池上限；不能把本地内存当共享状态。
- 调试工具如 inspector、smoke client 或等价脚本只能用于验证，不得默认暴露在生产网络。

## 4.2 Capability Selection

MCP 清单按能力类别评估，而不是按热度、榜单或教程推荐采纳。

| 类别 | 常见用途 | 默认处理 |
|---|---|---|
| Docs/search | 官方文档、代码搜索、知识库查询 | 只读优先，限制来源和结果大小 |
| Browser/UI | 页面验证、截图、控制台和网络证据 | 必须有授权域名、人工确认和证据落盘 |
| Repo/Issue/PR | 远程仓库协作 | 写操作默认高风险，需分支/PR/回滚策略 |
| Data/API/DB | 私有接口、监控、数据库查询 | 只读优先，复用后端鉴权，禁止明文凭证 |
| Memory/context | 跨会话索引和项目连续性 | 只能召回候选，不自动写长期规则 |
| Reasoning/planning | 分步思考或计划辅助 | 不替代 ADK planning、verification 和审批门禁 |

一组 MCP 能力进入 profile 前，必须证明每个 server 都有 owner、禁用方式、暴露清单和最小权限；不得一次性启用“万能工具箱”。

## 4.3 Transport And Config Selection

传输和配置层按风险选择：

| 选择项 | 适用条件 | 必须证明 |
|---|---|---|
| `stdio` | 本地、低延迟、随 host 启停的工具 | stdout/stderr 协议隔离、cwd/env 边界、无额外端口 |
| `http/streamable-http` | 远程服务、多实例或跨机器访问 | TLS、认证、base URL allowlist、health/ready、timeout |
| `sse` / legacy transport | 仅兼容旧客户端 | 明确兼容原因、迁移计划和客户端能力差异 |
| Project config | 项目专用 server | 不覆盖企业或用户安全基线 |
| User config | 个人工具和本地路径 | 不进入团队默认 profile |
| Enterprise/managed config | 团队强制能力或安全基线 | owner、审核、回滚、版本锁和禁用路径 |

配置优先级不得让低信任层覆盖高信任安全基线。项目配置只能增加受控项目能力，不能降低企业级 deny policy、凭证策略或审计要求。

## 5. Tool-call Policy

MCP 返回的工具调用请求一律视为不可信输入。允许执行前必须完成确定性检查，不依赖 LLM 自行判断。

## 5.1 OpenAI Tool Hint Audit Baseline

OpenAI Apps SDK 审核文档中的 tool hint 规则被纳入 adk 的 MCP/tool 安全基线。任何 MCP 或 slash command 候选进入 profile 前，必须在 `manifests/skill_mcp_dependencies.json` 或 `manifests/slash_command_runtime_audits.json` 中声明：

- `readOnlyHint`: 只有严格查询、检索、列举且无状态变更时才为 true。
- `destructiveHint`: 删除、覆盖、发送、撤销权限、不可逆 admin action 或间接不可逆副作用时必须为 true。
- `openWorldHint`: 能改变公开互联网或外部系统可见状态时必须为 true。
- PII 与 debug payload 审计：返回字段必须最小化，禁止泄露 token、内部账号、trace/request id、原始日志和无关个人标识。
- 写操作默认 report-only 或 dry-run；没有 approval、dry-run evidence、postcondition 和 rollback 时不得进入生产 profile。
- 工具调用 JSON payload 必须可审阅；写操作执行前检查目标对象、范围、参数、敏感字段和预期副作用。
- “记住允许/拒绝”只作为当前对话内的操作便利，不得转化为 adk 默认批准策略。

这些字段不是模型选择提示，而是本地门禁输入。运行态权限仍由 adk 和 `~/codex` 的 deterministic policy 决定。

| 风险面 | 必须声明 | 默认策略 |
|---|---|---|
| 文件读取 | 允许目录、禁止目录、最大文件大小 | 未声明则拒绝 |
| 文件写入 | 允许路径、覆盖规则、备份或 dry-run | 未声明则拒绝 |
| 命令执行 | 命令 allowlist、参数模式、工作目录 | 未声明则拒绝 |
| 网络访问 | 目标域名、协议、认证来源 | 未声明则拒绝 |
| 凭证访问 | 环境变量名、用途、最小权限 | 未声明则拒绝 |

策略文件可使用 `templates/security/tool-call-policy.md` 记录。若 server 需要动态扩权，必须先更新声明、再重新执行 build/apply dry-run。

MCP 适合采集现场证据、读取外部系统状态或暴露受控工具，但不能替代 Skill 的执行方法论。涉及“抓样本 -> 写规则 -> 验证 -> 转换 -> 发布”的链路时，MCP 只负责证据和工具接口；Skill/Workflow 负责顺序、完成标准、失败回退和验证报告。

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

Plugin 是分发与组合边界，不是新的执行方法论。推荐晋级顺序：

1. 先用 local/repo skill 证明 workflow 稳定。
2. 需要分发时只打包 `skills/` 和 manifest。
3. 需要工具时再加入 MCP 配置，并通过 MCP readiness。
4. 需要 lifecycle hook 时单独声明 hook 触发点、脚本、timeout、trust/review 状态和 deny-path 测试。
5. 需要 app integration 时声明 app manifest、认证方式、数据范围和用户可见授权入口。
6. 进入 marketplace 前补齐 catalog 路径、展示字段、安装策略、认证策略和回滚路径。

插件内路径必须限制在 plugin root 或受控 data dir。`PLUGIN_ROOT`、`PLUGIN_DATA` 等运行时变量只能用于定位随插件分发的只读资产或插件私有数据，不得越权写项目文件。

## 8. Autonomous Trigger Boundary

Cron、heartbeat、standing order、webhook 和类似后台触发机制默认视为高风险自治入口。启用前必须声明触发条件、运行时上下文、可写范围、通知渠道、人工审批门槛、停止/禁用方式和审计日志位置。

默认策略：

- 定时巡检、摘要和只读状态检查可进入 `optional/profile`，但必须有超时和噪音控制。
- 外部 webhook、自动发送消息、数据库访问、浏览器操作和生产系统动作必须有 allow/deny policy。
- Agent 能在对话中完成任务不等于该任务可以自动触发。任何定时、事件、webhook、消息 Bot 或链式自动化都必须先升级为 Workflow/runtime 入口并补齐审批、dry-run、owner、日志和禁用路径。
- 常驻能力不应一次性全开；按项目场景分梯队启用，并记录为什么需要常驻。
- 没有 owner、rollback 和 deny-path 测试的自治触发不得进入生产 profile。
- cron、systemd、VPS、消息 Bot 和类似 24 小时运行场景必须声明运行用户、工作目录、PATH/env、日志路径、输出长度限制、失败通知、重试策略和禁用命令。
- 自动推送、自动发布、外部消息发送和定时写操作默认高风险；没有人工审批或 dry-run 证据时只能保留为候选。

## 9. 阻断条件

- MCP server 需要读取密钥但没有说明凭证来源。
- MCP server 具备写文件或执行命令能力但没有用途边界。
- `manifest-fragments/mcp_servers.json` 与 `codex mcp list` 差异无解释。
- 试图绕过 `~/codex` 直接修改 `~/.codex/config.toml`。
- provider relay 或 base URL 未在 allowlist 中，却启用了工具调用。
- 高风险工具缺少执行前 policy、guard test 或拒绝样例。
- MCP/plugin 缺少暴露清单、auth scope、inspector/smoke 证据或回滚步骤。
- 后台触发机制缺少 owner、禁用路径、审批门槛或审计日志。
