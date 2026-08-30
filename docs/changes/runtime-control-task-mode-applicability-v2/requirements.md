# Requirements: Runtime Control Task Mode Applicability V2

## 目标

让 Runtime Control final gate 按显式 `task_mode` 判断交付工件是否适用：只读评估或解释任务在目标、证据、checkpoint 与 open item 已闭环时，不因缺少 `repo`/`build` 实施工件失败；实现和发布任务继续 fail closed。

## 范围

- Runtime Control policy/decision schema、Engine 与专属单元测试。
- V1 policy/decision 的兼容读取边界与 V2 迁移说明。
- 不修改 Agent/Skill/Profile/Workflow 总 manifest，不修改 runtime adapter 或外部 live 配置。

## 验收要求

### R1 显式任务模式

- V2 policy 仅接受 `readonly`、`implementation`、`release`。
- V2 `evaluate` 必须从 `goal.started.intake` 读取 `task_mode` 与 `artifact_mode`；调用参数不得覆盖状态绑定模式。
- Goal intake 必须包含 canonical attestation SHA-256 与 routing provenance；task/artifact mapping 不一致或摘要不匹配 fail closed。
- 模式变化只能由 active goal 的 `goal.updated` 进入，且必须同时携带 `mode_change_reason=replan`、新 attestation 与 `goal-replan` provenance。
- Intake attestation 必须绑定 `goal_id`、`request_sha256`、`routing_decision_sha256` 与 `authority_id`。
- Policy V2 必须声明 managed mode authority policy。没有 configured trusted registry，或没有外部 verifier 返回受管验证结果时，readonly artifact mode 的 effective floor 固定提升为 implementation。
- 不提供 `allow_idle`、`skip_gate` 或任意布尔绕过参数。

### R2 显式工件适用性

- V2 policy 用完整的 `artifact_applicability` 矩阵表达每个任务模式对每个 gate 的工件要求。
- 列表表示 gate 适用及其 required artifacts；`null` 表示 gate 对该任务模式不适用。
- `readonly.final` 不得要求 `repo` 或 `build`，且 `commit`、`apply`、`release` 不适用。

### R3 目标闭环不弱化

- `readonly.final` 仍要求 goal 已完成、open item 为 0、checkpoint 当前且已验证、required evidence 齐全、retry/no-progress 未超限。
- idle 或 active goal 不得通过 final gate。

### R4 实现与发布 fail closed

- `implementation.final` 至少要求 `repo`、`build`。
- `implementation.commit` 至少要求 `repo`、`build`、`review`；`implementation.apply` 至少要求 `repo`、`build`、`plan`、`dry-run`。
- `release.final`、`commit`、`apply` 使用相同下限；`release.release` 至少要求 `repo`、`build`、`live`、`review`。
- policy 不能通过删减上述工件降低门禁。

### R5 安全与隐私

- V2 policy 与 event 一样递归拒绝 `prompt`、`messages`、`content`、`text`、`raw_input`、`raw_output`、`objective`。
- decision 只返回 task mode、适用性和稳定 ID/计数，不返回原始内容。

### R6 兼容与迁移

- `runtime_control.policy/v1` 继续按原语义工作，缺省为 legacy implementation 行为并返回 `runtime_control.decision/v1`。
- V1 不接受 `readonly` 或 `release` task mode；要使用任务模式必须迁移到 V2。
- V2 返回 `runtime_control.decision/v2`，显式包含 state-bound `task_mode`、`artifact_mode`、intake attestation/provenance、`gate_applicable` 与 `required_artifacts`。
- Decision 同时披露 `effective_artifact_mode`、`mode_authority_id` 与 `mode_authority_managed`，不能把 policy membership 冒充外部签名认证。

### R7 验证

- 覆盖 readonly final pass、readonly idle/active 不通过、implementation/release 工件缺失失败、非法或缺失 task mode 失败、敏感字段拒绝、非法适用性矩阵失败、V1 兼容回归。
- JSON Schema fixture 与 Engine 语义验证均通过。
