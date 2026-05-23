# Spec Chain Delivery Runbook

## 适用场景

- 需求仍然模糊，需要先沉淀 `requirements -> design -> tasks` 链路再进入实现。
- 交付需要“单问题闭环”，避免一次变更夹带多个无关目标。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-adr-writer`
- `adk-task-breakdown`
- `adk-verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<spec 链路目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 先固化 `requirements.md`，再产出 `design.md`，最后落地 `tasks.md`。
- `tasks.md` 的每个任务必须能追溯到 `requirements.md` 中的验收条目。
- 需求包必须是单问题主线，发现多问题捆绑时先拆分再推进。
- 不使用“AI 生成代码量”“生成行数”或“工具调用次数”作为完成指标；这些只能作为过程信号，不能替代端到端业务价值、缺陷率、交付周期和可维护性证据。
- 代码进入生产前先视为维护负债。只有当它追溯到明确业务目标、接口契约、测试证据和回滚策略时，才可被计入有效资产。
- 存量系统变更必须优先左移：先还原 API、数据结构、状态机、关键业务链路和测试覆盖缺口，再进入实现。
- 新需求可用轻量原型辅助澄清，但原型不能绕过 `requirements -> design -> tasks -> verify` 链路直接进入生产。

## Spec 链路模板

```md
- Problem Statement:
- E2E Value Metric:
- Requirements Baseline:
- Design Decisions:
- API / State Model:
- Task Slices + Acceptance:
- Left-Shift Checks:
- Risk / Rollback:
```

## 验收门禁

- `proposal.md` 必须包含单问题陈述与非目标。
- `design.md` 必须包含关键决策与拒绝方案。
- `tasks.md` 必须包含 owner、done criteria、验证命令。
- `review-report` 必须说明本次变更如何避免只增加代码负债，以及采用了哪些 E2E 价值或质量指标。
- 缺失任一链路工件时，结论固定为 `needs-fix`。
