---
name: feature-delivery
description: 新功能从需求收敛到验证评审的交付工作流
version: 1.0.0
last_updated: 2026-06-01
primary_agent: requirements-analyst
primary_skill: adk-requirements-triage
triggers:
  - "新功能迭代"
  - "功能开发"
  - "feature delivery"
profiles:
  - core
  - embedded-fullstack
command_risk: low
stages:
  - propose
  - apply
  - verify
  - review
  - archive
artifacts:
  - proposal.md
  - design.md
  - tasks.md
  - verify-report.md
  - review-report.md
verification:
  - "rtk bash tests/test_validate.sh"
  - "rtk bash tests/test_workflow_closure.sh"
failure_handling:
  - "需求边界不清时停在 propose，不进入 apply"
  - "验证失败时返回 apply 修复并保留负结果"
---

# feature-delivery

## Goal
- 将新功能诉求转成可实现、可验证、可审查的交付链路。
- 固化目标、非目标、接口边界、任务拆分、测试证据和评审结论。

## Scope
- 适用于通用功能开发、嵌入式组件增强和接口行为扩展。
- 不适用于生产 P0/P1 事故快速修复；事故场景使用 incident 或 bugfix 流程。

## Ownership
- Primary agent: `requirements-analyst`
- Primary skill: `adk-requirements-triage`
- Supporting skills: `adk-task-breakdown`, `adk-interface-contract-design`, `adk-test-strategy`, `adk-verification-before-completion`, `adk-code-review-loop`

## Stage Contract
1. `propose`: 明确目标、非目标、验收标准和影响面。
2. `apply`: 按任务切片实施，并保持接口和测试同步更新。
3. `verify`: 运行定向验证，记录命令、退出码和证据路径。
4. `review`: 审查需求覆盖、设计一致性、测试充分性和风险。
5. `archive`: 归档变更工件和验证结论。

## Artifact Contract
- `proposal.md` 必须包含单问题陈述、上下文充分性和风险。
- `design.md` 必须包含接口边界、兼容性和回退。
- `tasks.md` 必须包含 ownership、验证命令和完成标准。
- `verify-report.md` 与 `review-report.md` 必须结论一致。

## Commands
```bash
rtk bash scripts/devkit.sh catalog build
rtk bash scripts/devkit.sh validate --strict
```

## Failure Handling
- 缺少可度量验收标准时停在 `propose`。
- shared contract 变更未列出影响面时升级架构评审。
- 回归失败时返回 `apply`，不得弱化测试或删除失败证据。

## Quality Gate
- 每个功能必须可追溯到需求、设计、任务和测试。
- 没有验证证据不得进入 `review-passed`。
