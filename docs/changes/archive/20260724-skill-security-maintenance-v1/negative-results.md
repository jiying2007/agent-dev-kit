# 负结果记录：skill-security-maintenance-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | 现有 Skill contract 已覆盖 AST10、维护和新 target watch | 增加三类负 fixture 后运行 checker | RED：新 fixture 均未产生失败 | 现有检查缺少 AST01-AST10、digest/effect 与 direct-target activation 约束 |
| 2026-07-23 | 任意来源字段可视为本地维护证据 | 缺 digest 负 fixture | 被 fail closed | 未知必须 `not-measured`，不能伪造 provenance/use count |
| 2026-07-23 | 文档发现路径足以新增 VS Code target | `coding-agent-target-enabled.json` | 被 fail closed | 缺真实 use case、固定版本、smoke、effect/security 和 rollback |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash agent-dev-kit/tests/test_agent_ecosystem_standards.sh` | 0 | AST 缺失、maintenance digest 缺失、target enabled 负例通过 | `tests/test_agent_ecosystem_standards.sh` | L2 | `skill-security-maintenance-v1` |
| `rtk bash agent-dev-kit/tests/run_all.sh --quick` | 0 | quick 19/19 | `docs/changes/skill-security-maintenance-v1/verify-report.md` | Workflow | `skill-security-maintenance-v1` |
| `rtk bash agent-dev-kit/tests/run_all.sh --timing-json /tmp/repository-absorption-adk-timing.json` | 0 | full 56/56 | `/tmp/repository-absorption-adk-timing.json` | Release | `skill-security-maintenance-v1` |
