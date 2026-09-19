# Token Context Governance Runbook

## 目标

保真省 Token 的目标不是少看信息，而是少读噪音、保留证据、必要时回退原文。任何压缩摘要都必须能回答三个问题：原文在哪里、置信度多少、什么情况下继续读原文。

## 读取层级

| Tier | 默认场景 | 证据要求 |
|---|---|---|
| L0 | 新项目认知、入口定位 | `PROJECT_MAP.md`、目录摘要、测试入口 |
| L1 | 低风险 bug、局部改动、常规日志 | 摘要 + `raw_evidence` + `confidence` |
| L2 | 测试失败、接口变化、根因未明 | 局部原文窗口、调用方、关键 diff、错误栈 |
| L3 | 高风险任务或交付争议 | 完整原文、完整日志、完整 diff |

## Task Cost 路由

读取 Skill 或 Hub 前先按 `templates/context/task-cost-profile.md` 判定 `task_cost`：

- `micro`：一行文档、局部机械修改、明确的小测试；不加载 skill、不查 Hub，直接定向验证。
- `standard`：单模块常规改动；最多一个 primary skill，只有项目事实相关时做 Hub 预检。
- `complex`：跨文件、根因未明、共享契约或长任务；一个 primary skill，small Hub 预检，计划与阶段验证。
- `high-risk`：安全、权限、迁移、生产、发布；L2/L3 原文、完整 gate、审批和回滚，Token 预算不得弱化证据。

判级先于关键词匹配；零命中允许 micro/standard 直接执行。supporting skill 只补充主流程，不重复加载相邻工作流。

## 变换层边界

原始材料不随摘要改写或销毁。上下文优化只改变“本轮发送给模型的内容”，完整日志、diff、文章、命令输出或审查证据必须通过 `raw_evidence` 可回读。若摘要与原文冲突，以原文和可复跑命令为准。

长期知识采用按需加载：先读 L0 索引或项目地图，再读 L1 摘要，只有在风险、置信度或验收需要时进入 L2/L3。不得因为已有摘要就跳过调用方、测试、权限条件、迁移日志或签名字段。

依赖图、调用图、代码地图或 review graph 可以作为 `scope_read` 候选来源，但不能替代源码审查。使用这类索引时必须记录生成时间、语言/目录覆盖范围、已知漏报风险和 raw fallback；高风险改动仍需回读调用方、测试、配置和权限边界。

## 增量压缩与保护边界

长线程摘要优先采用 incremental compression：先处理新增片段，再更新对应阶段摘要；不得等上下文接近上限后做一次性 whole-context compression。任何压缩层都必须保留 `raw_evidence`、`confidence`、`fallback_condition` 和 stable key，避免摘要层之间失去可追溯身份。

进入摘要前先做 deterministic pre-filter。寒暄、确认、分隔符、重复工具输出和重复文件读取可以折叠；用户纠正、明确决策、任务进度、执行日志、路径/API 变更和未完成任务不得被噪音过滤吞掉。若保护条目与去重或摘要冲突，优先保留保护条目的原文入口，并把冲突写入 excluded context 或风险台账。

压缩摘要不得只留下结论。每个阶段摘要至少说明：本阶段目标、已完成动作、未闭环风险、被保护条目、失效旧目标、下一步读取层级和原文回退入口。若摘要无法回答这些问题，必须回退 L2/L3，而不是继续叠加摘要。

## Memory Search 渐进披露

`memory-search-progressive-disclosure-v1` 只作为只读检索能力落地，不启用外部 worker、hook、本地 HTTP 服务、向量数据库写入或自动记忆采集。默认流程按 `search_index -> timeline_context -> observation_details` 逐层披露，任何长期记忆写入仍需单独的 owner review、脱敏状态和可回滚证据。

1. `search_index`：先用紧凑索引回答“有哪些候选记忆”。只返回 `query`、`result_ids`、`time_window`、`project_scope`、`observation_type`、`redaction_status` 和 `raw_fallback`，不得把全部历史 observation 注入上下文。
2. `timeline_context`：仅对选中的 `result_ids` 或严格收窄后的查询读取时间线。时间线只保留日期、项目、事件摘要、相关证据入口和缺口，不展开原始工具输出。
3. `observation_details`：只有在实现、审查、排障或交接确实需要时才按 ID 批量读取详情，并记录 `detail_fetch_reason`。详情读取仍必须保留 raw fallback，且不能把摘要当作主证据。
4. 原文回退：当摘要与源码、日志、diff、测试或用户最新目标冲突时，以原始证据和可复跑命令为准；缺少证据路径的 memory hit 只能作为候选线索。
5. 写入边界：长期记忆、新增 archive、提升为 guidance 或修改 memory store 都不是 memory search 的默认副作用，必须走对应审查流程。

检索结果使用 `templates/context/memory-search-result.md`。若需要进一步读取详情，先补齐 `detail_fetch_reason`；若结果包含敏感内容，先记录 `redaction_status`，再决定是否进入 L2/L3。

## Context Rot 防护

