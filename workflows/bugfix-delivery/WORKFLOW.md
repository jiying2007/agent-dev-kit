---
name: bugfix-delivery
description: 缺陷复现、根因定位、回归验证和审查闭环工作流
version: 1.0.0
last_updated: 2026-06-01
primary_agent: application-engineer
primary_skill: adk-systematic-debugging
triggers:
  - "缺陷修复"
  - "bugfix"
  - "回归测试"
profiles:
  - embedded-fullstack
command_risk: low
stages:
  - reproduce
  - diagnose
  - apply
  - verify
  - review
artifacts:
  - reproduction.md
  - root-cause.md
  - tasks.md
  - verify-report.md
  - review-report.md
verification:
  - "rtk bash tests/test_workflow.sh"
  - "rtk bash tests/test_integration.sh"
failure_handling:
  - "无法复现时停止修复并记录缺失条件"
  - "根因不明时不得提交猜测性改动"
---

# bugfix-delivery

## Goal
- 先复现再定位，确保缺陷修复有根因、有回归测试、有审查闭环。
- 限制修复范围，避免把 bugfix 混成无关重构。

## Scope
- 适用于嵌入式全栈 profile 下的设备侧应用、上位机工具和组件缺陷修复。
- 不适用于发布版本策略和长期重构。

## Ownership
- Primary agent: `application-engineer`
- Primary skill: `adk-systematic-debugging`
- Supporting skills: `adk-task-breakdown`, `adk-verification-before-completion`, `adk-code-review-loop`

## Stage Contract
1. `reproduce`: 固定触发条件、输入、环境和期望行为。
2. `diagnose`: 形成根因假设，逐项验证并记录负结果。
3. `apply`: 实施最小修复和回归测试。
4. `verify`: 运行复现路径、回归测试和相关 smoke。
5. `review`: 审查根因真实性、修复范围和测试覆盖。

## Artifact Contract
- `reproduction.md` 记录复现步骤、环境和观察。
- `root-cause.md` 区分已证实事实、假设和负结果。
- `verify-report.md` 必须包含修复前后同口径验证。

## Commands
```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/check-workflow-closure.sh --profile embedded-fullstack
```

## Failure Handling
- 无法复现时输出 blocked，不进入代码修改。
- 根因证据不足时继续诊断，不用大范围重构掩盖问题。
- 回归失败时返回 `diagnose` 或 `apply`，并保留失败样例。

## Quality Gate
- 修复必须伴随回归测试或明确说明无法自动化的验证证据。
- review 不接受“看起来修好了”作为完成证据。
