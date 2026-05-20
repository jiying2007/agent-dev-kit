# Planning Execution Loop Runbook

## 目标

把复杂任务转成可审查、可恢复、可验证的阶段执行闭环。

## 适用场景

- 已有计划需要持续执行。
- 任务跨会话、跨阶段或有多个验证检查点。
- 需要从参考仓吸收能力并落到 adk 资产。

## 推荐组合

- Agent：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- Primary Skill：`adk-planning-execution-loop`
- Supporting Skills：`adk-task-breakdown`、`adk-verification-before-completion`

## 工件

- `PROJECT.md`：目标、边界、非目标、长期约束。
- `REQUIREMENTS.md`：可证伪需求、验收条件、开放问题。
- `PLAN.md`：阶段、依赖、done criteria、验证命令。
- `session-state.md`：当前阶段、已完成项、未闭环项。
- `next-actions.md`：下一步命令和完成标准。
- `risk-ledger.md`：风险、阻塞、被证伪路径。
- `resume-prompt.md`：新会话恢复入口。
- `SUMMARY.md`：会话压缩摘要和最终交接上下文。

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 验收门禁

- 每个阶段都有 done criteria 与验证证据。
- 恢复工件足够让新会话继续执行。
- 完成声明前必须通过 completion gate。
- checkpoint 写入后必须可读、可追溯，并且无孤儿临时状态。
- 临时参考材料只能作为背景输入，不能未经评估进入长期知识或 adoption matrix。
