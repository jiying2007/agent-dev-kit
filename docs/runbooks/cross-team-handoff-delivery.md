# Cross-Team Handoff Delivery Runbook

## 适用场景

- 模块完成开发后需交接给其他团队继续维护或联调。
- 涉及共享接口、共享配置或多角色并行收口。

## 推荐 Agent 链

`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-task-breakdown`
- `adk-cross-team-handoff`（由 `team-core` 默认启用）
- `adk-verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<交接目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 必须冻结 Owner Matrix（R/A/C）和 Section Ownership。
- 每个交接项必须写明 `ready_to_handoff` 条件与接收人。
- 缺少签收记录不得宣称“交接完成”。

## 验收门禁

- 交接文档包含范围、风险、验收证据、回退路径、升级通道。
- `review` 阶段若缺 handoff contract，结论固定为 `needs-fix`。
- 关键交接项必须具备可复现验证命令与结果记录。
