# Upstream Intake Runbook

## 目标

把参考仓更新转成可追踪、可裁剪、可验证的 adk 候选项。

## 流程

1. `sync-subrepos` 拉取参考仓更新。
2. `diff-scan` 生成变化报告。
3. `adoption-matrix` 做 `adopt/observe/reject` 决策。
4. adopt 项必须声明 `core/optional/profile/reject` 归属。
5. 落地 Agent/Skill/Workflow 至少一层。
6. 回归通过后先进入 `~/codex` 治理链路，再由 `~/codex` apply 到 `~/.codex` pilot。

## 临时参考素材边界

- 本地临时文章、网页摘录和一次性调研目录只作为背景输入，不作为正式参考子仓。
- 临时素材不得直接写入 `adoption-matrix`、长期 knowledge 或 profile；只有被提升为受治理来源后才进入正式 intake。
- 从临时素材提炼出的做法必须先抽象成通用规则，再合并到已有 skill/runbook/template。
- 临时素材移除后，正式资产仍必须能独立说明目标、约束、验证和回滚。

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
- 不能直接把第三方资产混装进 `~/.codex`；必须先经过 adk 审查，再进入 `~/codex`。
- 临时参考素材不得成为完成声明的唯一证据。
