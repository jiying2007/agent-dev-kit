# Session State

- goal_statement：破坏式统一 Goal、Token、长任务与完成门禁，只保留一套 Runtime Control。
- current_stage：S5 source-to-live 与 whole-diff review complete；等待 owner 提交后刷新 release-clean 元数据。
- completion_claim：needs-fix。
- required_evidence：ADK/Codex/root full、zero-residual、wheel/bundle、source-to-live、review。
- claimant：primary Codex agent。
- verifier：completion gate + owner/independent review。
- open_items：T8 的 release-clean lock/current-status/M5/phase-gate 刷新。
- retry_budget：每根因 2。
- staleness_threshold：45 分钟或 dirty overlap 变化。
- heartbeat：2026-08-24 ADK full 62/62、Codex full 154/154 + 五 profile smoke、live zero-residual、author self-review B0/M0。
- stop_condition：pass | replan | split | blocked | abort。
- next_actions：owner 审查并提交 ADK/Codex/root；刷新 adk.lock/current-status/M5/phase-gate；运行 release-clean 与 final gate。
- excluded：commit/push、覆盖不相关 dirty、保存 raw prompt/session、兼容 alias/fallback。
