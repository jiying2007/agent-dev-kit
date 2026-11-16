---
name: adk-context-engineering
description: "用于上下文膨胀、跨会话恢复或并行 Agent 隔离时规划稳定规则、按需引用及证据指针；不用于直接替代任务计划、代码实现或 Token 配额门禁。"
version: 2.0.2
last_updated: 2026-11-16
triggers:
  - 上下文工程
  - 上下文膨胀
  - 跨会话恢复
  - Agent 理解偏差
  - 并行上下文隔离
  - context planning
non_triggers:
  - 直接写代码
  - 单纯运行测试
  - 只做 token 配额治理
inputs:
  - 当前任务目标和阶段
  - 稳定规则与动态证据来源
  - 可用 Skill/reference/tool surface
outputs:
  - 上下文加载计划
  - 摘要与 raw pointer 策略
  - 缺失/噪音/隔离风险
constraints:
  - progressive disclosure 优先
  - 稳定身份规则与动态证据分离
  - 不因压缩丢失高风险原始证据的可追溯 pointer
  - 不把临时 references 固化为长期事实
---

# adk-context-engineering

## Goal
生成最小充分、可恢复、可追溯的 context policy。

## Use When
- 长任务需 checkpoint / resume / handoff，或并行 Agent 需共享 contract 与上下文隔离。
- 上下文膨胀、冲突、缺证、错误 reference 或过度压缩导致误解。

没有 context 边界问题时仅作 supporting capability，不替代计划、编码或测试。

## Prerequisites
- 明确当前 objective、phase、risk level 与候选 primary Skill。
- 知道哪些输入是 authoritative facts，哪些只是假设、历史摘要或按需 reference。

## Context Policy
1. **Stable core**：只保留长期稳定的 role/rules/contract；优先 cache-friendly 内容。
2. **Task state**：目标、当前阶段、done/open/blocker、candidate identity。
3. **Evidence**：先摘要与 evidence ref；高风险/争议结论保留 L3/raw pointer，不默认复制全文。
4. **On-demand capability**：只有触发后才加载 Skill body、reference、tool schema。
5. **Handoff isolation**：子任务只接收 objective、必要 facts/contract、scope、evidence refs；不默认继承完整聊天历史。

## Workflow
1. 识别当前决策真正需要的事实、contract 和 evidence。
2. 将信息标记为 `always | phase | on-demand | raw-pointer | exclude`。
3. 删除重复、过期、低价值动态输出；冲突信息保留来源与 freshness，不静默覆盖。
4. 为长任务写 summary-first checkpoint；raw output 仅保留 opaque/path pointer 和 retention decision。
5. 交接默认使用下方模板，不扩大权限；仅在 ADK 源码根已确认且文件可读时，可选根下 `schemas/agent-handoff-v1.schema.json`；未使用不声称 schema 验证。
6. 验证恢复能力：新执行者只读取摘要和 refs 应能知道目标、已确认事实、未决问题和下一步；若不能，补缺失信息而不是扩大所有上下文。

## Failure / Abstain
- 权威来源不明确：输出 `needs-evidence`，不要用历史摘要替代事实。
- 压缩会让 blocker、permission、candidate identity 或原始证据不可追溯：保留 pointer 并拒绝继续压缩。
- 问题实质是 routing/token-policy：分别交给 `adk-runtime-router` / `adk-token-context-governance`。

## Quality Gate
- 关键信息均有 provenance 或明确 assumption 标记。
- dynamic/raw 内容不进入 always-loaded core。
- handoff 不扩大权限，不复制无关完整历史。
- 恢复摘要包含 objective、state、blockers、evidence refs、next action。
- “质量提升”必须由具体误解/缺失样例或 eval 证明，不接受主观描述。

## Evidence Template
```md
- Objective / Phase:
- Confirmed Facts:
- State / Blockers:
- Scope / Permission:
- Evidence / Fallback:
- Next Actions:
- Context decisions: always / phase / on-demand / raw-pointer / excluded
- Missing / conflicting evidence:
- Recovery check: pass | needs-evidence
- Efficiency observation: <optional; not a quality KPI>
```
