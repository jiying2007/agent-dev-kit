# Codify Decision：receipt-driven measured emitter

- delivery_goal：从显式、受验证的 Agent/Skill/Profile invocation receipt 生成可审计价值指标，同时保持无输入时 not-measured。
- reusable_pattern：`validated input -> evidence-layer partition -> metric applicability -> measured/not-measured result`。
- affected_asset：`agent_value.py`、invocation receipt/measurement schema、agent value contract 与定向测试。
- promotion_candidate：false。
- next_task_friction_reduced：后续 runtime adapter 只需生成统一 receipt，不再各自实现 KPI 聚合、缺失值或隐私引用语义。
- reduced_by：统一 opaque refs、去重、evidence-layer 隔离和 no-zero metric result schema。
- reduction_evidence：`tests/test_agent_value.py` 的 Agent/Skill/Profile、空输入、缺字段、重复 observation、隐私与状态负例。
- do_not_promote_reason：尚无独立 owner review，也没有 runtime/field receipt；当前证据只证明 source/test 层确定性行为。
- owner_review：pending-parent-integration-review。
- rollback_path：移除 `emit_measurements` 与 measurement schema，恢复 receipt schema 的单条验证边界；不涉及 manifest、runtime 或外部数据迁移。
- verification_evidence：`rtk bash tests/test_agent_value.sh` 18/18；`rtk tests/test_format.sh` pass；空输入 CLI smoke pass。
