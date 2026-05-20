# Codex Settings Audit Runbook

## 适用场景

- 目标是 `~/.codex` 运行配置（如 `config.toml`、MCP 列表、执行策略）的一致性与可追溯校验。
- 需要把“配置声明”与“实际加载结果”做一一对齐。

## 推荐 Agent 链

`requirements-analyst -> test-validation-engineer -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-verification-before-completion`
- `adk-commit-pr-quality-gate`

## 命令模板

```bash
bash scripts/devkit.sh propose --change <change-id> --title "<codex 配置审计目标>"
bash scripts/devkit.sh verify --change <change-id>
bash ../scripts/check-global-codex-health.sh ~/.codex minimal
bash ../scripts/check-global-codex-health.sh ~/.codex security
codex mcp list
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 配置摘要必须与实际加载结果逐项对齐，禁止只给静态配置不做运行态验证。
- MCP 服务变更必须输出“声明列表 vs 实际列表”差异结论。
- 若审计目标是运行策略变更，必须附最小可复现命令与结果摘要。
- provider relay、base URL、sandbox、approval policy、hooks 和 MCP server 属于运行态安全基线，必须逐项列出。
- 非标准 base URL 必须给出审查来源、用途、凭证边界和回退方式；否则结论为 `needs-fix`。
- hooks 只能作为校验和拦截层，不得绕过 `~/codex` 写入 `~/.codex`。
- MCP/plugin 变更必须附暴露清单、auth scope、schema/smoke、deny-path guard 和 rollback。
- plugin 晋级必须说明为何普通 skill 不足，以及 plugin manifest、profile 绑定和禁用路径。

## 审计模板

```md
- Config Summary:
- Provider/Base URL Allowlist:
- Sandbox + Approval Policy:
- Hook Policy:
- Runtime Loaded Result:
- MCP Declared List:
- MCP Loaded List:
- MCP/Plugin Readiness:
- Exposure Inventory:
- Auth Scope:
- Schema/Smoke Evidence:
- Tool-call Policy:
- Guard Tests:
- Rollback Path:
- Diff Decision:
- Verify Commands:
- Final Gate Result:
```

## 验收门禁

- `verify-report` 必须包含至少一条运行态配置验证证据。
- MCP 清单不一致且无解释时，结论固定为 `needs-fix`。
- `~/.codex` 健康检查失败时，不得给 `pass`。
- `security` profile 发现未审查 base URL、未声明 MCP 写权限或未解释 hooks 时，不得给 `pass`。
- MCP/plugin 缺少暴露清单、schema/smoke、deny-path guard 或禁用回滚时，不得给 `pass`。
