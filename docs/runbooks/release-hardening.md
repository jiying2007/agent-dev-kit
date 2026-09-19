# Release Hardening Runbook

## 适用场景

- 版本切版前收口
- 需要压实稳定性、安全性、发布可回滚性

## 推荐 Agent 链

`test-validation-engineer -> security-compliance-reviewer -> build-release-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-release-versioning`
- `adk-static-analysis-c-cpp`
- `adk-fault-injection-recovery`
- `adk-performance-profiling-embedded`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

可选增强（按需安装）：
- `adk-incident-rca-report`
- `adk-test-flakiness-triage`

## 命令模板

```bash
bash scripts/devkit.sh export --target claude-code --profile core --extra-profile release-hardening --with-optional-skill adk-incident-rca-report --out ../reports/adk-handoff --clean
bash scripts/devkit.sh security check --summary-json
bash scripts/devkit.sh release check --summary-json
bash scripts/devkit.sh release build --out dist --summary-json
bash scripts/devkit.sh release rehearse --previous-artifact <previous-current-contract.tar.gz> --candidate-artifact <candidate.tar.gz>
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
- release rehearsal 只接受当前 strict source contract 与 release-manifest v2；pre-contract/legacy bundle 必须 fail closed，不提供迁移执行兼容层
- contribution checklist（影响面、验证口径、兼容性说明）必须完整
- 正式发布只合入受保护 `main`；successful-main CI 后由 `release-tag-promotion` 创建 exact-SHA annotated SemVer tag，再调用 canonical release workflow。
- 同版本 tag 若已指向不同 commit 必须 fail closed 并提升 SemVer，禁止移动或覆盖旧 tag。
- canonical release 必须发布 GitHub Release，并让远端 assets 与本轮 validated archive/checksum/release-contract 保持 byte-identical；重跑不得静默覆盖。
