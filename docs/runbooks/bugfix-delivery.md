# Bugfix Delivery Runbook

## 适用场景

- 已出现真实缺陷，且需要在当前迭代内修复闭环。
- 根因尚未确定，或者修复路径存在多种可能。

## 推荐 Agent 链

`application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-systematic-debugging`
- `adk-task-breakdown`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<缺陷修复目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

## 执行纪律

- 单轮实验只验证一个假设，记录正负结果。
- 禁止“顺手重构”无关模块；修复范围必须与缺陷范围一致。
- 先补证据再下结论，不允许“疑似修复”直接放行。

## 验收门禁

- `proposal.md` 必须明确现象、触发条件、影响范围与非影响范围。
- `negative-results.md` 必须至少记录一条被证伪假设。
- `verify-report.md` 必须包含“复现 -> 修复 -> 回归”证据链。
- `review` 结论为 `pass` 且 `blocker/major=0` 后才可归档。
