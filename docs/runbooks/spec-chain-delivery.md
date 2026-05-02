# Spec Chain Delivery Runbook

## 适用场景

- 需求仍然模糊，需要先沉淀 `requirements -> design -> tasks` 链路再进入实现。
- 交付需要“单问题闭环”，避免一次变更夹带多个无关目标。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `adr-writer`
- `task-breakdown`
- `verification-before-completion`

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

## Spec 链路模板

```md
- Problem Statement:
- Requirements Baseline:
- Design Decisions:
- Task Slices + Acceptance:
- Risk / Rollback:
```

## 验收门禁

- `proposal.md` 必须包含单问题陈述与非目标。
- `design.md` 必须包含关键决策与拒绝方案。
- `tasks.md` 必须包含 owner、done criteria、验证命令。
- 缺失任一链路工件时，结论固定为 `needs-fix`。
