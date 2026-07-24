# 负结果记录：field-evidence-v2

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-07-23 | 旧 field event 集已满足 v2 | 首次运行 `test_software_m5_certification.sh` | RED：required event types 不完整 | v2 必须有 selection 与 human baseline 事件 |
| 2026-07-23 | repository campaign 只需 policy 即会出现在状态 | 集成测试访问新状态字段 | RED：缺少 `repository_runtime_campaign` | certifier 尚未调用 ADK repository certification |
| 2026-07-23 | 有事件即可，不必验证 selection 语义 | 删除 selection、令 accepted+rejected 与 preregistered 矛盾并重封 hash chain | 完整性通过但认证被 `required_field_events` 阻断 | hash 完整不等于业务语义完整 |
| 2026-07-23 | clean-room campaign 可替代真实仓证据 | 当前 live status | `repository_runtime_campaign` 保持 blocker | M5 至少需要两条 owner-approved real-repository task |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk tests/test_software_m5_certification.sh` | 0 | v2 正例、缺事件、计数矛盾、hash 篡改和真实 campaign blocker 通过 | `tests/test_software_m5_certification.sh` | L2 | `field-evidence-v2` |
| `rtk bash agent-dev-kit/tests/run_all.sh --quick` | 0 | quick 19/19 | `docs/changes/field-evidence-v2/verify-report.md` | Workflow | `field-evidence-v2` |
| `rtk bash agent-dev-kit/tests/run_all.sh --timing-json /tmp/repository-absorption-adk-timing.json` | 0 | full 56/56 | `/tmp/repository-absorption-adk-timing.json` | Release | `field-evidence-v2` |
