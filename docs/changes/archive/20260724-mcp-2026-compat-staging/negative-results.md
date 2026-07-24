# 负结果记录：mcp-2026-compat-staging

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | 现有 ecosystem checker 已能阻止 RC runtime | 新增 `mcp-rc-runtime-enabled.json` 后运行 checker | RED：新 fixture 未产生失败 | 现有 contract 不认识 candidate protocol 与 activation gates |
| 2026-07-23 | 只增加 candidate 字段即可保持正例 | 运行 ecosystem test | RED：正例缺少 compatibility 与 target-watch 字段 | 正例必须显式证明 active/candidate 分离和 runtime disabled |
| 2026-07-23 | RC 可提前声明 final compatibility | runtime-enabled 负 fixture | 被 fail closed | 最终规范与真实 client/server smoke 尚未发生 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash agent-dev-kit/tests/test_agent_ecosystem_standards.sh` | 0 | RC runtime-enabled 负例与 compatibility staging 正例通过 | `tests/test_agent_ecosystem_standards.sh` | L2 | `mcp-2026-compat-staging` |
| `rtk bash agent-dev-kit/tests/run_all.sh --quick` | 0 | quick 19/19 | `docs/changes/mcp-2026-compat-staging/verify-report.md` | Workflow | `mcp-2026-compat-staging` |
| `rtk bash agent-dev-kit/tests/run_all.sh --timing-json /tmp/repository-absorption-adk-timing.json` | 0 | full 56/56 | `/tmp/repository-absorption-adk-timing.json` | Release | `mcp-2026-compat-staging` |
