# Skill / Agent / Runtime 分层模型

## 目标

本文件定义 `agent-dev-kit` 中 Skill、Agent、Sub-agent、Workflow、MCP/tool 的职责边界，防止方法论、运行角色、外部工具和并行调度混写导致资产漂移。

## 分层定义

| 对象 | 生命周期 | 主要职责 | 资产位置 |
|------|----------|----------|----------|
| Automation | 确定性运行单元 | 执行规则明确、输入输出稳定、无需运行时推理的重复动作 | 脚本、CI job、cron job 或受控命令 |
| CLI/script | 操作入口或包装层 | 暴露命令、参数和机器可读输出，不定义任务方法论 | `scripts/`、tool wrapper、受控二进制 |
| Skill | 长期版本化资产 | 定义某类任务应该怎么做、输入输出、Done criteria、失败收口和验证要求 | `skills/<name>/SKILL.md` 或 `optional-skills/<name>/SKILL.md` |
| Agent | 运行时执行主体 | 读取上下文、选择 Skill、调用工具、推进任务并对结果负责 | `agents/<name>/AGENTS.md` |
| Sub-agent | 短生命周期执行实例 | 在主 Agent 拆分后处理边界明确的子任务，回传结构化结果 | 由运行时调度，任务契约由模板约束 |
| Workflow | 跨阶段状态机 | 定义 propose/apply/verify/review/archive 等阶段、状态和门禁 | `workflows/<name>/WORKFLOW.md`、`scripts/workflow.sh`、`docs/workflows.md` |
| MCP/tool | 外部能力接口 | 提供 Git、文档、设备、API、浏览器等能力连接，不定义任务方法论 | `manifest.json`、运行时配置和边界检查脚本 |

## 写入边界

- Skill 只写稳定方法、触发边界、输入输出、执行步骤、质量门禁和失败收口。
- Agent 只写角色责任、决策边界、协作方式和默认工具策略。
- Sub-agent 任务必须通过任务契约传递，不把临时任务细节沉淀到长期 Skill。
- MCP/tool 只声明能力和风险边界，不承担流程编排职责。
- Workflow 只管理阶段状态和门禁，不重复 Skill 的领域步骤。
- CLI/script 只作为确定性执行入口或包装层，不替代 Skill SOP、MCP/tool policy 或 Workflow 状态机。
- 默认选择最低充分抽象层：确定性重复任务用 Automation，预定义多步骤用 Workflow，需要上下文感知和运行时决策时才升级为 Agent。
- Agent/runtime 身份必须在任务契约中显式声明；workspace、消息入口、目录位置或启动方式都不能单独等同于执行 Agent。
- 只有任务类型长期稳定分化，且上下文、权限、工具面或交付责任确需隔离时，才拆新 Agent；否则优先用 Skill、Workflow 或 worker contract 约束。
- Intent/router 只能做候选选择和证据排序，不能绕过 Skill、Workflow、tool policy 或 owner approval 直接授予执行权限。

## Agent 入口规范

`AGENTS.md` 是运行角色契约，不是领域知识库。每个 Agent 必须至少包含：

- `角色定位`：职责、核心关注和非职责范围。
- `适用输入`：可处理的输入材料和上下文边界。
- `核心决策规则`：必须遵守的判断规则。
- `执行流程`：推进任务的阶段化动作。
- `必跑验证`：该角色放行前必须执行或要求的检查。
- `阻塞与升级`：何时暂停、转交或要求人工确认。
- `输出契约`：结论字段、证据和交付格式。

Agent 的 manifest 条目必须声明 `description`、`quality_tier`、`owns`、`does_not_own`、`handoff_to`、`default_skills` 和 `quality_gate`。描述用于 discovery，必须与角色职责一致，不能使用占位或泛化描述；`handoff_to` 和 `default_skills` 必须引用已登记资产。Agent 不直接复制 Skill 的 SOP；当流程稳定可复用时沉淀为 Skill，当跨阶段状态需要持久化时沉淀为 Workflow。

## Skill 入口规范

`SKILL.md` 是岗位 SOP 的入口，不是长篇知识库。默认只保留：

- frontmatter: `name`、`description`、`triggers`、`non_triggers`、`inputs`、`outputs`、`constraints`
- `Goal`
- `Prerequisites`
- `Workflow`
- `Commands`
- `Evidence Template`
- `Failure Handling`
- `Quality Gate`

长背景、示例、领域知识、检查清单和历史决策进入 `references/`。入口文件必须保持短小，严格门禁下不超过 140 行。

