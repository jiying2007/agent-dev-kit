# Evidence Index Delivery Runbook

## 适用场景

- 嵌入式全栈交付需要强证据链（命令、结果、产物路径）并可审计回放。
- 需要把“执行过程”沉淀为结构化证据索引，避免口头结论。

## 推荐 Agent 链

`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-systematic-debugging`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<证据化交付目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 每条关键验证命令必须记录：命令、退出码、结果摘要、证据文件路径、层级（Agent/Skill/Workflow）。
- 对失败验证也必须入索引，禁止只记录成功项。
- 结论声明前先完成 Evidence Index，禁止“先结论后补证据”。
- Evidence Index 至少包含一条负结果证据，并关联到对应工件（`negative-results`/`verify-report`/`review-report`）。

## Evidence Index 最小模板

```md
- Command:
- Exit Code:
- Result Summary:
- Evidence Path:
- Layer:
- Related Artifact:
- Owner:
```

## 验收门禁

- `verify-report`/`review-report` 中必须可追溯到 Evidence Index，且字段完整（命令/退出码/结果摘要/证据路径/层级）。
- 至少包含一条负结果证据（失败或被证伪路径）。
- 若证据索引缺失，结论固定为 `needs-fix`。
