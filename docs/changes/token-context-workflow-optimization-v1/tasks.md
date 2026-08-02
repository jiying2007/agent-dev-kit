# 执行任务：token-context-workflow-optimization-v1

- [x] T1 需求、设计、任务、基线和回退边界冻结（R1-R8）
- [x] T2 Codex usage schema 兼容、累计预算、精简 profile 与路由测试（R2/R3/R5/R7）
- [x] T3 Hub 显式路由、opt-in telemetry 和 2 KiB summary（R4/R7）
- [x] T4 根仓/Codex build+target receipt、no-op 与 same-run 复用（R6/R7）
- [x] T5 分层 AGENTS、runbook、ADK task-cost contract 与文档同步（R1/R2/R8）
- [x] T6 分仓定向/quick/full、性能与 before/after 验证（R8）
- [x] T7 review、source-to-live、Hub reviewing candidate 与完成门禁

## Ownership 与并行冲突检查
- scope_write：本 change；根仓 AGENTS/docs/token/check 编排与测试；ADK context/profile
  契约与测试；`~/codex` AGENTS/manifests/tools/scripts/tests/docs；Knowledge Hub
  context/telemetry/summary 实现、测试与文档。
- scope_read：四仓局部规则、历史 reuse/change、manifest/schema、metrics 与测试 fixture。
- must_not_touch：所有参考子仓、远端、
  `~/.codex` 手工资产、memory、Hub active/owner decision。
- 冲突：根仓已有参考子仓 dirty，但与 scope_write 不重叠；其余三个目标仓当前 clean。

## 轻量工件与收敛结论
- 需求梳理：`requirements.md`、`proposal.md`、`design.md`。
- task/checkpoint：本文件、`state.yaml`、`session-state.md`、`negative-results.md`。
- 验收记录：`verification-evidence.md`、before/after JSON、分仓测试摘要。
- 收敛结论：待 T7；未通过终态门禁前固定为 `needs-fix`。

## Checkpoints

| Stage | Status | Done Criteria | Verification | Evidence |
|---|---|---|---|---|
| S1 plan | complete | R1-R8、D1-D7、T1-T7 冻结 | `devkit apply` | requirements/design/tasks |
| S2 codex | complete | usage/profile/router 通过 | Codex 119 unit + doctor | source + tests |
| S3 hub | complete | route/summary/telemetry 通过 | Hub context pytest 14/14 | source + tests |
| S4 gates/docs | complete | receipt/no-op/context budget 通过 | 11,500/12,000 bytes；ADK strict | source + tests |
| S5 closeout | complete | blocker/major=0，终态门禁通过 | full/source-to-live | evidence |

## Anti-stall

- retry_budget：每个失败根因 2。
- staleness_threshold：目标仓 HEAD/相关 dirty 改变，或 45 分钟无 checkpoint。
- heartbeat：每完成一个 T 项更新本文件与 `session-state.md`。
- stop_condition：`pass | replan | split | blocked | abort`。
