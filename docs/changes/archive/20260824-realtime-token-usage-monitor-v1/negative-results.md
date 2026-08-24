# 负结果记录：realtime-token-usage-monitor-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-08-24 | 现有 CLI 已能动态监测 Token | 在实现前运行 `tests/test_token_monitor.sh` | 6/6 失败，统一报 `unknown command: token` | 证实静态预算与事后 usage 不能替代实时入口 |
| 2026-08-24 | 同一 scope 可混用 delta/snapshot | 自审并增加负例 | 会将已有 delta 与首个 snapshot 双计 | 改为同一 scope 固定一种事件语义并 fail closed |
| 2026-08-24 | `devkit verify` 的 exit 0 可证明所有子门禁通过 | 回读 `verify-report.md` | 报告含 27 条 `[FAIL]` 但 state=verified | 发现 Bash 条件上下文吞错；手工失效旧状态并修复 workflow 后重验 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk bash agent-dev-kit/tests/test_token_monitor.sh`（before） | 1 | 6/6 因 token 命令不存在而失败 | 本文件 | Workflow/Test | TDD negative |
| `rtk agent-dev-kit/tests/test_token_monitor.sh`（after） | 0 | 6/6；覆盖阈值、速率/ETA、幂等、恢复、安全、1000 events | `tests/test_token_monitor.py` | Workflow/Test | T2-T4 |
| `rtk agent-dev-kit/scripts/check-format.sh` | 0 | format 通过；首次提示新 shell test 缺 executable bit，修复后待复跑 | 本文件 | Workflow/Test | T4 |
| `rtk agent-dev-kit/tests/test_docs_cli_alignment.sh` | 0 | `docs/commands.md` 覆盖新增 token 命令 | `docs/commands.md` | Workflow/Docs | T5 |
| `rtk agent-dev-kit/tests/test_scripts_smoke.sh` | 0 | 25/25，新增 token monitor help smoke | `tests/test_scripts_smoke.sh` | Workflow/Test | T5 |
