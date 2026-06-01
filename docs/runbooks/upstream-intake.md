# Upstream Intake Runbook

## 目标

把参考仓更新转成可追踪、可裁剪、可验证的 adk 候选项。

## 来源仓与目标仓边界

- `llm_agent` 只把外部参考子仓作为 intake 来源。
- `agent-dev-kit` 是落地目标仓，不作为来源仓参与 `adopt/observe/reject` 评估。
- 目标仓变更走 `harden -> verify -> handoff` 闭环，不走来源仓 intake 流程。

## 流程

1. `sync-subrepos` 拉取参考仓更新。
2. `diff-scan` 生成变化报告。
3. `adoption-matrix` 做 `adopt/observe/reject` 决策。
4. adopt 项必须声明 `core/optional/profile/reject` 归属。
5. 进入实现前必须完成 `reuse-before-rebuild` 判定，使用 `templates/governance/reuse-before-rebuild-decision.md` 记录 `existing_asset_search`、候选资产和结论。
6. reuse 结论只能是 `use-as-is`、`adapt-existing`、`build-fresh` 或 `reference-only`；默认优先 `adapt-existing`，`build-fresh` 必须说明为什么现有 skill、script、workflow 或 runbook 无法复用。
7. 落地 Agent/Skill/Workflow 至少一层。
8. 回归通过后先进入显式 tool target 治理链路，再执行目标运行时 pilot。

## 30 天重吸收分级

- `re-intake-priority`：30 天内治理相关提交 `>=20`，进入下一波落地候选池。
- `light-recheck`：30 天内治理相关提交 `1~19`，做轻量复核与证据刷新。
- `no-action`：30 天内无治理相关提交，维持现状，等待下一周期。
- `keep-reject-optional-pilot`：当前为 reject 且需保留探索价值，只允许 optional 试点，不进 core。

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
- 新增 skill、script、workflow 或 runbook 前必须有 `reuse-before-rebuild` 记录；缺少 `existing_asset_search` 时结论固定为 `needs-fix`。
- 不能直接把第三方资产混装进运行目录；必须先经过 adk 审查，再进入显式 tool target。
- 临时参考素材不得成为完成声明的唯一证据。
