# Large Platform Delivery Runbook

## 适用场景

- 代码仓规模大、模块多、职责分层明显的 Agent/平台型项目。
- 变更跨越多个子模块，且可能触及 `scripts/`、`gateway`、`agent` 等关键目录。

## 推荐 Agent 链

`architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-commit-pr-quality-gate`
- `adk-verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh propose --change <change-id> --title "<大仓交付目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 先输出模块责任图（module ownership map），再实施跨模块改动。
- 共享入口、发布脚本、网关命令注册等关键触点必须显式标注风险与回退。
- core/optional 边界必须明确，避免把场景化能力错误并入 core。

## 验收门禁

- `tasks.md` 必须包含 ownership 与冲突矩阵。
- 关键目录（如 `scripts/`、总入口、命令注册）改动必须有专项验证证据。
- 若跨模块改动无法给出责任边界或回退路径，结论固定为 `needs-fix`。