每个 live Skill 还必须在 `manifest.json:skills` 或 `manifest.json:optional_skills` 中声明 `category`、`lifecycle_order`、`stage_order`、`activation_mode` 和 `pattern`。`lifecycle_order` 定义大类阶段，`stage_order` 定义同一阶段内的执行/呈现顺序。场景级 primary/supporting/fallback 关系不由 `SKILL.md` 自行声明，统一以 `manifest.json:routing` 为准；`skill_routing_matrix` 仅通过 `routing_intent` 引用该 IR 并补充 workflow/profile/example 展示元数据。optional skill 被作为 primary 使用时，相关 routing intent 必须声明 `availability: optional-skill-required`。

## Description 触发质量

`description` 是运行时 discovery 的第一层入口，必须能让 Agent 判断何时使用该 Skill。新增或大改 Skill 时必须满足：

- 描述具体场景和任务结果，不能只写泛化能力名。
- 与 `triggers`、`non_triggers`、`manifest.json` routing 语义一致。
- 能和相邻 Skill 区分，避免多个 Skill 同时成为 primary。
- 不使用 `TODO`、`TBD`、`待补充`、`示例技能` 等占位内容。
- 涉及高风险操作时体现边界，例如发布、外部系统、生产设备、凭据或运行态资产。

## 并行执行契约

主 Agent 派生 Sub-agent 前，必须把执行规则作为任务契约分发，而不是只给一句自然语言目标。任务契约至少包含：

- `agent_identity`
- `runtime_identity`
- `primary_skill`
- `supporting_skills`
- `scope_read`
- `scope_write`
- `must_not_touch`
- `done_criteria`
- `verification_commands`
- `report_schema`
- `conflict_policy`

标准模板见 `templates/planning/worker-contract.md`。

OpenAI Agents SDK 文档中的 handoff/ownership 语义在 adk 中落地为本地 contract，而不是直接绑定 SDK。`manifests/subagent_contracts.json` 是默认审计入口，必须声明 owner、`scope_read`、`scope_write`、`must_not_touch`、handoff condition、reply owner、stop condition 和 report schema。最终回复归属默认保留在主 Agent，子代理只交付结构化结果和验证证据。

## Workflow 入口规范

Workflow 是一等资产，必须同时出现在 `manifest.json:workflows` 和 `workflows/<name>/WORKFLOW.md`。manifest 负责索引与导出闭包；`WORKFLOW.md` 负责阶段契约和人工可审查说明。

每个 Workflow 必须声明：

- `path`、`primary_agent`、`primary_skill` 和 `supporting_skills`。
- `workflow_type`、`lifecycle_order`、`entry_conditions` 和 `exit_evidence`。
- `triggers`、`agents`、`skills`、`commands` 和 `verification`。
- `WORKFLOW.md` frontmatter 中的 `profiles`、`stages`、`artifacts`、`failure_handling`。
- 固定章节：`Goal`、`Scope`、`Ownership`、`Stage Contract`、`Artifact Contract`、`Commands`、`Failure Handling`、`Quality Gate`。

Workflow 不重复领域 Skill 的细节；它只定义阶段、工件、门禁、失败回路、审批点和验证闭包。

## 外部 Skill 引入

第三方 Skill 不直接进入生产资产链路。默认流程是：

1. 作为候选资产进入参考或 intake 记录。
2. 做安全、许可证、触发边界、重复能力和运行时权限检查。
3. 需要采纳时转写为 adk 原生 `skills/` 或 `optional-skills/`。
4. 通过 `manifest.json`、验证脚本和测试门禁后，才允许进入显式 tool target 适配链路。

安装成功不等于采纳完成；生产资产以 `manifest.json` 和验证证据为准。

## 临时文章吸收

公众号文章、教程摘录和趋势榜单只作为 intake 输入。允许吸收的是可复用执行规则、边界条件、完成标准、验证命令和失败收口；不得吸收的是原文表达、工具热度、未经审查的安装命令、领域专用代码和平台宣传。

若候选内容与现有 Skill/Agent/Workflow 重叠，默认 `MERGE` 到已有资产；只有证明现有入口无法表达新职责，才允许新增资产。新增资产必须同时说明触发边界、非触发条件、依赖边界和回退方式。

外部 AGENTS、CLAUDE、GEMINI 或平台配置分享必须先拆层：项目事实进入项目地图或 README 类工件，Agent/Skill 可移植规则进入对应治理文档，runtime connector、MCP、hook、provider、API key、平台协作命令和安装片段保持 report-only，直到供应链和运行态权限审查完成。

同一份 Skill 在不同宿主 runtime 下可能因 discovery timing、项目规则优先级、memory/context injection、sub-agent delegation、sandbox/approval、hook 和工具权限不同而表现不同。跨平台吸收只能记录触发边界、字段兼容矩阵和验证规则，不能继承平台私有 API、字段语义或默认权限。

Agent 能执行任务不等于允许自治运行。定时、事件、webhook、消息机器人、自动发送、自动发布和后台循环属于 Workflow/runtime 入口，必须先声明 owner、触发条件、输入输出、审批点、dry-run、日志、禁用路径和回滚方式。
