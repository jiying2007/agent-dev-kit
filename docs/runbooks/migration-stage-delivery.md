# Migration Stage Delivery Runbook

## 适用场景

- 需要把旧实现逐步迁移到新实现，且迁移期存在“双实现并存”阶段。
- 变更跨多个模块，必须按里程碑分阶段验收与回退。

## 推荐 Agent 链

`architecture-planner -> application-engineer -> test-validation-engineer -> build-release-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-release-versioning`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh propose --change <change-id> --title "<迁移目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 明确三类目录边界：`参考基线（只读）`、`中间验证层（可回归）`、`目标实现层（最终交付）`。
- 每个里程碑必须输出阶段结论：`baseline-aligned` / `migrate-ready` / `cutover-ready`。
- 阶段切换前必须完成同口径验证，禁止直接跨阶段推进。
- 每个里程碑必须绑定回退锚点（tag/commit/change-id）。

## 阶段验收模板

```md
## Stage <N>
- Scope:
- Source Baseline:
- Target Increment:
- Verification Commands:
- Evidence Index:
- Rollback Anchor:
- Stage Decision:
```

## 验收门禁

- `tasks.md` 必须包含里程碑拆分、owner、阶段依赖与冲突矩阵。
- `verify-report` 必须包含至少一条“旧实现 vs 新实现”的同口径对比证据。
- 缺少回退锚点或阶段结论不明确，结论固定为 `needs-fix`。
