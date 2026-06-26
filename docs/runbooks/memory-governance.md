# Memory Governance Runbook

## 目标

Agent 记忆只保存可复用经验，不保存噪声。任务结束后先做 After Action Review，再生成可审查的 memory candidate；是否写入长期位置由风险、作用域和人工确认决定。

## 四层记忆

| 层级 | 用途 | 默认处理 |
|---|---|---|
| `session` | 当前任务状态、临时 ID、已完成步骤 | 任务结束后通常丢弃或进入 session summary |
| `user` | 稳定偏好和明确授权 | 候选化后等待用户确认 |
| `project` | 项目结构、脚本入口、验证门禁、团队约定 | 优先写项目 runbook 或 `AGENTS.md` 候选 |
| `lesson` | 失败根因、负结果、成功路径和工具限制 | 写入 lessons、archive 或 skill/template 候选 |

不得保存完整聊天记录、临时草稿、过期价格、未经确认推测、密钥、凭据、隐私原文和只对本次任务有用的信息。

## 召回策略

记忆召回先读索引，再读候选摘要，最后才回读原始归档。每条长期记忆应能回答：适用范围是什么、依据来自哪里、何时最后验证、何时需要复核。无法给出来源和复核时间的内容只能进入会话摘要或归档，不进入默认行为规则。

从任务中沉淀经验时，只保存“下次同类任务会改变行为”的规则。工具名、榜单、一次性教程和未经供应链审查的安装命令不得升级为项目默认能力。

常驻记忆只放少量稳定事实、偏好和硬约束；历史会话、长日志和项目过程细节走按需搜索、摘要和原文回退。召回候选按来源可信度、相关性、重要性、时间衰减、访问频率和作用域共同排序，不能只按向量相似度或关键词命中决定是否注入上下文。

## 实现边界

记忆系统先做结构化治理，再选择存储技术。Markdown、JSONL、SQLite、FTS、向量库和外部 memory MCP 只是实现选项，不改变写入准入、风险分级和人工确认规则。

默认路线：

1. 先用可审计文件保存 `session`、`project` 和 `lesson` 候选。
2. 当候选数量大到人工检索低效时，再引入索引、全文检索或语义检索。
3. 语义检索结果只能作为召回候选，不能替代来源、置信度、复核时间和冲突检查。
4. 外部 memory server、embedding 服务或跨工具会话索引进入运行链路前，必须走 MCP 与供应链准入。

命名空间必须显式区分 `user`、`project`、`workflow`、`lesson` 和 `session`。不得把项目临时路径、一次性偏好、失败猜测或聊天原文写入用户长期记忆。

不同 Agent、profile、团队或项目的记忆、Skill、会话和凭据默认隔离。共享前必须声明 memory scope、access control、adapter parity 和 rollback/audit 证据；外部 memory provider、消息网关或共享会话索引在供应链和运行态审查前保持 `report-only`。

外部长期记忆层进入候选前，必须先写清 backend capability matrix：`data_model`、`query_mode`、`transaction_consistency`、`namespace_isolation`、`backup/rollback`、`audit` 和 `resource_cost`。数据库、向量、图谱、MCP 或跨工具索引的选型不能只依据教程、榜单或厂商能力声明；未完成 owner、license、版本锚点、凭据边界和回滚审查前保持 `report-only`。

backend capability matrix 还必须覆盖下列字段，避免把记忆产品或论文概念直接提升为运行时：

| 字段 | 必须回答的问题 |
|---|---|
| `temporal_strata` | 是否区分片段、会话、日报、周报、画像等时间层级；层级只影响检索候选，不得绕过证据审查。 |
| `lifecycle_model` | raw/research、engineering、archive 等状态如何流转；每次晋升需要哪些验证和回退证据。 |
| `retrieval_fusion` | 语义、关键词、时间、可信度、热度或图关系如何合成；必须返回命中理由和 raw fallback。 |
| `deterministic_pre_filter` | 写入或摘要前哪些噪音、纠正、决策、进度、执行日志信号由规则识别，而不是交给 LLM 自行判断。 |
| `identity_keys` | 计划、进度、决策、纠正和执行日志如何生成稳定 key；冲突时如何做 `ADD`、`UPDATE`、`DELETE` 或 `NONE` 判定。 |
| `graph_topology` | 图谱节点、边、孤立节点和过时关系如何维护；图谱只能辅助召回，不能替代来源证据。 |
| `offline_sync` | 离线缓存、端云同步和冲突合并的真相源、幂等性、审计日志与失败回滚方式。 |
| `purge_semantics` | 删除、降权、哈希化、墓碑和物理清除分别代表什么；hash-only tombstone 不能单独声明为合规删除。 |

长期记忆层必须区分 resident memory 与 retrievable memory。resident memory 只保留少量稳定规则和偏好；retrievable memory 负责历史事实、长会话、关系和证据召回。引入外部层前必须声明写入触发条件、召回融合与去重策略、token 裁剪规则、memory scope、备份路径和审计路径。

## 策略选择

不同记忆策略解决不同问题，不能用单一向量库替代治理：

| 策略 | 适用 | 风险 |
|---|---|---|
| 原始片段 | 需要完整事实、审计或复盘 | 体积大、含噪音，必须脱敏和限制召回 |
| 摘要 | 会话接力、长任务阶段压缩 | 可能丢关键细节，必须保留原文入口 |
| 事实抽取 | 用户偏好、项目规则、稳定约束 | 抽取错误会污染长期规则 |
| 向量检索 | 语义召回、跨文档候选发现 | 相似不等于正确，必须二次核对来源 |
| 关系图谱 | 依赖、接口、责任人和风险关系 | 维护成本高，缺少更新机制会快速过期 |

