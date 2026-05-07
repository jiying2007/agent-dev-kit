# Upstream Intake Runbook

## 目标

把参考仓更新转成可追踪、可裁剪、可验证的 gdk 候选项。

## 流程

1. `sync-subrepos` 拉取参考仓更新。
2. `diff-scan` 生成变化报告。
3. `adoption-matrix` 做 `adopt/observe/reject` 决策。
4. adopt 项必须声明 `core/optional/profile/reject` 归属。
5. 落地 Agent/Skill/Workflow 至少一层。
6. 回归通过后再进入 `~/.codex` pilot。

## 技能路由

- Primary Skill：`adk-skill-composition-governance`
- Supporting Skills：`adk-security-supply-chain`、`adk-commit-pr-quality-gate`
- Fallback：若候选涉及安全、依赖或脚本执行风险，先切到 `adk-security-supply-chain`，审查通过后再回到组合治理。

## 命令模板

```bash
bash ../scripts/sync-subrepos.sh . fetch
bash ../scripts/diff-scan.sh . 7 reports/weekly-change-report.md
bash ../scripts/check-upstream-intake-readiness.sh .
```

## 验收门禁

- `adoption-matrix` 不允许真实 pending。
- `adopt + done` 必须有本地证据。
- 不能直接把第三方资产混装进 `~/.codex`。
