# Config Baseline Governance Runbook

## 适用场景

- 变更以配置文件为主（环境、工具链、任务编排、主机参数等）。
- 需要防止“配置漂移”与“隐式行为变化”，并保留可审计证据。

## 推荐 Agent 链

`requirements-analyst -> application-engineer -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `gdk-requirements-triage`
- `gdk-task-breakdown`
- `gdk-verification-before-completion`
- `gdk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<配置治理目标>"
bash scripts/devkit.sh apply --change <change-id>
bash scripts/devkit.sh verify --change <change-id>
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 先给配置摘要，再改配置：变更前后必须分别输出配置摘要快照。
- 配置修改必须绑定最小验证命令；不能执行时必须给出原因和替代证据。
- 配置改动不得夹带无关逻辑重构。
- 必须显式声明“是否存在行为变化”与“回退方式”。
- 必须给出“声明配置 vs 运行态加载”对比结论，并记录命令级 Evidence Index。

## 配置摘要模板

```md
- Config Files:
- Key Changes:
- Runtime Loaded Config:
- Behavior Impact:
- Diff Decision:
- Verify Commands:
- Evidence Index (command/exit_code/result_summary/evidence_path/layer):
- Rollback Plan:
```

## 验收门禁

- `proposal.md` 必须声明 `Config Scope` 和 `Behavior Impact Decision`。
- `verify-report` 必须包含配置验证命令输出与命令级 Evidence Index（命令/退出码/结果摘要/证据路径/层级）。
- 若缺少配置摘要或验证命令不可复现，结论固定为 `needs-fix`。
