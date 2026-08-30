# Negative Results: Runtime Control Task Mode Applicability V2

## 2026-08-30 基线复现

- 环境：Python 3.8.10 development evidence；当前 `runtime_control.policy/v1`。
- 输入：已完成 goal，open item 为 0，required evidence 和当前 checkpoint 齐全，不提供 `repo`/`build` 工件，按 final gate 评估。
- 结果：`gate_allowed=false`、`completion_allowed=false`、`missing_artifacts=[build, repo]`、reason=`required-artifact-missing`。
- 结论：误报来自全局 gate policy 缺少任务模式维度，不是 evidence 或 checkpoint 状态问题。

## 假设矩阵

| 假设 | 验证 | 结果 |
|---|---|---|
| H1 全部任务共享 `gate_policy.final` 导致只读误报 | 读取 `evaluate()` 并用闭环状态复现 | 确认 |
| H2 放宽 final 为 idle/active 可解决 | 对照现有 final 完成条件 | 否决；会绕过目标闭环 |
| H3 将 V1 final 工件列表置空可解决 | 分析 implementation/release 影响 | 否决；会全局弱化门禁 |
| H4 由 objective 文本推断任务模式 | 对照敏感字段与隐私合同 | 否决；Engine 不得读取原始内容 |
| H5 final 调用自由传 `task_mode=readonly` | CR4 反例：同一 completed implementation state 在 evaluate 时降级 | 确认；调用方可绕过 implementation artifact floor |
| H6 trusted authority ID + arbitrary request/routing digest + self-hash | CR5 反例：公开 ID membership 与普通 SHA 可由调用方构造 | 确认；无外部 verifier 时必须提升 implementation floor |

## Repair Note

- failed_scope：V1 final gate 对只读已完成目标误要求 implementation artifacts。
- passing_scope_to_preserve：V1 replay、usage、progress、retry、evidence、checkpoint、apply/final 行为。
- minimal_rerun：`tests/test_runtime_control.sh`。
- rollback_anchor：本变更前 `runtime_control.policy/v1` 与 `runtime_control.decision/v1`。
- root_cause_status：known。
- repair_action：新增 opt-in V2 applicability matrix，并将 task/artifact mode 绑定 goal intake canonical attestation/provenance；冻结 V1 legacy lane。
- semantic_verification：readonly pass，implementation/release missing fail，idle/active final fail，final override fail，只有 attested replan 可改变模式。
- trust_verification：normal evaluate 无 verifier 时，伪造 trusted ID/self-hash 的 readonly goal 得到 `effective_artifact_mode=implementation`、missing repo/build、gate denied；test-only verifier 不匹配绑定 digest 时同样拒绝。
- open_item：pure engine 不认证外部签名或 routing decision provenance；production composition root verifier 尚未接入。
- do_not_repeat：不通过 allow-idle 或全局清空 final artifacts 规避错误。
