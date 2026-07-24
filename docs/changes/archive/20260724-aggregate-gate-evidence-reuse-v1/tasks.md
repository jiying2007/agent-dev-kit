# 执行任务：aggregate-gate-evidence-reuse-v1

- [x] T1 需求、非目标、安全边界与基线冻结
- [x] T2 实现 workspace fingerprint 与 evidence schema/validator
- [x] T3 接入 check-all producer、workspace allowlist consumer 与可观测结果
- [x] T4 补齐伪造、失败、漂移、回退和聚合集成测试
- [x] T5 定向/root/ADK/full 验证并量化性能
- [x] T6 独立复审、Evidence Index、Hub/收口结论
- [x] 代码评审与分级闭环（blocker/major/minor）
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- scope_write：根 `scripts/check-all.sh`、`scripts/check-workspace-entrypoints.sh`、
  `scripts/lib/same-run-evidence.sh`、root contract tests；本 change 工件。
- scope_read：根/ADK AGENTS、历史 full/root timing、相关 leaf checks 和
  terminal maturity review。
- must_not_touch：harden/performance 实现、leaf gate 语义、用户 intake 和
  runtime evidence、参考子仓内容、远端、`~/codex`、`~/.codex`。
- 冲突：`check-all.sh` 与 root tests 是前一 change 的 dirty 文件；基于当前
  内容做最小增量 patch，不覆盖其诊断/result JSON 改动。

## 轻量工件与收敛结论
- 需求梳理：`requirements.md`、`proposal.md`、`design.md`。
- task/checkpoint：本文件、`state.yaml`、`negative-results.md`。
- 验收记录：`root-regression-timing.json`、`full-result.json`、
  `review-findings.md`；CLI 将生成 `verify-report.md`、`review-report.md`。
- 收敛结论：最终 full 55/59、854 秒，实际复用 6 项，workspace 151 秒；
  相对 906/207 秒基线分别减少 52/56 秒。四项失败与基线完全一致，均由
  strict ADK dirty 派生，没有被复用掩盖。
- Hub 结论：本次不另写 Knowledge Hub candidate。安全合同、负结果、性能
  数据与回退已经以 project-bound change artifact 作为 SSOT；源码尚未提交，
  重复写 provisional Hub 结论会制造双 SSOT。

## Checkpoints
| Stage | Status | Done Criteria | Verification | Evidence |
|---|---|---|---|---|
| S1 plan | complete | R1-R5、deny-path、baseline 固化 | change apply | requirements/design |
| S2 implementation | complete | producer/consumer fail-closed | contract tests | source + fixtures |
| S3 integration | complete | standalone 等价、full 实际复用 | root/full | result JSON |
| S4 closeout | complete | blocker/major=0 | verify/review/final-ready | reports |

## Anti-stall
- retry_budget：每个失败根因 2。
- staleness_threshold：45 分钟或一个 T 项。
- heartbeat：每完成一个 T 项更新本文件或 Evidence Index。
- stop_condition：pass / replan / split / blocked / abort。
