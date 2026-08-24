# 执行任务：realtime-token-usage-monitor-v1

- [x] T1 需求、设计、外部证据边界和停止条件冻结（R1-R8/D1-D8）
- [x] T2 实现 canonical event/state evaluator 与幂等恢复（R1-R5）
- [x] T3 接入 `devkit.sh token monitor`，支持 stdin/file、JSONL、gate（R2/R3/R6）
- [x] T4 增加 delta/snapshot/duplicate/recovery/security/1000-event 确定性测试（R4/R5/R8）
- [x] T5 文档、CLI 帮助、change evidence 与 before/after 同步（R7/R8）
- [ ] T6 strict/quick/full、根仓门禁、独立 review 与完成验证（R8）；机械门禁完成，等待 owner/independent review

## Ownership 与并行冲突检查
- 写入范围（scope_write）：本 change；`src/agent_dev_kit/token_monitor.py`、`cli.py`、
  `tests/test_token_monitor.sh`、`tests/run_all.sh`、README/CLI 对齐文档。
- 读取范围（scope_read）：token/context/performance/usage 现有实现、外部官方一手文档、本地参考仓。
- 是否与其他任务冲突（同文件/同 contract/同配置）：`agent-dev-kit` 当前内部 clean；CLI 和 test runner
  是共享文件，串行修改并在 apply 前复核 dirty/HEAD。

## 轻量工件与收敛结论
- 需求梳理工件：`requirements.md`、`proposal.md`、`design.md`。
- task checklist 工件：本文件、`state.yaml`、`session-state.md`。
- 执行反馈/验收记录工件：`negative-results.md`、`verification-evidence.md`、review report。
- 收敛结论或阻塞说明：终态门禁前固定 `needs-fix`。

## Checkpoints / Anti-stall

| Stage | Status | Done Criteria | Verification | Evidence |
|---|---|---|---|---|
| S1 plan | complete | R1-R8/D1-D8/T1-T6 冻结 | `devkit apply` | change 工件 |
| S2 core | complete | evaluator/CLI/test 完成 | targeted test 6/6 | source + test |
| S3 regression | complete | strict/quick/full 通过 | Python 3.11 parity + root gates | verification evidence |
| S4 closeout | in-progress | review blocker/major=0 | final gate | author self-review done；owner/independent pending |

- retry_budget：每个失败根因 2。
- staleness_threshold：相关 HEAD/dirty 改变或 45 分钟无 checkpoint。
- heartbeat：完成每个 T 项更新本文件与 `session-state.md`。
- stop_condition：`pass | replan | split | blocked | abort`。
