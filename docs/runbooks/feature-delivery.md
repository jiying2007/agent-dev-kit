# Feature Delivery Runbook

## 适用场景

- 新功能从需求澄清进入可交付实现
- 涉及多个模块但不引入基础设施级改动

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `task-breakdown`
- `adr-writer`
- `interface-contract-design`
- `unit-test-embedded`
- `verification-before-completion`
- `commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

## 验收门禁

- 需求边界、非目标、风险在 `proposal.md` 可追溯
- 关键接口/状态机变更在 `design.md` 记录
- `proposal.md` 必须显式完成 breaking change 检查
- `negative-results.md` 至少记录一条被排除方案
- 验证报告包含至少一条回归证据
- 评审结果必须为 pass，且 blocker/major 为 0
