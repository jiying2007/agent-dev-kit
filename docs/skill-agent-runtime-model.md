# Skill / Agent / Runtime 分层模型

## 目标

本文件定义 `agent-dev-kit` 的内容与运行时职责边界，防止角色、方法、编排、工具、知识和门禁互相复制。`manifest.json` 始终是 identity/product-boundary SSOT；本文件只定义内容架构，不建立第二份资产目录。

## 七层模型

| 对象 | 回答的问题 | 主要职责 | 资产位置 |
|---|---|---|---|
| Agent | 谁负责？ | role、ownership、decision authority、permission、handoff、stop condition | `agents/<name>/AGENTS.md` |
| Skill | 会做什么、怎么做？ | 可复用 capability、procedure、I/O、failure、evidence | `skills/` / `optional-skills/` |
| Workflow | 多个能力怎样组合？ | state、transition、checkpoint、abort/resume、completion | `workflows/` |
| Tool / Automation | 真正执行什么？ | 确定性动作、机器输入输出、副作用 | `scripts/`、CLI、受控 tool |
| Guardrail | 什么不能做？ | schema、policy、runtime gate、approval、isolation | `schemas/`、`manifests/`、validator/runtime |
| Reference | 需要知道什么？ | 领域知识、方法细节、命令/模式、历史依据 | `references/`、`knowledge/` |
| Eval | 如何证明做对？ | routing、behavior、authority、permission、trajectory evidence | `tests/`、fixtures、受管 runtime receipts |

`Sub-agent` 是短生命周期执行实例，不是新的内容层；它必须使用 typed handoff/task contract 承接上述角色与能力。`MCP/tool` 只提供外部能力接口，不定义任务方法论，也不自动授予权限。

## 核心不变量

- Agent 不复制默认 Skill 的 SOP；Agent 只保留稳定、低变化、适合常驻 context 的角色语义。
- Skill 不复制 Workflow 的跨阶段状态机；Workflow 不复制 Skill 的领域步骤。
- Tool/Automation 不决定任务目标；它只执行显式输入定义的动作。
- Guardrail 的 machine-enforceable 规则不得只停留在 prompt。
- Reference 默认按需加载，不因“以后可能有用”进入 always-loaded context。
- Eval 不以文档存在或 token 下降替代真实 task/authority evidence。

## Agent vNext 入口规范

`AGENTS.md` 是 thin role contract，不是岗位百科、调试手册或 SOP。每个 live Agent 的正文应围绕：

- `Mission`
- `Owns`
- `Does Not Own`
- `Decision Authority`
- `Permission Boundary`
- `Default Capabilities`
- `Handoff / Escalation`
- `Stop Conditions`
- `Input Contract`
- `Output Contract`

Agent 不应默认包含：执行流程、必跑命令、工具箱、通用工程知识、长 checklist、完整 pass/needs-fix 示例或默认 Skill 已经定义的 procedure。角色专属 judgement 可以保留，但复用方法应移动到 Skill/reference。

Agent 的 identity、path、quality tier、`owns`、`does_not_own`、`handoff_to`、`default_skills` 与 permission profile 以 `manifest.json` 为准。机器化 permission、decision authority、handoff 与 eval 语义继续由既有 `manifests/agent_value_contracts.json` 承载；禁止再创建平行 Agent behavior identity/authority catalog。

新增 Agent 只有在至少存在一个独立边界时才合理：decision authority、permission envelope、ownership、可独立委托 specialist 责任或不同 handoff/escalation semantics。否则优先新增/复用 Skill 或 Workflow。

## Skill vNext 入口规范

`SKILL.md` 是被激活后读取的 capability instruction。Discovery 第一层保持轻量，至少包含 `name` 与能表达 **what + when + boundary** 的 `description`；ADK 可继续保留 `triggers`、`non_triggers`、`inputs`、`outputs`、`constraints` 作为 authoring 辅助，但复杂 runtime policy 不塞入 portable metadata。

机器化 Skill 语义由 `manifests/skill_content_contracts_v2.json` 从 `manifest.json` 派生：

- `capability_class`: `task | workflow | support | guardrail | tool | knowledge | meta`
- `runtime_role`: `primary | supporting | governance | fallback`
- `selection_group`
- `effect_ceiling`
- eval obligations

`capability_class` 与 `runtime_role` 正交。Tool、guardrail、meta 也可以是直接用户任务入口；只要它被 `routing.intents[].primary_skill` 明确选择，就必须解析为 `runtime_role=primary`。真正的 support/knowledge 资产不能因普通 trigger 命中而隐式晋升为 primary。

`effect_ceiling` 只是能力副作用上限，不是授权。真正执行仍必须同时满足 Agent permission、tool/runtime policy 与必要 approval；ceiling 只能收紧现有 mutation permission，不能授予更强权限。

