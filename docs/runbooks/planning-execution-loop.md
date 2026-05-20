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
- `goal-closure.md`：原始目标、完成声明、证据、open items、停止条件。
- `repair-ledger.md`：失败范围、保留的通过项、最小重跑命令、回退锚点。

## 目标闭环与卡死保护

- 每个长任务开始时记录 `goal_statement`、done criteria、`retry_budget` 和 `staleness_threshold`。
- 每个 checkpoint 更新 heartbeat：当前阶段、最新动作、下一步、阻塞和是否有信息增量。
- 进入完成声明前，先生成 `completion_claim`，再由 `adk-verification-before-completion` 独立核对证据。
- retry budget 用尽、heartbeat 过期或连续无信息增量时，必须 replan、split、blocked 或 abort，不能继续盲目推进。

## 失败修复策略

- 失败后先确认最小失败范围：输入、文件、模块、测试、设备阶段或运行环境。
- 修复前写 repair note：failed scope、passing scope to preserve、minimal rerun、rollback anchor。
- 已通过产物默认保留；只重跑最小失败项，除非共享契约或全局配置发生变化。
- schema/格式正确不代表语义正确，语义修复后仍需走完成前证据核验。

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
- 目标闭环记录能从原始目标追溯到完成声明、证据和剩余风险。
- 失败修复记录包含最小失败范围、保留通过项和最小重跑证据。
- 完成声明前必须通过 completion gate。
- checkpoint 写入后必须可读、可追溯，并且无孤儿临时状态。
- 临时参考材料只能作为背景输入，不能未经评估进入长期知识或 adoption matrix。
