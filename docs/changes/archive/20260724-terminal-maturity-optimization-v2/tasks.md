# 执行任务：terminal-maturity-optimization-v2

- [x] T1 需求确认、dirty 边界与验收冻结
- [x] T2 根测试 runner、聚合入口和 architecture fixture
- [x] T3 `check-all` 有界诊断与机器证据
- [x] T4 ADK Python 入口与受支持环境合同
- [x] T5 maturity `effective_level` 与状态语义
- [x] T6 参考仓 baseline、strict ADK 与 source-to-live 决策收敛
- [x] T7 定向/full/双 Python/复审与收口证据
- [x] 代码评审与分级闭环（blocker/major/minor）
- [x] 文档同步与收尾

## Ownership 与并行冲突检查
- scope_write：根 `scripts/check-all.sh`、root test runner/fixtures、成熟度
  scorecard/tests/docs；ADK launcher/tests/docs 与本 change。
- scope_read：两仓 AGENTS/README/manifest、dirty subrepo 状态、M5 policy/ledger、
  source-to-live 证据。
- must_not_touch：用户既有外部 intake 内容、参考仓 dirty 文件本体、远端、
  `~/codex`、`~/.codex`、凭证和现场 ledger 历史事件。
- 冲突：root scorecard/current-status 与现有 Software M5 dirty 变更共享，
  必须基于当前内容最小 patch；ADK `tests/run_all.sh` 已有用户变更，禁止覆盖。

## 轻量工件与收敛结论
- 需求梳理：`proposal.md`、`design.md`、根 context-preflight report。
- task/checkpoint：本文件、`state.yaml`、`negative-results.md`。
- 验收记录：`verify-report.md`、`review-report.md`。
- 当前结论：T1–T6 完成；三个参考仓 dirty 分类已复核并续期，ADK dirty
  仍只允许通过真实提交收敛；source-to-live 必须在提交后由 owner 授权执行，
  外部 runtime/field/final 保持 blocked。

## Checkpoints
| Stage | Status | Done Criteria | Verification | Evidence |
|---|---|---|---|---|
| S1 plan | complete | scope/risks/stop fixed | change governance | proposal/design/tasks |
| S2 root gates | complete | all root tests discoverable, diagnostics bounded | root targeted tests | root runner/check-all contract |
| S3 ADK/status | complete | Python/effective-level contracts pass | ADK/root contracts | ADK 57/57 + product maturity contract |
| S4 state closure | complete | dirty classification and delivery decision explicit | subrepo/evidence gates | 2026-07-23 dirty triage + explicit post-commit handoff |
| S5 final | complete-with-delivery-blocker | blocker/major=0 locally | two-repo full + final-ready | verify/review reports |

## Anti-stall
- retry_budget：每个失败根因 2。
- staleness_threshold：45 分钟或一个 T 项。
- heartbeat：每完成一个 T 项更新本文件或 Evidence Index。
- stop_condition：pass / replan / split / blocked / abort。
