# Session State

- goal_statement：在持续工程目标中新增平台中立的实时 Token 消耗监测，并保留更广泛优化候选。
- current_stage：S4 closeout；核心实现、CLI、文档、8 组定向测试和 Python 3.11 full parity 已完成。
- completion_claim：needs-fix；机械门禁通过，独立/owner semantic review 尚未完成。
- required_evidence：targeted test、strict/quick/full、根仓 gate、独立 review、completion guard。
- claimant：primary Codex agent。
- verifier：后续独立 review/verification 步骤。
- open_items：T6；其余广泛优化候选仍待后续 goal 阶段评估。
- retry_budget：同根因 2 次。
- staleness_threshold：45 分钟或相关 HEAD/dirty 变化。
- heartbeat：2026-08-24，change apply、typed core、CLI、文档和 targeted test 已完成。
- stop_condition：pass | replan | split | blocked | abort。
- next_actions：运行 change verify；保持 owner/independent review open；转入 freshness timezone 独立 change。
- excluded：参考仓修改、runtime 私有数据库、网络写、自动进程终止、live apply。
- raw_evidence：当前 change；`token-context-workflow-optimization-v1`；官方 URL 见 design。
