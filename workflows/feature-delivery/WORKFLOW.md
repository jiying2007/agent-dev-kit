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

## SDD 最小路径（不新增平行 Workflow）
- **开始之前**：用户的明确方案可直接进入受许可的实现；需求未决且决策代价高时才使用只读 Explore/Challenge，不将头脑风暴设为所有需求的固定前置。
- **propose**：将变更的行为差异写入已有 `docs/changes/<change-id>/proposal.md` 的 Canonical Change Contract；每个 `REQ-NNN` 关联 `ADDED/MODIFIED/REMOVED`、影响面、`ACC-NNN` 和可证伪的负例。对原有规格只写 delta；小修或非行为变更不强迫创建空 spec 文件。
- **apply**：复杂接口/跨仓协议先完成 owner、状态、超时、错误、兼容和恢复设计；实施者按 `TASK-NNN` 逐切片提交代码和测试，跨仓契约仅一处写入，单仓不能自证双端联调完成。
- **verify/review**：以 `VERIFY-NNN` 对正例/反例运行定向测试，记录真实命令与退出码；反向核对新增、删除或变化的可观察代码是否有对应规格，缺失标 `not-checked`。review 不凭文档完整度放行。
- 操作例与轻重分级见 `docs/runbooks/spec-driven-delivery.md`。本 Workflow 保持原 `propose/apply/verify/review/archive` 生命周期、权限和既有工件结构。

## Quality Gate
- 每个功能必须可追溯到需求、设计、任务和测试。
- 没有验证证据不得进入 `review-passed`。
