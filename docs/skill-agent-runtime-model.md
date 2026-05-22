# Skill / Agent / Runtime 分层模型

## 目标

本文件定义 `agent-dev-kit` 中 Skill、Agent、Sub-agent、Workflow、MCP/tool 的职责边界，防止方法论、运行角色、外部工具和并行调度混写导致资产漂移。

## 分层定义

| 对象 | 生命周期 | 主要职责 | 资产位置 |
|------|----------|----------|----------|
| Skill | 长期版本化资产 | 定义某类任务应该怎么做、输入输出、Done criteria、失败收口和验证要求 | `skills/<name>/SKILL.md` 或 `optional-skills/<name>/SKILL.md` |
| Agent | 运行时执行主体 | 读取上下文、选择 Skill、调用工具、推进任务并对结果负责 | `agents/<name>/AGENTS.md` |
| Sub-agent | 短生命周期执行实例 | 在主 Agent 拆分后处理边界明确的子任务，回传结构化结果 | 由运行时调度，任务契约由模板约束 |
| Workflow | 跨阶段状态机 | 定义 propose/apply/verify/review/archive 等阶段、状态和门禁 | `scripts/workflow.sh`、`docs/workflows.md` |
| MCP/tool | 外部能力接口 | 提供 Git、文档、设备、API、浏览器等能力连接，不定义任务方法论 | `manifest.yaml`、运行时配置和边界检查脚本 |

## 写入边界

- Skill 只写稳定方法、触发边界、输入输出、执行步骤、质量门禁和失败收口。
- Agent 只写角色责任、决策边界、协作方式和默认工具策略。
- Sub-agent 任务必须通过任务契约传递，不把临时任务细节沉淀到长期 Skill。
- MCP/tool 只声明能力和风险边界，不承担流程编排职责。
- Workflow 只管理阶段状态和门禁，不重复 Skill 的领域步骤。

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

## Description 触发质量

`description` 是运行时 discovery 的第一层入口，必须能让 Agent 判断何时使用该 Skill。新增或大改 Skill 时必须满足：

- 描述具体场景和任务结果，不能只写泛化能力名。
- 与 `triggers`、`non_triggers`、`manifest.yaml` routing 语义一致。
- 能和相邻 Skill 区分，避免多个 Skill 同时成为 primary。
- 不使用 `TODO`、`TBD`、`待补充`、`示例技能` 等占位内容。
- 涉及高风险操作时体现边界，例如发布、外部系统、生产设备、凭据或运行态资产。

## 并行执行契约

主 Agent 派生 Sub-agent 前，必须把执行规则作为任务契约分发，而不是只给一句自然语言目标。任务契约至少包含：

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

## 外部 Skill 引入

第三方 Skill 不直接进入生产资产链路。默认流程是：

1. 作为候选资产进入参考或 intake 记录。
2. 做安全、许可证、触发边界、重复能力和运行时权限检查。
3. 需要采纳时转写为 adk 原生 `skills/` 或 `optional-skills/`。
4. 通过 `manifest.yaml`、验证脚本和测试门禁后，才允许进入 `agent-dev-kit -> ~/codex -> ~/.codex` 链路。

安装成功不等于采纳完成；生产资产以 `manifest.yaml` 和验证证据为准。
