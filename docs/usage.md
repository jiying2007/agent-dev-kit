# Usage

`agent-dev-kit` is a generic ADK asset package for agents, skills, profiles, workflows and governance checks. It is not bound to a single runtime.

## Common Commands

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

## Boundaries

- ADK core keeps platform-neutral contracts.
- Tool-specific adapters must be explicit, isolated and declared in `manifest.yaml`.
- Production promotion requires validation evidence, runtime-boundary checks and a rollback plan.
