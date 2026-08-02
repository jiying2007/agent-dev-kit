# 需求基线：token-context-workflow-optimization-v1

## R1：风险分级而不是全流程默认升级

- 定义 `micro | standard | complex | high-risk` 四级任务成本模型。
- `micro` 允许 `no-skill`、默认不调用 Knowledge Hub、只跑定向验证。
- `standard` 最多加载一个 primary skill；只有项目事实或历史依赖时调用一次 Hub。
- `complex` 最多加载一个 primary 和一个 supporting skill，Hub 默认 `small + limit 3`。
- `high-risk` 保留原文回退、完整验证与 source-to-live 门禁，不以省 Token 为由降级。

## R2：累计固定上下文预算

- 预算必须覆盖层级累计，而不只检查单个 `AGENTS.md`。
- `~/codex` 全局入口、`llm_agent/AGENTS.md` 与 `agent-dev-kit/AGENTS.md` 的累计目标不超过 12,000 bytes。
- 规则入口只保留优先级、硬边界、路由和高频命令；详细示例与长流程下沉到已登记文档。
- 超预算时门禁失败，并报告每层字节数和累计值。

## R3：更窄的默认能力面与可靠路由

- `token-lean` 常驻 skill 从 20 项降到不超过 12 项；并行、worktree、branch/PR、资产治理和嵌入式专属能力延迟加载。
- `team-collab` 与专用 profile 保留完整能力，不删除 vendor 资产。
- Skill 检索必须支持合法 `zero-hit/no-skill`，并在通用仓/通用测试请求中抑制 embedded-only 候选。
- 默认返回候选数从 5 降到 3，summary 输出不超过 2,048 bytes；显式参数仍可在硬上限内扩大。

## R4：Knowledge Hub 按事件调用与有界输出

- Hub 预检只在首次进入目标、目标变化、项目事实/历史、debug、release、decision、validation 等需要长期证据的场景触发。
- 同一任务不串联执行 `map -> context -> search`；`context` 是默认单入口，只有歧义或低置信度才回退。
- 提供显式项目/范围提示，避免 cwd 与 query 路由冲突；显式范围无效时 fail closed。
- 只读或 telemetry 不可写环境不得输出冗长异常；支持自动/显式禁用 telemetry。
- `summary-json` 默认最多返回 3 条候选并满足 2,048-byte 预算，完整契约改由 evidence path 回退。

## R5：可用的 Token 观测

- Codex usage dashboard 必须兼容没有 `thread_goals` 表的旧/简化状态库，并明确报告该数据面 unavailable，而不是整体失败。
- 观测只保存计数、Token 数、字节、耗时、hash 和路由层级，不保存 prompt、query、日志正文或凭证。
- 至少能区分固定上下文、Skill/Hub 工具输出和重复门禁的成本；无法取得的字段显式为 unavailable。

## R6：门禁证据复用与 no-op 快路径

- 保留现有 same-run evidence 的 PID、root、fingerprint、producer hash 和 fail-closed 约束。
- Codex source-to-live 编排应复用同一 source/profile/target 的 build/doctor/plan receipt，避免 `check.sh` 再次无条件 build/plan。
- apply plan 为 `copy=overwrite=delete=0` 时允许报告 no-op；目录确保操作仍必须可审计。
- 根仓 smoke/quick 至少共享确定性的 runtime inventory，或明确输出不能复用的原因；不得伪造 reuse 数量。

## R7：有界成功输出与失败回退

- 成功默认只输出状态、计数、耗时、receipt/evidence 路径。
- 单个 summary 目标不超过 4 KiB；路由/Hub summary 目标不超过 2 KiB。
- 失败输出保留错误样本和原始证据路径；完整日志写临时或 change evidence，不直接注入对话。

## R8：验证与兼容

- 新增或修改行为必须有定向测试；不得弱化现有失败用例。
- `team-collab`、高风险原文门禁、Hub owner gate、memory/write/remote 边界不改变。
- Python 3.8 结果只作开发证据；release 结论需受支持 Python 环境。

## 非目标

- 不删除安全、权限、发布、owner 或 source-to-live 门禁。
- 不自动提升 Knowledge Hub `active`、不自动写 memory、不自动 commit/push/merge。
- 不把 Token 数作为质量或个人绩效 KPI。
- 不修改参考子仓、用户已有 dirty 内容或 `~/.codex` 手工文件。

## 验收指标

- 三级 ADK 规则累计 `<= 12,000 bytes`。
- `token-lean` active skill `<= 12`，默认 skill-search limit `= 3`、summary `<= 2,048 bytes`。
- 通用 Python 单测请求不再把 embedded-only skill 排在首位；微型 README 请求允许 zero-hit。
- 缺少 `thread_goals` 表时 usage summary/threads 仍返回有效 JSON。
- Hub context summary `<= 2,048 bytes`，显式 project/scope 路由有正负测试。
- root smoke 相同覆盖下目标 `<= 20s`，或提供 slowest/reuse 证据说明剩余瓶颈。
- Codex source-to-live 同一签名不重复 build/plan；no-op apply 可识别。

## 阻塞与停止条件

- 每阶段同一根因 retry budget 为 2；第三次前必须 replan。
- 任一目标仓 HEAD 或相关 dirty scope 改变即视为 stale，暂停整合验证。
- 需要删除资产、放宽权限或改变高风险 gate 语义时停止并请求新授权。
- stop condition：`pass | replan | split | blocked | abort`。
