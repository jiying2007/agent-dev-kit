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

`review` 一致性新增硬约束：
- 若变更工件中存在 `[artifact:ReviewReport]` / `[artifact:TestReport]`，则 `review --result` 必须与 artifact 结论一致
- `review --result pass` 时，`ReviewReport.status` 与 `TestReport.status` 必须同时为 `PASS`

`propose` 工件新增强制检查：
- `proposal.md` 必须包含：`问题陈述（单问题）`、`上下文充分性检查`、`Core/Optional 边界检查`、`变更重复性检查`、`Breaking Change 检查`
- `tasks.md` 必须包含：`Ownership 与并行冲突检查`
- `negative-results.md` 必须包含：`已验证的负结果`

可选增强：
- `catalog build`：在变更启动前生成当前 Agent/Skill 能力目录，便于选型。
- `match`：把任务描述输入匹配器，快速筛选可触发 skill。

## 场景建议

说明：下列 `Skill` 列表均按 `Primary -> Supporting` 排列；第一个为主技能，其余只补充检查项，不抢占入口。若场景需要多个可选技能，必须先确认 profile/安装范围，再执行匹配。

### 场景 A：新功能迭代

- Agent：`requirements-analyst -> architecture-planner -> application-engineer`
- Skill：`adk-requirements-triage + adk-adr-writer + adk-task-breakdown + adk-unit-test-embedded + adk-verification-before-completion`
- 命令：先 `propose`，开发完成后 `verify -> review -> archive`
- Runbook：`docs/runbooks/feature-delivery.md`

### 场景 B：驱动 Bring-up

- Agent：`driver-engineer -> component-engineer -> test-validation-engineer`
- Skill：`adk-register-map-design + adk-driver-bringup-checklist + adk-interrupt-dma-patterns + adk-integration-hil-sil + adk-systematic-debugging`
- 命令：`propose` 后逐步落地，`verify` 必须含 HIL/SIL 证据，`review` 闭环后归档
- Runbook：`docs/runbooks/driver-bringup.md`

### 场景 C：发布前收口

- Agent：`test-validation-engineer -> security-compliance-reviewer -> build-release-engineer`
- Skill：`adk-static-analysis-c-cpp + adk-fault-injection-recovery + adk-release-versioning + adk-commit-pr-quality-gate + adk-verification-before-completion`
- 命令：`verify` + `review --result pass` 后再 `archive`
- Runbook：`docs/runbooks/release-hardening.md`

### 场景 D：线上事故复盘（可选技能）

- Agent：`application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-incident-rca-report + adk-test-flakiness-triage + adk-systematic-debugging`
- 命令：先 `install --with-optional-skill adk-incident-rca-report`，再 `propose -> apply -> verify -> review`

### 场景 E：高风险变更的产物门禁

- Agent：`architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-artifact-gating + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：
  1. `install --profile core`
  2. `propose -> apply -> verify -> review`
  3. `review` 结论必须与 `artifact:ReviewReport` / `artifact:TestReport` 一致
- 适用条件：变更涉及共享契约、发布链路、跨角色交接，且需要可追溯交付证据

### 场景 F：缺陷修复闭环（Bugfix）

- Agent：`application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-systematic-debugging + adk-task-breakdown + adk-verification-before-completion`
- 命令：`propose -> apply -> verify -> review -> archive`
- 关键纪律：禁止“顺手重构”无关区域；必须保留负结果证据
- Runbook：`docs/runbooks/bugfix-delivery.md`

### 场景 G：重构压实（Refactor）

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-component-api-stability + adk-unit-test-embedded + adk-verification-before-completion`
- 命令：`propose -> apply -> verify -> review -> archive`
- 关键纪律：基线验证与重构后回归必须同口径对比
- Runbook：`docs/runbooks/refactor-hardening.md`

### 场景 H：codex 运行闭环（Runtime Pilot）

- Agent：`application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`~/codex doctor/apply dry-run -> health-check(~/.codex) -> check-global-codex-health -> check-adk-harden-readiness --require-pilot`
- 关键纪律：未通过 pilot 验证不得给出“可放行/可追踪上游更新”结论
- Runbook：`docs/runbooks/codex-runtime-pilot.md`

### 场景 I：跨团队交接收口（Handoff Delivery）

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-task-breakdown + adk-cross-team-handoff + adk-verification-before-completion`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：Owner Matrix、Section Ownership、Sign-off 三项缺一不可
- Runbook：`docs/runbooks/adk-cross-team-handoff-delivery.md`

### 场景 J：大型工程交付收口（Large Platform Delivery）

- Agent：`architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-commit-pr-quality-gate + adk-verification-before-completion`
- 命令：`catalog -> propose -> apply -> verify -> review`
- 关键纪律：先给 module ownership map，再执行跨模块改动
- Runbook：`docs/runbooks/large-platform-delivery.md`