长任务不得依赖单一长会话硬扛上下文。推荐采用轻量编排器模式：

- 主 Agent 只保留目标、状态、任务契约、风险和汇总证据，不读取全量源码、日志和历史讨论。
- 子任务使用窄上下文执行，只接收 `scope_read`、`scope_write`、`must_not_touch`、done criteria 和验证命令。
- 阶段状态写入文件，如 `PROJECT.md`、`REQUIREMENTS.md`、`PLAN.md`、`STATE.md`、`SUMMARY.md` 或项目等价物；文件是跨会话记忆，不把完整聊天当记忆。
- 同一阶段内可按依赖拆成 wave 执行；跨 wave 只传递结构化结果和未解决风险。
- 发现上下文腐烂信号，如重复旧错误、忘记约束、重写已删除代码或无根据扩大范围时，停止执行并重建阶段摘要。
- 主上下文出现 `CTX_PRESSURE` 或持续增长时，优先归档状态并新开窄任务，不继续堆叠日志和 diff。
- 每个子任务上下文包必须满足 single、specific、short、testable：一个目标、明确 scope、短摘要、可验证输出。当前轮必须自包含目标、约束、证据入口和验证命令，不依赖若干轮之前的对话历史作为隐式状态。

会话分叉按 context health 和任务连续性选择动作：

- 同一任务且上下文仍干净时继续执行。
- 失败尝试、错误日志或错误方案污染上下文时，回到最近的有效证据点，并只携带失败教训和禁止路径。
- 上下文重启或 resume prompt 必须携带失败路径、已排除方案和当前假设；重复尝试同一路径时必须说明本次差异。
- 新任务、高精度修改或完成前审查优先用人工 brief / resume prompt 开新窄上下文。
- 中间输出很多但只需要结论的调研、验证和对比任务交给子任务；父上下文只接收结论、风险和证据入口。
- 自动摘要或压缩前必须说明下一步目标；没有目标的压缩只能作为归档摘要，不能替代执行上下文。

## 上下文预算模式

使用 `templates/context/context-budget-profile.md` 为每个中大型任务记录 `task_type`、`risk_level`、`budget_profile`、`read_tier`、`compress_allowed`、`raw_required`、`raw_evidence` 和 `fallback_condition`。

| 模式 | 适用场景 | 默认策略 |
|---|---|---|
| 极速 | 扫仓、入口定位、候选文件发现 | L0/L1，激进压缩，必须保留原文入口 |
| 均衡 | 日常编码、低中风险 bug | L1/L2，摘要先行，关键窗口回读 |
| 精确 | 根因未明、接口变化、代码 review | L2，少压缩，多读调用方、测试和配置 |
| 审计 | 安全、权限、支付、迁移、生产事故 | L3，不压缩结论证据，只做去重、排序或脱敏 |

简化规则：粗看开压缩，精看限压缩，审计看原文。出现 `HOT`、`CTX_PRESSURE`、阶段切换或目标切换时，先产出交接摘要，再用预算配置限制下一阶段只读取必要证据。

## Low Token Profile

`low-token-communication-profile-v1` 是通信 profile，不是证据压缩豁免。触发条件包括用户明确要求低 token、上下文压力告警、只需状态更新或短战术答复。启用时使用 `templates/context/low-token-profile.md` 记录 `trigger`、`active_scope`、`technical_terms_preserved`、`safety_exception`、`restore_condition` 和 `user_override`。

低 token 输出可以减少寒暄、背景复述和重复过程，但不得移除命令、路径、来源、风险、验证证据、阻塞条件或不确定性。中文技术回答必须保留精确英文术语、文件名、字段名和错误码。

以下安全例外必须临时恢复完整清晰表达：

- `security warning`：安全、凭证、权限、隐私、供应链或生产风险告警。
- `irreversible action confirmation`：删除、覆盖、发布、迁移、reset、清理、提交历史重写等不可逆或难回滚动作确认。
- `multi-step ambiguity`：多步骤指令压缩后会增加歧义、顺序误解或审批边界不清。
- `review finding precision`：代码审查发现需要精确文件、行号、行为链路、证据和影响说明。

用户可以用显式要求退出低 token profile；进入高风险任务、需要审查证据、发生歧义或需要教学解释时，也应按 `restore_condition` 自动恢复正常表达。

## 运行中 Token 监测

静态 `token-budget` 负责资产体积，`task-cost` 负责执行前预算；运行期 Goal、Token、context、
progress 和完成门禁统一进入 `runtime_control.event/v1`。usage 只允许累计 snapshot，cached input
是 input 子集，total 必须等于 input + output。唯一 Engine 同时判断 checkpoint、compact、stop、
replan 和 pass，任何 runtime adapter 或阶段 gate 都不得复制阈值和动作优先级。

事件只能包含计数、稳定 ID、时间、hash 和低敏 model 标签。prompt、objective、messages、content、
raw input/output 不得进入 journal/state。Engine 是 pure reducer/decision；副作用继续由 runtime
按 approval/sandbox 边界执行。

## 可压缩对象

