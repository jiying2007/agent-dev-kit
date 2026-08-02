# Session State

- goal_statement：全面落地 ADK/Codex/Hub 第二阶段 Token、治理与验证效率优化。
- completion_claim：R1-R9 已实现并完成分仓与跨仓验证；不声明 release-clean。
- claimant：Codex implementation role。
- verifier：`adk-verification-before-completion` 与分仓门禁。
- current_stage：complete。
- last_checkpoint：T6-T7 full regression、source-to-live、Hub candidate 与 bundle complete。
- open_items：无；仅保留人工 review 与未来 release-clean gate。
- retry_budget：每根因 2。
- staleness_threshold：45 分钟或相关仓 HEAD/fingerprint 改变。
- heartbeat：2026-08-01 T7。
- stop_condition：pass / replan / split / blocked / abort。

## Recovery Prompt

实现与验证已完成。若继续，先核对四仓 fingerprint 与 bundle；发布前必须另跑 release-clean gate。
不得清理四仓既有 dirty，不自动 commit/push，不自动提升 Hub active。每阶段先跑定向测试，
失败两次回到设计；完成前必须跑 source-to-live、full gate 与 final-ready。