### 场景 K：证据索引化交付（Evidence Index Delivery）

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-systematic-debugging + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：验证命令必须索引化记录（命令/退出码/证据路径）
- Runbook：`docs/runbooks/evidence-index-delivery.md`

### 场景 L：阶段式迁移交付（Migration Stage Delivery）

- Agent：`architecture-planner -> application-engineer -> test-validation-engineer -> build-release-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-release-versioning + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`catalog -> propose -> apply -> verify -> review`
- 关键纪律：必须按里程碑输出阶段结论与回退锚点，禁止跳阶段推进
- Runbook：`docs/runbooks/migration-stage-delivery.md`

### 场景 M：配置基线治理（Config Baseline Governance）

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：配置摘要、验证命令、行为影响结论三项缺一不可
- Runbook：`docs/runbooks/config-baseline-governance.md`

### 场景 N：codex 设置审计（Codex Settings Audit）

- Agent：`requirements-analyst -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`propose -> verify -> check-global-codex-health -> codex mcp list -> review`
- 关键纪律：声明配置与运行态加载结果必须一致
- Runbook：`docs/runbooks/codex-settings-audit.md`

### 场景 O：Spec 链路交付（Spec Chain Delivery）

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-adr-writer + adk-task-breakdown + adk-verification-before-completion`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：`requirements/design/tasks` 三段链路缺一不可
- Runbook：`docs/runbooks/spec-chain-delivery.md`

### 场景 P：技能候选筛选交付（Skill Curation Delivery）

- Agent：`requirements-analyst -> architecture-planner -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-commit-pr-quality-gate + adk-verification-before-completion`
- 命令：`catalog -> match -> validate --strict -> review`
- 关键纪律：必须声明 `global-ready/project-bound` 与 `core/optional/reject` 归属结论
- Runbook：`docs/runbooks/skill-curation-delivery.md`

### 场景 Q：Prompt 演进交付（Prompt Evolution Delivery）

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：必须保留 before/after 对比与失败样例证据
- Runbook：`docs/runbooks/prompt-evolution-delivery.md`

### 场景 R：Lead-Agent 收敛交付（Lead-Agent Convergence Delivery）

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-requirements-triage + adk-task-breakdown + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`catalog -> propose -> apply -> verify -> review`
- 关键纪律：先判定模式，再推进执行，最后输出收敛结论
- Runbook：`docs/runbooks/lead-agent-convergence-delivery.md`

### 场景 S：生产运行路由（Runtime Routing）

- Agent：`requirements-analyst -> architecture-planner -> code-review-governor`
- Skill：`adk-skill-composition-governance + adk-verification-before-completion`
- 命令：`catalog -> match -> check-runtime-routing`
- 关键纪律：一个场景只能有一个主 skill，辅助 skill 不抢占入口
- Runbook：`docs/runbooks/runtime-routing.md`

### 场景 T：长任务计划执行（Planning Execution Loop）

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-planning-execution-loop + adk-task-breakdown + adk-verification-before-completion`
- 命令：`propose -> apply -> verify -> review`
- 关键纪律：每个阶段必须有检查点、恢复摘要和验证证据
- Runbook：`docs/runbooks/adk-planning-execution-loop.md`

### 场景 U：生产部署（Production Deployment）

- Agent：`build-release-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-release-versioning + adk-verification-before-completion + adk-commit-pr-quality-gate`
- 命令：`validate -> install --backup --install-report -> check-global-codex-health -> check-adk-harden-readiness`
- 关键纪律：生产安装必须可回滚，并记录安装报告
- Runbook：`docs/runbooks/production-deployment.md`

### 场景 V：上游吸收（Upstream Intake）

- Agent：`requirements-analyst -> architecture-planner -> code-review-governor`
- Skill：`adk-skill-composition-governance + adk-security-supply-chain + adk-commit-pr-quality-gate`
- 命令：`sync-subrepos -> diff-scan -> check-upstream-intake-readiness`
- 关键纪律：参考资产不得直接混装进 `~/.codex`；必须先经过 adk，再进入 `~/codex`，最后由 `~/codex` apply
- Runbook：`docs/runbooks/upstream-intake.md`

### 场景 W：团队生产交付（Team Delivery）

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Skill：`adk-task-breakdown + adk-cross-team-handoff + adk-verification-before-completion`
- 命令：`propose -> verify -> review`
- 关键纪律：Owner Matrix、handoff token、接收方复验三项缺一不可
- Runbook：`docs/runbooks/team-delivery.md`

## 变更工件约定

- `proposal.md`：为什么做、做什么、不做什么
- `design.md`：架构影响、配置影响、验证策略
- `tasks.md`：可执行任务清单
- `checklist.md`：交付门禁
- `negative-results.md`：被证伪假设与不采用方案留痕
- `review-report.md`：分级评审结论与闭环状态
- `state.yaml/history.log`：状态轨迹与时间线