- 只读命令：`git diff`、`git status`、`git log`、`rg`、目录清单。
- 测试与服务日志：优先 `pytest -q`、`npm test -- --runInBand`、`docker logs --tail 100`。
- 大 JSON 或结构化输出：先抽关键字段，再保留原始文件路径。

## 不得压缩代替审查

- 写操作、删除、移动、部署、数据库写入和生产变更命令。
- 安全审计、权限系统、支付逻辑、数据库迁移、生产事故、协议兼容、加密签名和性能瓶颈分析。
- 摘要缺少错误栈、迁移日志、调用方、权限条件、金额单位或签名字段时，必须回退 L2/L3。

## 证据保留

使用 `templates/context/tool-output-summary.md` 记录摘要，使用 `templates/context/raw-evidence-index.md` 登记完整材料。敏感日志先脱敏，密钥、账号和隐私内容不得写入长期归档。

## OpenAI Reasoning Guidance 对齐

面向 GPT-5 系列 reasoning model 的上下文包按“稳定在前、动态在后”组织，以提高提示缓存命中和降低重复上下文成本。稳定内容包括目标、仓库规则、skill 契约、验证命令和长期决策；动态内容包括用户本轮输入、最新 diff、命令输出、失败样本和未闭环阻塞。

长任务压缩必须保留：

- 已完成动作和可复跑证据。
- 当前假设、运行 ID、文件路径、工具结果和退出码。
- 未解决 blocker、被排除方案和下一步具体目标。
- 最新用户目标与已失效目标必须分开记录，避免旧计划覆盖新请求。
- 多问题会话必须拆成 per-issue mini summary，分别记录状态、证据和下一步。
- 错误事实、失败路径和被证伪假设必须进入 excluded context 或风险台账，不得混入 active plan。
- 如果手动传回 Responses 状态或等价运行状态，必须保留阶段/phase 语义，不得把中间输出压成只有自然语言结论。

工具说明优先下沉到 tool、MCP、skill 或 manifest 描述：工具做什么、何时使用、必填输入、副作用、重试安全和常见错误。只有跨工具通用策略才进入系统级或 AGENTS 级规则。

## 预算分配建议

| 任务类型 | project_map | search | source | logs | diff | docs |
|---|---:|---:|---:|---:|---:|---:|
| exploration | 30 | 30 | 20 | 10 | 0 | 10 |
| bugfix | 10 | 15 | 40 | 25 | 5 | 5 |
| review | 5 | 10 | 20 | 10 | 45 | 10 |
| audit | 5 | 5 | 35 | 20 | 25 | 10 |
| handoff | 20 | 10 | 20 | 10 | 20 | 20 |

比例用于指导上下文打包，不是硬性配额；高风险项始终优先满足原文证据。

## 项目索引

长期项目维护 `templates/context/project-map.md` 的落地副本。只记录入口、测试、禁读目录、高风险区域、常见坑和 `Last Verified`，避免把一次性日志写成长期事实。

项目索引和上下文文档应作为“交接入口”，不是百科全书。适合记录目标、入口、验证命令、禁读目录、当前状态和未闭环风险；不适合保存完整聊天、营销信息、过期趋势或未验证工具 claims。

项目地图和上下文文件必须短小、分层、按需加载。需要更多背景时先引用原文入口或局部证据窗口，而不是把全仓源码、完整历史会话或多篇教程粘贴进默认上下文。

长期项目 wiki、context map 或知识库必须分离 immutable raw sources、generated summaries、schema/rules 和 index/log。自动摄入、摘要或查询前必须能检查矛盾条目、孤立页面、过时断言和缺失来源；未通过人工确认的自动生成内容只能作为候选摘要，不得覆盖原始证据。

上下文工具化按轻到重升级：项目地图和阶段摘要先行，仍无法支撑跨会话连续性时再考虑外部 continuity pack 或 historical search。外部工具的 MCP、hook、embedding、数据库和配置写入保持 `report-only`，直到供应链和运行态权限审查完成。

切换或升级模型前必须做任务本地回归，覆盖工具调用、长上下文、权限扩大和擅自执行风险。模型能力提升不能替代 deterministic gate、approval gate 或原文证据回读。

## Session Memory 质量门禁

面向长线程、恢复线程和跨 agent handoff，压缩结果必须满足 `manifests/context_state_contracts.json`：

- `stable`：目标、仓库规则、验证命令、长期决策和工具契约。
- `dynamic`：本轮用户输入、最新 diff、命令输出、失败样本和阻塞。
- `evidence`：原文路径、source URL、命令、退出码、artifact 或可复跑报告。
- `excluded`：过期计划、错误结论、被证伪假设、不得重复的失败路径。

压缩前先确认下一步目标；压缩后必须能回答：最新目标是什么、哪些旧目标已失效、哪些事实来自证据、什么条件下回读原文。

## 验证

```bash
scripts/check-token-budget.sh
scripts/check-context-experience-patterns.sh
scripts/devkit.sh validate --strict
tests/test_token_budget.sh
tests/test_execution_policy.sh
```
