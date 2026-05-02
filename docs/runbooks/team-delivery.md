# Team Delivery Runbook

## 目标

把团队协作从口头交接升级为责任、证据和签收可追溯的交付流程。

## 推荐 profile

`team-core`

## 推荐组合

- Agent：`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`
- Primary Skill：`cross-team-handoff`
- Supporting Skills：`task-breakdown`、`verification-before-completion`

## 工件

- Owner Matrix：R/A/C。
- Section Ownership：每个模块或文档一个主负责人。
- Handoff Token：ready_to_handoff、receiver、acceptance evidence。
- Sign-off：交接方、接收方、批准方。

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<团队交付目标>"
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 验收门禁

- 缺少 Owner Matrix 不得进入交接完成态。
- 接收方未复验不得声明签收完成。
- review 阶段缺 handoff contract 时结论固定为 `needs-fix`。
