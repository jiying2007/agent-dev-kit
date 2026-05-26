# agent-dev-kit

`agent-dev-kit`（adk）是通用 Agent/Skill/Profile/Workflow 资产包。它的目标是把参考资料和工程经验压实为可验证、可回滚、可迭代的 ADK 资产，而不是绑定到某个具体运行时。

## Scope

adk 负责：

1. 维护通用 Agent、Skill、Profile、Workflow 和 Manifest。
2. 提供需求、实现、验证、评审、发布和复盘门禁。
3. 管理官方参考来源的 freshness、review status 和 promotion gate。
4. 通过显式 tool target 适配不同运行时。
5. 阻止平台专属 handoff 混入 ADK core。

adk 不负责：

1. 替代具体运行时的全局策略文件。
2. 默认安装到任何平台的用户运行目录。
3. 在 core 中保留平台专属兼容链路。
4. 绕过验证、review、rollback 直接发布资产。

## Tool Targets

当前通用目标声明在 `manifest.yaml:tool_targets`：

- `claude-code`
- `hermes-agent`
- `opencode`

新增目标必须保持显式隔离，并通过 `runtime-boundary` 验证。

## Quick Start

```bash
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh install --tool claude-code --profile core --target /tmp/adk-target --mode copy
bash scripts/devkit.sh convert --target claude-code --profile core --out dist --clean
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh openai-governance --summary-json
```

## Profiles

| Profile | Purpose |
|---|---|
| `core` | 基础 Agent/Skill 组合 |
| `personal-core` | 个人通用 ADK 核心配置 |
| `embedded-fullstack` | 嵌入式全栈开发配置 |
| `team-core` | 团队协作、交接和评审配置 |
| `release-hardening` | 发布前质量、验证和安全强化 |

## Quality Gates

- `scripts/validate-assets.sh --strict`
- `scripts/check-runtime-boundary.sh`
- `scripts/check-openai-developers-governance.sh`
- `tests/run_all.sh`

没有验证证据，不声明可发布、可合并或生产可用。

## OpenAI Official References

OpenAI Developers 内容只作为官方参考来源。保留在 `source_docs`、URL 或 title 中的产品名属于 citation metadata；被提升为 ADK 规则、manifest 或 runbook 时必须转为平台中立 contract。
