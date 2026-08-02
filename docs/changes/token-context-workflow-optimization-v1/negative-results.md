# 负结果记录：token-context-workflow-optimization-v1

## 已验证的负结果
| 时间 | 假设/方案 | 验证方法 | 结果 | 不采用原因 |
|---|---|---|---|---|
| 2026-08-01 | 静态 token budget 通过即可代表日常轻量 | root/ADK budget + usage/smoke | 被证伪 | 文档/Skill 均贴近上限，真实 usage 入口还失败 |
| 2026-08-01 | Hub 查询延迟是主要瓶颈 | metrics summary | 被证伪 | warm context P95 约 350ms，主要成本是调用频率和输出 |
| 2026-08-01 | 现有 same-run reuse 已覆盖 smoke | smoke result JSON | 被证伪 | 复用只在 full workspace aggregate 生效，smoke count=0 |
| 2026-08-01 | 直接删除治理步骤 | 风险审查 | 拒绝 | 会削弱高风险证据、owner 与 source-to-live 边界 |
| 2026-08-01 | change 中枚举参考仓名不会影响 ADK 门禁 | `tests/run_all.sh --fail-fast` | 被证伪 | `test_no_external_repo_refs` 拒绝生产资产携带外部仓引用；已改为通用边界 |
| 2026-08-01 | 新增 task-cost template 无需同步资产计数断言 | full gate 第二次运行 | 被证伪 | context governance asset 从 10 增至 11；同步精确断言后重跑 |
| 2026-08-01 | Hub capture 的 `ai_role=implementation` 合法 | candidate dry-run | 被证伪 | 合法枚举不含 implementation；改用 `summarized` 后 dry-run/apply 通过 |

## Evidence Index（命令级）
| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---|---|---|---|---|
| `rtk scripts/check-all.sh --smoke --result-json /tmp/llm-agent-check-smoke.json` | 0 | 12/12，32s，reuse=0 | `/tmp/llm-agent-check-smoke.json` | Project | R6 baseline |
| `rtk bash ~/knowledge-hub/tools/knowledge-metrics.sh --summary-json` | 0 | 580 invocations；context=425；warm context P95=350.3ms | command output | Hub | R4 baseline |
| `rtk bash ~/codex/scripts/usage-report.sh --view summary --json` | 1 | SQLite 缺少 `thread_goals` | command output | Tool | R5 baseline |
| `rtk tests/run_all.sh --fail-fast` | 1 | 前 4 项通过，`test_no_external_repo_refs` 失败 | command output | ADK | 修复 change tasks 外部仓名后重跑 |
| `rtk tests/run_all.sh --fail-fast`（第二次） | 1 | 前 16 项通过，asset count 仍断言 10 | command output | ADK | 更新为 11 后重跑 |
| `knowledge-capture ... --ai-role implementation --dry-run` | 1 | invalid ai_role | command output | Hub | 改用 `summarized` |
