# Target Architecture Report (目标架构报告)

> **使用说明**: 在长期资产、跨仓治理、平台迁移、运行态交付链路或核心能力重构前使用此模板。它用于记录当前架构、目标架构、职责边界、问题地图、阶段路线图、任务表和证据索引，避免架构结论只停留在会话上下文。

[artifact:target-architecture-report]
status: DRAFT
owner: [填写负责人]
scope:
- [本文档覆盖的仓库、系统、profile 或运行态边界]
inputs:
- [需求/goal/task card]
- [当前状态报告]
- [验证门禁或历史证据]
handoff_to:
- architecture-planner, implementation-planner, reviewer

> **使用场景**: 长期资产架构优化、跨运行态 source-to-live 设计、平台中立能力提升、重大治理边界调整。
> **适用角色**: architecture-planner, governance-owner, workflow-coordinator

---

## Summary

- **目标**: [本次目标架构要解决的问题]
- **非目标**: [明确不做的内容]
- **当前结论**: [pass / needs-fix / blocked / split]
- **主要证据**: [关键命令、报告或验证路径]

## Scope

| Area | In Scope | Out of Scope |
|---|---|---|
| [范围A] | [包含内容] | [排除内容] |

## Current Architecture Map

```text
[当前系统/仓库/资产流]
  -> [输入/来源]
  -> [中间资产]
  -> [验证/交付]
  -> [运行态或反馈]
```

## Target Architecture

| Layer | Owner | Purpose | Primary Assets | Gate |
|---|---|---|---|---|
| [层级] | [owner] | [职责] | [资产] | [验证门禁] |

## Responsibility Boundary

| Decision | Lands In Source / Governance Repo | Lands In Neutral Assets |
|---|---|---|
| [决策类型] | [证据/报告/registry] | [agent/skill/workflow/template/script/test] |

## Issue Map

| ID | Severity | Finding | Evidence | Action |
|---|---|---|---|---|
| P0-1 | blocker/major/minor | [问题] | [证据] | [处理动作] |

## Phase Roadmap

| Phase | Goal | Done Criteria | Verification |
|---|---|---|---|
| Phase 1 | [目标] | [完成标准] | [验证命令] |
| Phase 2 | [目标] | [完成标准] | [验证命令] |

## Implementation Tasks

| ID | Priority | Task | Files | Stop Condition | Verification |
|---|---|---|---|---|---|
| A1 | P0 | [任务] | [文件/目录] | [停止条件] | [验证命令] |
| B1 | P1 | [任务] | [文件/目录] | [停止条件] | [验证命令] |
| C1 | P2 | [任务] | [文件/目录] | [停止条件] | [验证命令] |

## Verification Gates

| Command | Expected |
|---|---|
| `[验证命令]` | [期望结果] |

## Rejected Options

| Option | Decision | Reason |
|---|---|---|
| [不采纳方案] | reject | [原因] |

## Evidence Index

| Command | Exit Code | Result Summary | Layer |
|---|---:|---|---|
| `[命令]` | 0 | [结果摘要] | [层级] |
| `[负例或 before-fix 命令]` | 1 | [失败/被证伪摘要] | [层级] |

## Goal Closure State

- goal_statement: [原始目标]
- completion_claim: [当前完成声明]
- required_evidence: [必需证据]
- claimant: [声明人]
- verifier: [验证人或门禁]
- open_items: [未闭环项]
- retry_budget: [重试预算]
- staleness_threshold: [过期阈值]
- heartbeat: [当前阶段状态]
- stop_condition: pass / replan / split / blocked / abort

## Checklist

- [ ] 当前架构地图可追溯到源事实
- [ ] 目标架构不混入运行态私有路径或一次性事实
- [ ] 职责边界清晰，说明哪些内容进入治理仓，哪些进入中立资产
- [ ] 问题地图包含 severity、evidence 和 action
- [ ] 实施任务覆盖 P0/P1/P2 或说明为什么不适用
- [ ] Evidence Index 至少包含一个通过证据和一个负结果或 before-fix 证据
- [ ] Goal Closure State 字段完整
- [ ] source-to-live 或 live 写入动作有显式审批边界
