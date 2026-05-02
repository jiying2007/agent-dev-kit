# Prompt Evolution Delivery Runbook

## 适用场景

- 变更以提示词、流程文本、策略文案为主。
- 需要证明“文本变更”确实改善行为，而不是只改描述。

## 推荐 Agent 链

`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `task-breakdown`
- `verification-before-completion`
- `commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<prompt 演进目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 变更前必须保存 baseline prompt snapshot。
- 至少保留一组“同输入对比”证据（before/after）。
- 失败样例必须入档，禁止只展示成功样例。
- 关键验证命令必须入命令级 Evidence Index（命令/退出码/结果摘要/证据路径/层级）。

## Prompt 回归模板

```md
- Prompt Baseline:
- Prompt Update:
- Test Inputs:
- Before/After Diff:
- Failure Cases:
- Evidence Index (command/exit_code/result_summary/evidence_path/layer):
- Final Decision:
```

## 验收门禁

- `verify-report` 必须包含 prompt 回归证据（含至少一条失败样例）与命令级 Evidence Index。
- 若只改文本且无行为对比证据，结论固定为 `needs-fix`。
