# Workflow Guide

## 核心流程（默认）

1. `propose`：定义背景、目标、非目标、风险与回退。
2. `apply`：实施代码与文档改动，状态标记为已应用。
3. `verify`：执行工件检查、结构校验与格式检查，生成验证报告。
4. `review`：按 blocker/major/minor 分级评审并给出 `pass/needs-fix`。
5. `archive`：仅在 `review-passed` 后归档，形成可追溯历史。

阶段流转硬约束：
- `apply` 仅允许从 `proposed` 进入
- `verify` 仅允许从 `applied` 进入
- `review` 仅允许从 `verified` 进入
- `archive` 仅允许从 `review-passed` 进入（`--force` 除外）

`propose` 工件新增强制检查：
- `proposal.md` 必须包含：`问题陈述（单问题）`、`上下文充分性检查`、`Core/Optional 边界检查`、`变更重复性检查`、`Breaking Change 检查`
- `tasks.md` 必须包含：`Ownership 与并行冲突检查`
- `negative-results.md` 必须包含：`已验证的负结果`

可选增强：
- `catalog build`：在变更启动前生成当前 Agent/Skill 能力目录，便于选型。
- `match`：把任务描述输入匹配器，快速筛选可触发 skill。

## 场景建议

### 场景 A：新功能迭代

- Agent：`requirements-analyst -> architecture-planner -> application-engineer`
- Skill：`requirements-triage + adr-writer + task-breakdown + unit-test-embedded + verification-before-completion`
- 命令：先 `propose`，开发完成后 `verify -> review -> archive`
- Runbook：`docs/runbooks/feature-delivery.md`

### 场景 B：驱动 Bring-up

- Agent：`driver-engineer -> component-engineer -> test-validation-engineer`
- Skill：`register-map-design + driver-bringup-checklist + interrupt-dma-patterns + integration-hil-sil + systematic-debugging`
- 命令：`propose` 后逐步落地，`verify` 必须含 HIL/SIL 证据，`review` 闭环后归档
- Runbook：`docs/runbooks/driver-bringup.md`

### 场景 C：发布前收口

- Agent：`test-validation-engineer -> security-compliance-reviewer -> build-release-engineer`
- Skill：`static-analysis-c-cpp + fault-injection-recovery + release-versioning + commit-pr-quality-gate + verification-before-completion`
- 命令：`verify` + `review --result pass` 后再 `archive`
- Runbook：`docs/runbooks/release-hardening.md`

### 场景 D：线上事故复盘（可选技能）

- Agent：`application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`incident-rca-report + test-flakiness-triage + systematic-debugging`
- 命令：先 `install --with-optional-skill incident-rca-report`，再 `propose -> apply -> verify -> review`

### 场景 E：高风险变更的轻量产物门禁（可选配置）

- Agent：`architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`artifact-gated-lite + verification-before-completion + commit-pr-quality-gate`
- 命令：
  1. `install --extra-profile artifact-gated-lite --with-optional-skill artifact-gated-lite`
  2. `propose -> apply -> verify -> review`
  3. `review` 结论必须与 `artifact:ReviewReport` / `artifact:TestReport` 一致
- 适用条件：变更涉及共享契约、发布链路、跨角色交接，且需要可追溯交付证据

## 变更工件约定

- `proposal.md`：为什么做、做什么、不做什么
- `design.md`：架构影响、配置影响、验证策略
- `tasks.md`：可执行任务清单
- `checklist.md`：交付门禁
- `negative-results.md`：被证伪假设与不采用方案留痕
- `review-report.md`：分级评审结论与闭环状态
- `state.yaml/history.log`：状态轨迹与时间线
