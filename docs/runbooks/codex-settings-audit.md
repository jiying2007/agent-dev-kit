# Codex Settings Audit Runbook

## 适用场景

- 目标是 `~/.codex` 运行配置（如 `config.toml`、MCP 列表、执行策略）的一致性与可追溯校验。
- 需要把“配置声明”与“实际加载结果”做一一对齐。

## 推荐 Agent 链

`requirements-analyst -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `requirements-triage`
- `verification-before-completion`
- `commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<codex 配置审计目标>"
bash scripts/devkit.sh verify --change <change-id>
bash scripts/check-global-codex-health.sh ~/.codex minimal
codex mcp list
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 配置摘要必须与实际加载结果逐项对齐，禁止只给静态配置不做运行态验证。
- MCP 服务变更必须输出“声明列表 vs 实际列表”差异结论。
- 若审计目标是运行策略变更，必须附最小可复现命令与结果摘要。

## 审计模板

```md
- Config Summary:
- Runtime Loaded Result:
- MCP Declared List:
- MCP Loaded List:
- Diff Decision:
- Verify Commands:
- Final Gate Result:
```

## 验收门禁

- `verify-report` 必须包含至少一条运行态配置验证证据。
- MCP 清单不一致且无解释时，结论固定为 `needs-fix`。
- `~/.codex` 健康检查失败时，不得给 `pass`。
