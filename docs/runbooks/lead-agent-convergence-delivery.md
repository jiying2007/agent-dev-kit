# Lead-Agent Convergence Delivery Runbook

## 适用场景

- 任务跨多轮推进，需在“分析/执行/收敛”间做模式切换。
- 需要轻量工件保证多角色协作可追踪，但不引入过重流程。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh propose --change <change-id> --title "<收敛目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 每轮先判定执行模式：`diagnosis-first` / `repro-first` / `planning-first` / `execution-first`。
- 采用轻量三工件：`需求梳理`、`task checklist`、`执行反馈/验收记录`。
- 当继续抽象收益不明确时，必须从“继续分析”切换到“收敛执行”。
- 对复杂、非常规或高风险架构决策，可进入 `debate-first` 模式，让不同角色分别从需求、架构、测试、安全、运维角度挑战方案。
- 辩论式协作只用于暴露盲点和收敛决策，不用于制造多个互相冲突的执行计划；最终必须由主 Agent 归并为单一结论、拒绝方案和验证路径。
- 辩论参与者的输出必须包含 evidence、risk、counterexample 和 recommendation；没有证据的观点不得升级为门禁。

## 收敛模板

```md
- Work Mode:
- Current Goal:
- Debate Findings:
- Task Checklist:
- Validation Summary:
- Known Leftovers:
- Convergence Decision:
```

## 验收门禁

- 必须给出当前模式与切换理由。
- `review-report` 必须包含“可放行最小条件”或“收敛结论”。
- 若无收敛结论且无阻塞说明，结论固定为 `needs-fix`。