默认混合策略：短期任务保留结构化状态和必要原文入口；长期只保存事实抽取、失败教训和流程规则候选；语义检索只负责找候选，不负责直接改写行为。

记忆写入分两步：先从原始对话、日志或归档中抽取可审计 facts，再基于当前旧记忆和 new facts 做变更判定。判定事件必须是 `ADD`、`UPDATE`、`DELETE` 或 `NONE` 之一，并记录来源、旧值、冲突、风险和审计说明；不得把原始聊天、检索结果或 LLM 摘要直接写入长期记忆。

写入前先做 deterministic pre-filter：寒暄、确认、分隔符和重复工具输出默认不生成长期候选；用户纠正、明确决策、任务进度、执行日志和路径/API 变更必须保留来源与 stable identity key。LLM 可以帮助摘要，但不能决定是否覆盖旧候选；覆盖、追加、阻断和删除必须由可审计规则和 owner review 共同约束。

受保护条目必须标记 `protected_entry_class`，当前最小集合是 `correction`、`decision`、`progress` 和 `execution-log`。若新候选与旧候选使用相同 `stable_identity_key`，必须设置 `duplicate_key_status: collision` 与 `contradiction_status: conflict_review`，并把 `promotion_action` 固定为 `conflict_review`。这类候选不得使用 `auto_promote_candidate` 或 `promoted`，即使摘要文本看起来更短或更完整。

外部记忆工具只能在 AGENTS、项目地图、阶段摘要和归档索引仍不足以支撑跨会话连续性时升级。升级前先区分需求是 continuity pack 还是 historical search：前者优化下一轮继续执行所需的目标、约束、阻塞和完成标准；后者优化跨会话查找历史证据。两者都必须保留 `raw_evidence`、来源置信度和回退路径。

## 写入准入

候选必须同时满足：

1. 下次同类任务会用到。
2. 有证据来源，例如命令、文件、错误、验证结果或用户明确要求。
3. 作用域清楚，不能把项目规则误写成全局用户规则。
4. 风险分级清楚，且高风险需要人工确认。
5. 有 `last_verified`；依赖外部 API、路径、平台策略或用户偏好时必须有 `next_review_by`。

候选晋升必须先进入 inbox 或 candidate 工件，再按频率、跨会话重复、作用域、安全性、冲突状态和验证证据评分。含 `[REDACTED]`、疑似密钥、token、cookie、连接串、账号路径或原始敏感日志的候选固定为 `blocked`；`conflict_review`、高风险、项目局部事实和权限相关候选不得自动晋升到全局用户记忆。

## 风险分级

| 风险 | 示例 | 处理 |
|---|---|---|
| 低风险 | 图片要检查重叠、发布前跑指定 dry-run、已证实工具限制 | 可自动生成候选，允许进入审计材料 |
| 中风险 | 项目默认目录、跨团队工作流、默认脚本选择 | 生成候选并说明影响范围和回退位置 |
| 高风险 | 自动发布、删除文件、操作生产数据库、支付动作、保存账号或密钥、扩大权限 | 必须 `requires_user_confirmation: true`，不得自动落地 |

## 写入路由

| write_route | 使用场景 |
|---|---|
| `none` | 不值得保存，只在本次回复说明 |
| `session-summary` | 仅用于会话接力 |
| `project-runbook` | 项目内稳定流程或验证步骤 |
| `project-AGENTS` | 必须影响未来 Agent 默认行为的项目规则 |
| `user-memory` | 用户长期偏好，必须确认 |
| `archive` | 研究结论、复盘材料、证据链 |
| `skill-template` | 可复用为 skill 或模板的流程 |

## stale / 冲突治理

- 外部 API、平台规则、路径和用户偏好不是永久真理，必须设置 `next_review_by`。
- 新候选与旧规则冲突时，使用 `conflicts_with` 标记，不静默覆盖。
- 新规则替代旧规则时，使用 `supersedes` 标记并说明依据。
- 整理报告必须显式列出 `promotion_candidates`、`stale_active`、`duplicate_groups`、`contradictions`、`missing_evidence` 和 `suggested_docs`；缺证据项不得进入 active memory。
- 每条候选必须记录 `contradiction_status`，取值可为 `none`、`duplicate`、`stale`、`conflicts_with`、`supersedes`、`missing_evidence` 或 `conflict_review`。
- failure replay 只能生成 incident candidate，先进入 evidence/conflict/owner review；不得把失败回放结论直接晋升为长期默认规则。
- 长期未使用或被验证推翻的候选应降权、归档或删除。
- 遗忘、降权和删除必须可审计，至少包含最小阈值、宽限期、复核条件和原文回退入口。不得仅因向量相似度低、短期未命中或模型判断“不重要”就删除长期候选。
- 项目 AGENTS 或 runbook 的经验规则只保存会改变未来默认行为的具体结论。优先修订已有规则，避免叠加近义规则；过时经验必须可审计降权、归档或删除。

## 执行流程

1. 任务完成后用 `templates/memory/after-action-review.md` 复盘。
2. 从复盘中提取 reusable lessons。
3. 对每条 lesson 生成 `templates/memory/memory-candidate.md`。
4. 按风险决定自动记录候选、请求确认或拒绝写入。
5. 修改本治理资产后运行：

```bash
rtk bash scripts/check-memory-governance.sh
rtk bash scripts/validate-assets.sh --strict
```
