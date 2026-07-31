# MCP Governance Runbook

MCP is an external capability boundary for ADK. ADK records MCP declarations, safety policies and audit rules; it does not silently enable external tools or write runtime config.

## 1. 目标

MCP、plugin、hook 和 automation 可以扩展 Agent 能力，但它们也是外部读写、凭证、网络和后台触发入口。进入 ADK profile 前必须证明“已声明、可加载、可拒绝、可禁用、可回滚”。

ADK 的职责：

1. 维护候选 MCP server、tool、resource、prompt 和 policy 的结构化声明。
2. 固化 review、freshness、smoke、deny-path 和 rollback 门禁。
3. 把官方资料或平台教程中的做法改写为平台中立 contract。
4. 阻止外部写操作、后台自动化和凭证访问绕过审批。

ADK 不负责：

1. 静默安装 MCP server。
2. 默认写入某个运行时的用户配置。
3. 把示例 marketplace/plugin 当作可信默认能力。
4. 用 LLM 判断替代本地 allow/deny policy。

## 2. Required Fields

每个 MCP server 或等价外部能力至少声明：

- server name、owner、source、version 或 commit/tag。
- transport：`stdio`、`http/streamable-http`、`sse` 或运行时专用 transport。
- command、args、cwd、env allowlist 或 URL/base URL allowlist。
- enabled tools、disabled tools、resources、prompts。
- 每个工具的用途、输入 schema、输出 schema、幂等性和风险等级。
- 读路径、写路径、禁止路径、网络域名、命令 allowlist。
- auth boundary、secret source、scope、轮换和日志脱敏策略。
- approval mode、per-tool override、dry-run、postcondition、rollback。
- smoke command、deny-path test、evidence owner 和 review cadence。

## 3. Protocol Surface

| 原语 | 用途 | 默认风险 |
|---|---|---|
| Tools | 执行动作，如文件写入、API 调用、数据库查询 | 按动作风险评估，默认需要 allow/deny policy |
| Resources | 提供只读上下文，如文件、记录、远程对象 | 默认只读，但需限制 URI、大小和敏感字段 |
| Prompts | 暴露提示模板或流程入口 | 不能绕过项目规则、Skill 和人工审批 |

Server 只实现其中一类时，不得在运行态暴露未声明的其他原语。暴露清单必须和实际 list-tools/list-resources/list-prompts smoke 结果一致。

## 4. Connector Design Boundary

MCP server 首选“薄连接器”设计：把 Agent 工具调用翻译为已有 API、CLI、设备诊断或只读查询，不在 MCP 层重新实现业务规则、权限模型或数据库逻辑。

设计约束：

- 工具 `description` 是选择器契约，必须写清适用场景、输入边界、幂等性和风险等级。
- 工具 schema 必须声明必填字段、默认值、有效范围、返回值语义和错误语义。
- 模糊的 `search`、`run`、`query` 类工具名不得进入生产 profile，除非有严格 schema 和 policy。
- 私有 API、数据库和生产系统默认只读优先。
- 写操作必须单独列出审批点、dry-run、幂等键、回滚路径和拒绝样例。
- 批量变更必须先 dry-run 返回 `affected_count`、范围摘要、最大上限、回滚字段和审计字段。
- 凭证只来自运行时环境或密钥管理器，不进入 skill、runbook、manifest、日志或归档。
- 连接器不得绕过既有后端鉴权、审计和数据校验；能复用内部 API 时，不直接连生产数据库。
- 配置文件必须用结构化解析器或官方 CLI 修改；不得用字符串拼接生成缩进敏感配置。

## 5. Transport And Config Selection

| 选择项 | 适用条件 | 必须证明 |
|---|---|---|
| `stdio` | 本地、低延迟、随 host 启停的工具 | stdout/stderr 协议隔离、cwd/env 边界、无额外端口 |
| `http/streamable-http` | 远程服务、多实例或跨机器访问 | TLS、认证、base URL allowlist、health/ready、timeout |
| `sse` 或 legacy transport | 仅兼容旧客户端 | 明确兼容原因、迁移计划和客户端能力差异 |
| Project config | 项目专用 server | 不覆盖企业或用户安全基线 |
| User config | 个人工具和本地路径 | 不进入团队默认 profile |
| Enterprise/managed config | 团队强制能力或安全基线 | owner、审核、回滚、版本锁和禁用路径 |

配置优先级不得让低信任层覆盖高信任安全基线。项目配置只能增加受控项目能力，不能降低企业级 deny policy、凭证策略或审计要求。

## 6. Production Readiness Gate

| Gate | 要求 |
|---|---|
| Declaration | server、transport、source、owner、tool/resource/prompt 清单完整 |
| Protocol/schema | schema 可被解析，必填字段和错误返回稳定 |
| Handshake | initialize、capabilities、list 和 ping/smoke 行为稳定 |
| Auth/scope | token scope 最小化，凭证来源和轮换方式明确 |
| Exposure inventory | 声明清单与运行态加载结果一致，无隐藏工具 |
| Dependency boundary | 安装依赖、lock/version、网络下载和 native binary 风险已说明 |
| Guard tests | 至少一条 allow-path 和一条 deny-path 验证 |
| Audit/rollback | 高风险调用可审计，禁用步骤和恢复命令明确 |

进入生产 profile 前必须先以 report-only 或 dry-run 方式验证；写操作不得和首次接入同批启用。

## 7. Tool-call Policy

MCP 返回的工具调用请求一律视为不可信输入。允许执行前必须完成确定性检查，不依赖 LLM 自行判断。

