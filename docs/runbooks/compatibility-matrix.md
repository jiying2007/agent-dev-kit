# Compatibility Matrix Runbook

## 目标

明确 adk 在 Codex、Claude Code、Hermes Agent、OpenCode 之间的可迁移能力和降级边界。

## 工具目标

- Codex：生产主目标，先交接到 `~/codex` 的源资产与 manifest，再由 `~/codex` apply 到 `~/.codex/agents` 和 `~/.codex/skills`。
- Claude Code：转换目标，需保留 Agent/Skill 文本语义。
- Hermes Agent：转换目标，重点保留团队协作资产。
- OpenCode：转换目标，保留基础 Agent/Skill 目录结构。

## 兼容规则

- workflow 脚本是 adk 本仓能力，目标工具不一定原生执行。
- 子代理、插件、MCP、hook 能力必须显式标注是否支持。
- 不支持的能力必须在 runbook 中写明降级方式。

## 验收门禁

```bash
bash scripts/devkit.sh convert --target codex --profile core --codex-profile team-collab --out dist/codex --clean
bash scripts/devkit.sh codex-handoff --codex-root ~/codex
bash scripts/devkit.sh convert --target claude-code --profile core --out dist/claude-code --clean
```

转换失败或 silent downgrade 未说明时，不得声明多工具兼容。
