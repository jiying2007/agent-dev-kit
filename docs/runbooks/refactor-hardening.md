# Refactor Hardening Runbook

## 适用场景

- 需要跨文件/跨模块重构，目标是提升结构质量且保持行为不变。
- 涉及公共组件、共享接口或高回归风险路径。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `task-breakdown`
- `component-api-stability`
- `unit-test-embedded`
- `verification-before-completion`
- `commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<重构目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

## 执行纪律

- 先建立基线验证，再实施重构，再跑同口径回归。
- 每个子任务必须有 ownership 与 scope，禁止并行改同一 shared contract。
- 若行为变化不可避免，必须显式标注为 breaking change 并附迁移/回退方案。

## 验收门禁

- `proposal.md` 明确“本次重构保持行为不变”或显式声明 breaking change。
- `tasks.md` 必须具备 ownership 与并行冲突检查结果。
- `verify-report.md` 必须包含“基线结果 vs 重构后结果”的对比证据。
- 若存在 blocker 或 major 未闭环，结论固定为 `needs-fix`。