| 风险面 | 必须声明 | 默认策略 |
|---|---|---|
| 文件读取 | 允许目录、禁止目录、最大文件大小 | 未声明则拒绝 |
| 文件写入 | 允许路径、覆盖规则、备份或 dry-run | 未声明则拒绝 |
| 命令执行 | 命令 allowlist、参数模式、工作目录 | 未声明则拒绝 |
| 网络访问 | 目标域名、协议、认证来源 | 未声明则拒绝 |
| 凭证访问 | 环境变量名、用途、最小权限 | 未声明则拒绝 |

策略文件可使用 `templates/security/tool-call-policy.md` 记录。若 server 需要动态扩权，必须先更新声明、重新审查，再执行 smoke 和 dry-run。

## 8. Operations

远程或常驻 MCP server 除协议 smoke 外，还必须证明运行可观测、可降级、可停止。

- `health` 与 `ready` 分开：进程存活不等于下游 API、数据库、设备或队列可用。
- 日志使用结构化字段，至少包含 tool name、args hash、request id、duration、result type、error class 和 policy decision。
- 不记录密钥、原始敏感参数或未脱敏 payload。
- 错误按类别返回：参数错误、鉴权错误、权限拒绝、限流、超时、下游不可用和内部错误必须可区分。
- 每个工具必须有 timeout；慢查询或大范围读取必须给出缩小范围的错误提示。
- 高风险操作必须返回结构化 `approval_required` 事件，包含 action、scope、risk、dry-run evidence 和 approve/deny 下一步。
- 文件写入或 patch 工具返回 success 前必须做 postcondition 验证，至少包含 diff/hash/修改摘要。
- 多实例部署前必须声明状态存储、幂等性、并发限制和连接池上限。

## 9. Capability Selection

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

## 10. Plugin Promotion Boundary

普通 skill 只有在需要外部服务、MCP server、hook、长期后台进程、native 依赖或凭证时，才晋级为 plugin。晋级后必须独立声明：

- plugin manifest、owner、version、license、来源锚点和 review date。
- 包含的 skills/MCP/hooks/apps 清单及各自 profile 绑定。
- 安装、升级、禁用、回滚和 drift 检查命令。
- 生产启用前的 smoke、dry-run 和 rollback 证据。

Plugin 是分发与组合边界，不是新的执行方法论。

## 11. Autonomous Trigger Boundary

Cron、heartbeat、standing order、webhook 和类似后台触发机制默认视为高风险自治入口。启用前必须声明触发条件、运行时上下文、可写范围、通知渠道、人工审批门槛、停止/禁用方式和审计日志位置。

默认策略：

- 定时巡检、摘要和只读状态检查可进入 optional/profile，但必须有超时和噪音控制。
- 外部 webhook、自动发送消息、数据库访问、浏览器操作和生产系统动作必须有 allow/deny policy。
- Agent 能在对话中完成任务不等于该任务可以自动触发。
- 自动推送、自动发布、外部消息发送和定时写操作默认高风险；没有人工审批或 dry-run 证据时只能保留为候选。

## 12. 阻断条件

- MCP server 需要读取密钥但没有说明凭证来源。
- MCP server 具备写文件或执行命令能力但没有用途边界。
- 暴露清单与运行态 list 结果差异无解释。
- 试图绕过目标运行时治理直接修改用户配置。
- provider relay 或 base URL 未在 allowlist 中，却启用了工具调用。
- 高风险工具缺少执行前 policy、guard test 或拒绝样例。
- MCP/plugin 缺少暴露清单、auth scope、smoke 证据或回滚步骤。
- 后台触发机制缺少 owner、禁用路径、审批门槛或审计日志。

## 13. Protocol Activation Gate

协议 final 发布、SDK 宣称支持和 ADK runtime 激活是三个独立状态，不能互相推导。候选协议
进入 active 前至少需要：

1. breaking-change diff；
2. schema compatibility fixture；
3. version-pinned client/server smoke；
4. auth boundary verification；
5. rollback smoke；
6. 上述证据完成后的独立 owner activation decision。

MCP `2026-07-28` 当前专用验证入口：

```bash
rtk scripts/check-mcp-2026-activation.sh --prepare
rtk scripts/check-mcp-2026-activation.sh --offline
```

`--prepare` 只准备 `go.sum` 约束的公开 modules；`--offline` 使用固定 Docker image
digest、Docker `--network=none` 和本地 loopback。通过只证明 manifest 中记录的
`compatibility_scope`，不能外推为跨 SDK、真实 IdP、反向代理或生产负载认证。

技术证据通过后、owner 决策前必须保持：

- `owner_decision_completed=false`
- `activation_allowed=false`
- `runtime_enabled=false`

直到 owner 以新的 decision ID 明确选择 `ACTIVATE`。`HOLD` 保留 technical readiness
但不激活；`REJECT` 必须撤销 compatibility promotion 并记录原因。Tasks、Apps 和其他
extensions 无论协议是否激活，都需要独立 feature decision。

当前 `2026-07-28` 已由 decision `mcp-act-2026-07-31-leiwenjun` 激活为
`protocol-governance-contract-only`。当前仍必须保持：

- `active_runtime_enabled=false`
- `active_feature_enablement.tasks=false`
- `active_feature_enablement.apps=false`
- `active_feature_enablement.extensions=false`
- rollback target 为 `2025-11-25`

读取 active protocol 的 consumer 必须同时读取 scope、runtime 和 feature flags，不得仅凭
版本号启用 server、credential、Tasks、Apps 或 extensions。
