# 执行任务：runtime-control-v1

- [x] T1 三仓 dirty/callsite/contract/删除清单冻结
- [x] T2 ADK Runtime Control Engine + unit tests
- [x] T3 删除 ADK 旧 module/CLI/tests/docs，归档 superseded changes
- [x] T4 Codex adapter/journal/manifest/唯一 CLI + tests
- [x] T5 删除 Codex usage/session/goal/final-ready 旧 active 资产与全部调用点
- [x] T6 llm_agent 单一跨仓 gate、wheel/bundle 和 zero-residual
- [x] T7 三仓 targeted/full 与 whole-diff review
- [ ] T8 build/doctor/plan/dry-run/apply/check/runtime health/收口

## Ownership 与并行冲突检查
- scope_write：ADK runtime_control/CLI/tests/docs；Codex tools/scripts/manifests/tests/docs/AGENTS；root gate/reports。
- scope_read：三仓现有 monitoring/goal/build/apply/contracts；`~/.codex` 只读直到 apply 阶段。
- must_not_touch：Codex 9 个 dirty agent/base config 内容，除必要 active reference 的最小局部合并。
- conflict：shared CLI/manifest 串行；不并行编辑。

## 轻量工件与收敛结论
- requirements/design/tasks/session-state/risk-ledger/negative-results/verification/review。
- 完成前固定 needs-fix；owner 已批准 breaking cutover，但 Git commit/push 不在自动权限内。

## Checkpoints
| Stage | Status | Done | Verification | Evidence |
|---|---|---|---|---|
| S1 contract | complete | R1-R10/D1-D9 冻结 | callsite scan | requirements/design |
| S2 ADK | complete | 唯一 Engine，旧 ADK active=0 | ADK full 62/62 | source/tests |
| S3 Codex | complete | 唯一 adapter/CLI，旧 Codex active=0 | Codex 47 tests | source/tests |
| S4 integration | complete | wheel/root gate/active zero residual | cross-repo targeted | verification-evidence.md |
| S5 live | partial | source-to-live 与 health 已完成；release-clean 元数据等待真实提交 | build/plan/apply/check | receipts/review-evidence.md |

## Anti-stall
- retry_budget：同根因 2。
- staleness_threshold：45 分钟或目标仓 HEAD/dirty overlap 变化。
- heartbeat：每完成一个 S 阶段更新 session-state。
- stop_condition：pass | replan | split | blocked | abort。
