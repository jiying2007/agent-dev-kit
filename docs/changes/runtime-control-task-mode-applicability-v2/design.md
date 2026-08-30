# Design: Runtime Control Task Mode Applicability V2

## 根因

V1 只有全局 `gate_policy[gate_event]`。`evaluate()` 无任务类型输入，所以所有 final gate 都要求同一组 `repo`/`build` 工件。只读交付虽然没有实施工件，仍会得到 `required-artifact-missing`。

## 方案

### Policy V2

V2 用二维矩阵替代全局 gate 列表：

```json
{
  "schema_version": "runtime_control.policy/v2",
  "artifact_applicability": {
    "readonly": {
      "steady": [],
      "final": [],
      "commit": null,
      "apply": null,
      "release": null
    },
    "implementation": {
      "steady": [],
      "final": ["repo", "build"],
      "commit": ["repo", "build", "review"],
      "apply": ["repo", "build", "plan", "dry-run"],
      "release": null
    },
    "release": {
      "steady": [],
      "final": ["repo", "build"],
      "commit": ["repo", "build", "review"],
      "apply": ["repo", "build", "plan", "dry-run"],
      "release": ["repo", "build", "live", "review"]
    }
  }
}
```

Engine 同时执行 schema 形状验证和安全不变量验证。JSON Schema 约束字段、枚举和数据类型；Engine 约束 implementation/release 的最小工件集以及 readonly 的禁止工件。

### Gate 语义

1. `goal.started` 接收 typed intake，并重算 task/artifact/provenance 的 canonical attestation。
2. Engine 把 task mode 与 artifact mode 保存进 goal state；V2 evaluate 只读 state，拒绝调用参数覆盖。
3. 从 `artifact_applicability[artifact_mode][gate_event]` 取得 required artifacts。
3. 值为 `null` 时返回失败 decision，reason 为 `gate-not-applicable`；不抛异常，因为这是有效输入组合的政策裁决。
4. 列表为空只表示没有该类工件要求，不跳过 goal/evidence/checkpoint/retry/progress 检查。
5. final 仍只允许 completed goal；apply 仍只允许 active/completed 且满足全部适用工件。

### 兼容策略

- V1 是冻结的 legacy lane：仍接受原字段，仍返回 V1 decision，`task_mode` 省略时视为 legacy implementation。
- 调用 V1 policy 时显式传 `readonly`/`release` 会报错，避免把新语义悄悄套到旧配置。
- V2 是 opt-in lane：必须使用带 attested intake 的 goal state，返回 V2 decision。
- Legacy `goal.started` 仍可被 V1 policy reducer/evaluator 消费；无需迁移旧 journal。

### Replan

普通 `goal.updated` 只能改预算或 open item。模式变化必须在同一事件中携带 `intake` 与 `mode_change_reason=replan`；新 intake provenance kind 固定为 `goal-replan`，attestation 不得与当前值相同。事件之外修改 state 或在 final 调用传 mode 都会失败。

### Managed authority 与 CR5 trust boundary

普通 SHA-256 可由调用方重算，因此 intake digest 只用于绑定字段和防误改，不证明 authority 身份。V2 policy 新增 `mode_authority_policy`：

- `managed=true`；
- 无 authority 时必须是 `trusted_mode_authorities=[]`、`verification_backend=not-configured`；
- 声明受管 registry 时必须有非空 authority 列表与 `managed-authority-registry` backend。

Engine 只有在 authority 属于 registry，且调用方注入的外部 `mode_authority_verifier` 明确返回 true 时，才允许 readonly floor。Production 默认不注入 verifier；此时即使伪造 trusted authority ID、自算 intake SHA，`effective_artifact_mode` 仍为 implementation。

Pure engine 不验证签名、OIDC 或 routing decision 的真实来源。测试 verifier 只验证结构和 fail-closed 分支，不是生产信任证明；端到端 verifier wiring 仍 open。

## 被否决方案

- `allow_idle=true`：会绕过真实目标闭环，拒绝。
- `skip_artifacts=true`：不能表达为什么不适用，也可能被实现或发布任务滥用，拒绝。
- 根据 objective 文本推断 task mode：违反 Runtime Control 不存取原始目标内容的隐私边界，拒绝。
- final 调用传 `task_mode`：调用方可在交付时降级为 readonly，拒绝。
- 只检查 authority ID membership：ID 和 SHA 都可伪造，拒绝；必须有外部 verifier result，否则 implementation floor。
- 修改 V1 `gate_policy` 的 final 为空：会同时弱化实现和发布任务，拒绝。

## 回滚

回滚 Engine、V2 schemas 和本 change 目录即可；V1 policy/event/state 行为未迁移，旧调用方不需要数据回滚。
