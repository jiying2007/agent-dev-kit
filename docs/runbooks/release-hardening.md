# Release Hardening Runbook

## 适用场景

- 版本切版前收口
- 需要压实稳定性、安全性、发布可回滚性

## 推荐 Agent 链

`test-validation-engineer -> security-compliance-reviewer -> build-release-engineer -> code-review-governor`

## 推荐 Skill 组合

- `release-versioning`
- `static-analysis-c-cpp`
- `fault-injection-recovery`
- `performance-profiling-embedded`
- `verification-before-completion`
- `commit-pr-quality-gate`

可选增强（按需安装）：
- `incident-rca-report`
- `test-flakiness-triage`

## 命令模板

```bash
bash scripts/devkit.sh install --tool codex --profile core --extra-profile release-hardening --with-optional-skill incident-rca-report
bash scripts/devkit.sh propose --change <change-id> --title "发布收口"
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change <change-id>
```

## 验收门禁

- 版本说明包含变更摘要、兼容性说明、回滚版本
- 故障注入/回归验证结果入档
- 关键风险项有 owner 与截止时间
- 若存在 breaking change，必须包含迁移窗口与回退触发条件
- 评审报告中 blocker/major 必须为 0
- 若触及发布脚本或构建入口，必须附 release gate 专项验证证据
- contribution checklist（影响面、验证口径、兼容性说明）必须完整
