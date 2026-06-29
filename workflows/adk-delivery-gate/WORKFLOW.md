---
name: adk-delivery-gate
description: agent-dev-kit 通用资产生产交付门禁
version: 1.0.0
last_updated: 2026-06-29
primary_agent: code-review-governor
primary_skill: adk-verification-before-completion
triggers:
  - "优化 adk"
  - "agent-dev-kit 交付"
  - "嵌入式资产发布"
  - "完成前验证"
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
  - negative-results.md
  - verify-report.md
  - review-report.md
verification:
  - "rtk bash scripts/devkit.sh validate --strict"
  - "rtk bash tests/run_all.sh --fail-fast"
failure_handling:
  - "review 出现 blocker 时返回 apply 修复并重新 verify"
  - "验证无法执行时记录原因、影响和剩余风险"
---

# adk-delivery-gate

## Goal
- 将 agent-dev-kit 资产变更收敛到可追溯、可验证、可审查的交付闭环。
- 防止 Agent、Skill、Workflow、manifest、脚本和文档之间出现声明与行为漂移。

## Scope
- 适用于 `agent-dev-kit` 内 Agent、Skill、Workflow、manifest、script、template、schema 和 docs 的生产级变更。
- 不替代具体领域 Skill 的执行步骤；领域步骤仍由 primary/supporting skills 承担。

## Ownership
- Primary agent: `code-review-governor`
- Primary skill: `adk-verification-before-completion`
- Supporting skills: `adk-runtime-router`, `adk-requirements-triage`, `adk-task-breakdown`, `adk-test-strategy`, `adk-code-review-loop`, `adk-after-action-review`, `adk-token-context-governance`, `adk-commit-pr-quality-gate`

## Stage Contract
1. `propose`: 固定目标、非目标、影响面、重复能力检查、风险和回退。
2. `apply`: 只实施已声明范围内的资产变更，避免无关格式化和重构。
3. `verify`: 运行结构、闭包、格式和相关回归检查，生成验证证据。
4. `review`: 按 blocker/major/minor 分级审查，结论必须与证据一致。
5. `archive`: 仅在 review 通过后归档变更工件。

## Artifact Contract
- 必需工件：`proposal.md`, `design.md`, `tasks.md`, `negative-results.md`, `verify-report.md`, `review-report.md`。
- 高风险变更必须补充 artifact 标签、回滚方案和人工审批点。
- 验证命令、退出码和证据路径必须可复查。

## Commands
```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash scripts/check-workflow-closure.sh --profile core
rtk bash tests/run_all.sh --fail-fast
```

## Failure Handling
- 结构或闭包检查失败时先修 manifest、path、profile 或 workflow contract，再继续。
- review 有 blocker 时返回 apply 阶段修复，修复后重新 verify 和 review。
- 验证无法执行时不得声明完成，必须记录原因、影响和剩余风险。

## Quality Gate
- `manifest.yaml` 的 workflow 条目必须指向本文件，并声明 primary agent、primary skill、supporting skills、commands 和 verification。
- Workflow 引用的 Agent/Skill 必须在所选 profile 闭包内可用。
- 完成声明必须有可复查的命令证据。
- 中高风险交付必须附 Completion Guard Payload；必需检查未通过、缺少证据路径或缺少 verifier 时，不得把任务状态标记为完成。
