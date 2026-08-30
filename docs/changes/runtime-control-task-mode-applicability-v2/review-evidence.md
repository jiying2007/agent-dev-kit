# Review Evidence: Runtime Control Task Mode Applicability V2

## 首轮自审

- API：`evaluate(..., task_mode=None)` 对 V1 保持兼容；V2 mode 来自 attested goal state，任何调用参数覆盖 fail closed。
- Schema：V2 policy 和 decision 使用独立 schema version；event/state 保持 V1，无 journal migration。
- 安全：无 idle/skip/allow boolean；readonly 仅 steady/final，且不能要求或伪造 implementation artifacts 来改变适用性。
- Trust：authority registry membership 本身不放行；production 默认无 verifier，unverified readonly 使用 implementation floor。外部签名验证仍 open。
- 门禁：implementation/release 最小工件集在 Engine 和 JSON Schema 双重固定，配置不能删减。
- 隐私：policy/event 均递归拒绝敏感字段；decision 不返回原始内容。
- 兼容：现有 Codex adapter 继续消费 V1 decision；workspace entrypoint 对 V1 schema 的断言不受影响。

## 交叉审查重点

1. 已闭环：`task_mode`、`artifact_mode`、attestation digest 与 provenance 绑定 `goal.started`；仅 attested replan 可变更。
2. readonly final 是否允许可选 `review` 工件；当前 schema/Engine 允许，但不要求。
3. implementation task 不允许 `release` gate、release task 允许全 gate 的边界是否符合上层 lifecycle。
4. 在 Python 3.11/3.12 环境补跑 ruff、strict 和 64/64 full suite。
5. 在受管 composition root 接入 routing decision/signature verifier；测试 verifier 不可作为 runtime evidence。