Skill body 不强迫使用一套固定 headings。按 capability class 选择最小充分结构：

- task：Goal / Use When / Prerequisites / Workflow / Failure / Output-Evidence。
- workflow：Goal / State Model / Entry / Transition / Stop-Replan / Completion。
- guardrail：Protected Boundary / Policy / Trip Conditions / Enforcement / Exceptions / Evidence。
- tool：Tool Contract / Input Validation / Execution / Exit-Failure / Security。
- support/knowledge：只保留支持 primary 所需的最小 instructions/reference pointers，默认不得争抢 implicit primary。

重复、确定性步骤进入 `scripts/`；长背景、命令百科、历史案例进入 `references/`；资产模板进入 `assets/`。主入口只保留触发后立即需要的信息。

## Description 触发质量

`description` 是 discovery 的第一层入口。新增或大改 Skill 必须：

- 说明做什么、何时使用以及至少一个关键近邻边界。
- 与 `triggers/non_triggers`、manifest routing 和 Skill v2 runtime role 一致。
- 能与相邻 Skill 区分，避免多个 primary 同时命中。
- 高风险场景描述行为边界，但不得用 description 承诺权限。
- 通过 positive、near-miss negative、abstain/collision fixture 验证；只改文案不等于完成。

## Routing 与 progressive disclosure

`manifest.json:routing` 继续是 reviewed intent routing IR。`src/agent_dev_kit/matcher.py` 保持稳定匹配 kernel；公共 `scripts/skill-match.sh` 与 `scripts/devkit.sh match` 通过 `matcher_vnext` 叠加 Skill v2 eligibility，而不是把新策略复制进 matcher kernel。

运行时规则：

- 显式 routing intent 的 primary 必须与 Skill v2 `runtime_role=primary` 一致；冲突由 CI fail-closed。
- 隐式 trigger fallback 只允许 `runtime_role=primary`。
- `--skill` 显式加载可以读取 supporting/governance Skill；runtime role 不等于访问权限。
- effect ceiling 只收紧 mutation permission。
- CI 与 runtime 共用 `resolve_skill_content()`，避免两套 derivation。

在候选确定后只能有一个 primary，supporting/governance capability 按需加载。`adk-runtime-router` 负责 intent/risk/evidence planning；它不能绕过 permission、owner approval 或 tool guardrail。大 catalog 默认先暴露 namespace/description summary，命中后再读取 `SKILL.md`，再按需进入 references/scripts/assets 或 L3/raw evidence。

## Handoff / Sub-agent

跨 Agent、parent→Sub-agent、review→implementation、verification→release 的 handoff 统一使用 `schemas/agent-handoff-v1.schema.json`。至少传递 objective、facts/assumptions、scope、evidence refs、permission envelope、stop conditions、context policy 与 expected output。

Handoff 必须 summary-first；raw output 默认只传 opaque/path pointer；接收方权限不得因为 handoff 自动扩大。现有 `templates/planning/worker-contract.md` 可继续作为 worker task package，但不能创建与全局 handoff 冲突的权限语义。

## Guardrail 分层

- G0：prompt guidance。
- G1：schema/static validator。
- G2：runtime/tool guardrail。
- G3：explicit owner/human approval。
- G4：sandbox/worktree/runtime isolation。

越高 side-effect/risk 的动作越不能只依赖 G0。Prompt 说明是行为提示，不是安全边界。

## Eval 分层

- E0：schema、identity parity、reference integrity。
- E1：routing、trigger、near-miss collision、abstain。
- E2：task behavior、failure handling、evidence completeness。
- E3：authority、permission、handoff negative。
- E4：完整 trajectory。

仓库没有受管 production runtime authority/receipt 时，E2–E4 的生产测量必须保持 `not-measured`，不得用结构测试伪造 production success。Token/context 指标是 efficiency evidence，不是 quality KPI。

长期 content ratchet 由注册的 `manifests/content_architecture_policy.json` 承载；change package 只保存某次迁移的历史证据，因此归档后不会成为运行时依赖。

## Workflow 入口规范

Workflow 是一等资产，管理阶段、state、artifact、checkpoint、approval、failure loop 与 completion gate；领域 procedure 留给 Skill。Manifest 继续索引 Workflow 的 profile、primary agent/skill、supporting skills、entry conditions 与 exit evidence。

## 外部 Skill 引入

第三方 Skill 不直接进入生产资产链路。外部 Agent/Skill/Plugin/MCP 实践默认只作为 method/provenance evidence：先做来源、版本、许可证、安全、重复能力与权限审查；需要采纳时重写为 ADK 原生资产并经过 manifest、validator、eval、pilot/owner gate。安装成功、registry listing 或社区热度都不等于生产批准。

跨宿主 runtime 只迁移可证明的 method/contract，不继承平台私有 API、默认权限、hook、memory 注入或自动化副作用。
