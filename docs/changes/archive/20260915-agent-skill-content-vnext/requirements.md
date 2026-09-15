# Agent/Skill Content Architecture vNext — Requirements

## Problem
ADK 的治理面已经具备 manifest SSOT、progressive disclosure、typed evidence、permission/handoff 和 exact-head 验证，但内容面仍存在 Agent 与默认 Skill 重复表达 SOP、Agent 常驻上下文过重、Skill 类型被单一模板约束、primary 候选过多以及自然语言规则与机器策略边界不清等问题。

## Goals
1. 保持 `manifest.json` 为 identity/product-boundary 唯一 SSOT。
2. 将 Agent 收敛为 thin role contract：身份、ownership、authority、permission、handoff、stop conditions、I/O；procedure 归 Skill。
3. 为全部 core 与 optional Skill 建立 v2 machine contract，区分 capability class、runtime role、selection group、effect ceiling 与 eval obligations，并由公共 match runtime 实际消费。
4. 将 handoff 提升为全局 typed schema，并把可确定 guardrail 从 prompt 下沉到 validator/policy/runtime adapter。
5. 建立 Agent↔Skill 去重 ratchet、size budget、cross-skill collision/eval fixture 和 manifest parity gate；长期 ratchet 不依赖 active change 目录。
6. 保留 `adk-runtime-router` 已成熟的 one-primary、progressive disclosure、fallback/evidence 语义，不恢复已退役 selector。
7. 旧 heading/template 测试退役，改为按资产职责校验。
8. 完成 Phase 0–8 后不得保留新的平行 Agent behavior SSOT 或永久 Skill v1/v2 双轨兼容层。

## Non-goals
- 不凭主观判断删除 13 个 Agent identity。
- 不启用外部 Agent/Skill runtime、MCP、hooks 或插件。
- 不把 token 指标当 quality KPI。
- 不伪造 runtime/field behavior evidence；未接入受管 authority 的行为指标继续显式 `not-measured`。

## Acceptance
- 13/13 Agent 通过 thin-contract validator；manifest default skills/handoff/permission 一致。
- 57 个 core Skill + 8 个 optional Skill 全部由 v2 contract 覆盖，无 parallel path/description identity catalog。
- 既有 `agent_value_contracts.json` 继续作为 Agent permission/authority/handoff/eval typed authority；不得新增平行 behavior authority。
- handoff、Skill content、content architecture policy schema 均通过 Draft 2020-12 schema check，并登记统一 contract registry。
- public match runtime 使用 Skill v2：显式 routing primary 必须是 v2 primary；implicit fallback 不得把 supporting/governance/fallback Skill 晋升为 primary；effect ceiling 只能收紧权限。
- CI 与 runtime 共用 Skill v2 resolver，禁止 checker/runtime 两套派生语义。
- content quality gate 不再强迫 Agent 携带 SOP/commands/examples，也不再强迫所有 Skill 使用同一 body headings。
- BSP Agent/Skill 作为去重样板：Agent 不再复制 boot/probe/clock/reset/pinctrl/IRQ/DMA procedure；procedure 留在 Skill/reference。
- context-engineering 重写为 context policy planner，不保留“10 分钟”等硬编码时间阈值。
- change package 在 independent review PASS 后归档，且归档不破坏 validator/runtime。
- exact-head CI 全绿后才允许 expected-head squash merge；merge 后 fresh-main CI + promotion evidence 再验证。
