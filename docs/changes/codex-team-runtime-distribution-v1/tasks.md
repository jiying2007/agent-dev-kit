# Tasks

- [x] T1 新增 Runtime Bundle 构建 API 与 CLI。
- [x] T2 提升 `adk-cross-team-handoff` 并闭合 `team-core`。
- [x] T3 增加确定性、安全和 source-exclusion 测试。
- [x] T4 在 `team-codex-assets` 实现 bundle 导入与 source-to-live 控制面。
- [x] T5 生成真实 `team-core` Bundle 并完成团队仓导入、build、plan/apply/rollback smoke。
- [x] T6 运行 ADK strict/full、团队仓测试和最终治理门禁；既有阻断已记录。
- [ ] T7 完成 ADK source push、个人 `~/codex` source-to-live apply 与远端/运行态核验。

## Goal closure

- goal_statement：团队仅从 Release 获取 ADK Skill，并通过团队 Codex 仓安全安装。
- completion_claim：本地实现、内部团队仓发布、fresh clone 隔离验证与 ADK 59/59 回归完成；ADK source push 和个人 source-to-live apply 进入交付阶段。
- required_evidence：ADK tests、bundle inventory/digest、团队仓 tests、端到端 receipt/rollback。
- claimant：Codex implementation agent。
- verifier：完成前验证门禁与用户/owner 复核。
- open_items：T7、真实团队成员新 session pilot。
- retry_budget：2。
- staleness_threshold：30 minutes。
- heartbeat：每阶段完成时更新。
- stop_condition：pass / replan / split / blocked / abort。
