# 负结果记录：repository-runtime-evidence-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | CLI 已支持 `eval repository` | 首次运行 `tests/test_repository_runtime_evidence.sh` | RED：缺少 `repository` 子命令 | 公共入口尚未实现，按 Level 2 TDD 进入最小实现 |
| 2026-07-23 | 任意 security result 变坏都能覆盖目标负例 | 修改 baseline result | RED 测试意外未失败 | 测试构造未命中 ADK certification 条件，改为修改 ADK result |
| 2026-07-23 | 最终 outcome pass 即可认证 | 六类负报告：隔离缺失、invalid process、usage/cost 缺失、digest drift、matrix 不完整、安全失败 | 均被 certifier 拒绝 | lucky pass、不可比 baseline 和不完整 provenance 不得计为认证 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash agent-dev-kit/tests/test_repository_runtime_evidence.sh` | 0 | contract、完整矩阵与六类 fail-closed 负例通过 | `tests/test_repository_runtime_evidence.sh` | L2 | `repository-runtime-evidence-v1` |
| `rtk bash agent-dev-kit/tests/run_all.sh --quick` | 0 | quick 19/19 | `docs/changes/repository-runtime-evidence-v1/verify-report.md` | Workflow | `repository-runtime-evidence-v1` |
| `rtk bash agent-dev-kit/tests/run_all.sh --timing-json /tmp/repository-absorption-adk-timing.json` | 0 | full 56/56 | `/tmp/repository-absorption-adk-timing.json` | Release | `repository-runtime-evidence-v1` |
