---
name: release-hardening
description: 发布前安全、性能、版本、回滚和放行证据收口工作流
version: 1.0.0
last_updated: 2026-06-01
primary_agent: build-release-engineer
primary_skill: adk-release-versioning
triggers:
  - "准备发布"
  - "发布前检查"
  - "release hardening"
profiles:
  - release-hardening
command_risk: medium
stages:
  - baseline
  - harden
  - verify
  - review
  - release-decision
artifacts:
  - release-notes.md
  - verify-report.md
  - review-report.md
  - rollback-plan.md
verification:
  - "rtk bash tests/test_validate.sh"
  - "rtk bash tests/test_profile_coherence.sh"
failure_handling:
  - "缺少回滚方案时不得发布"
  - "安全或合规 blocker 必须修复或显式接受风险"
---

# release-hardening

## Goal
- 在发布前收敛版本、验证、安全、性能、回滚和放行证据。
- 让发布结论可追溯、可复查、可回滚。

## Scope
- 适用于 release-hardening profile 下的发布准备和放行检查。
- 不替代具体构建系统或部署平台的执行脚本。

## Ownership
- Primary agent: `build-release-engineer`
- Primary skill: `adk-release-versioning`
- Supporting skills: `adk-test-strategy`, `adk-code-review-loop`, `adk-branch-closeout`, `adk-verification-before-completion`, `adk-commit-pr-quality-gate`

## Stage Contract
1. `baseline`: 固定版本、变更范围、依赖和发布目标。
2. `harden`: 执行安全、性能、兼容性和配置检查。
3. `verify`: 收集构建、测试、制品和回滚验证证据。
4. `review`: 审查 blocker、重大风险和人工审批点。
5. `release-decision`: 给出 release / hold / rollback-prep 结论。

## Artifact Contract
- `release-notes.md` 必须包含版本、变更、兼容性和已知问题。
- `rollback-plan.md` 必须包含触发条件、步骤和验证方式。
- `verify-report.md` 必须列出发布门禁命令和结果。

## Commands
```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/check-workflow-closure.sh --profile release-hardening
```

## Failure Handling
- 制品不可复现或校验缺失时结论为 hold。
- 回滚不可验证时不得进入 release 决策。
- 安全 blocker 未闭环时必须暂停或记录人工风险接受。

## Quality Gate
- 发布结论必须绑定版本、制品、验证证据和回滚路径。
- 任何无法执行的验证必须说明影响和剩余风险。
