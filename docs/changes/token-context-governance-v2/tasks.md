# 执行任务：token-context-governance-v2

- [x] T1 冻结目标、范围、风险、验收和恢复契约
- [x] T2 预算余量、task-cost receipt 与受支持 Python release 证据
- [x] T3 working-tree/release 双模式和 same-run evidence bundle 复用
- [x] T4 Codex plan v3、workflow activation 与成本投影
- [x] T5 Hub bounded capture、context receipt 与 review SLA packet
- [x] T6 跨仓 release bundle、定向/完整回归与性能证据
- [x] T7 source-to-live、review、Hub candidate 与完成门禁

## Checkpoints

| Stage | Status | Done Criteria | Evidence |
|---|---|---|---|
| S1 plan | complete | R1-R9、D1-D9、T1-T7 冻结 | proposal/requirements/design/tasks |
| S2 ADK/root | complete | T2-T3 定向测试通过 | negative-results/verification-evidence |
| S3 Codex | complete | T4 unit/governance/source plan 通过 | verification-evidence |
| S4 Hub | complete | T5 pytest/check 通过 | verification-evidence |
| S5 closeout | complete | T6-T7 全量与 source-to-live 通过 | verify/review/bundle/candidate |

## Anti-stall

- retry_budget：每个失败根因 2。
- staleness_threshold：45 分钟或相关仓 HEAD/fingerprint 改变。
- heartbeat：每完成一个 T 项更新 `session-state.md`。
- stop_condition：`pass | replan | split | blocked | abort`。
