# 设计：agent-value-lifecycle-v1

## 数据边界

- `manifest.json` 继续提供 Agent/Skill/Profile 身份和 Agent permission/handoff 上限。
- `manifests/agent_value_contracts.json` 只提供价值治理合同，不成为平行身份目录。
- `schemas/asset-invocation-receipt-v1.schema.json` 定义 runtime adapter 或受治理测试可产出的脱敏观测记录。
- `schemas/asset-value-measurement-v1.schema.json` 定义确定性 measured emitter 输出；默认无 receipt 时为 `not-measured`，不产生零值指标。
- emitter 不主动采集、不访问 runtime、不写外部状态，只消费显式 receipt 输入；test/runtime/field 分层输出，不能混合成同一统计组。

## 校验顺序

1. 使用 Draft 2020-12 Schema 校验合同或 receipt 的封闭结构。
2. 从当前 manifest 构造 Agent、Skill、Profile identity index。
3. 检查 Agent 全覆盖、无重复/未知 ID、权限等级和 capability 上限、handoff 引用与 eval contract。
4. 检查 quality KPI 没有数量或 Token proxy。
5. receipt 校验 identity、路由状态一致性、测量状态、指标类型、evidence layer 和 privacy/raw 边界。
6. emitter 拒绝重复 receipt 或同资产同 layer 的重复 invocation observation，再按 `asset_kind + asset_id + evidence_layer` 聚合。
7. 缺少可选观测字段时输出 `status=not-measured` 与原因，不生成 `value=0`；数量和 sample size 仅是诊断/分母证据，不参与质量判断。
8. runtime/field receipt 必须由调用方注入 verifier 并返回严格 `True`；test layer 只做 schema/body integrity 校验，输出 `source_verification=structural-only`。
9. `receipt_id=ref:sha256(canonical receipt body without receipt_id)` 用于 replay/tamper 检测；不代表 source authority。
10. 拒绝未来 `observed_at`，聚合输出最早/最晚 UTC observation window。
11. canonical authority policy 默认关闭；runtime/field 必须由 registry 中 authority 的 attestation 绑定 payload/manifest/bundle/layer/target/trace，再由外部 verifier 复核。
12. 聚合调用方固定 window/as-of；receipt 超龄或窗外即拒绝，每个 asset/layer 输出自己的实际观测窗口。
13. 可选指标只有 observed==applicable 才 measured；部分覆盖输出 `not-measured/incomplete-coverage` 和 coverage。
14. evidence scope 只描述证据层；v1 的 `quality_evidence_eligible` 固定 false，owner review 永远必需且 lifecycle authority 为 none。
15. mutable input contract 只能注册 non-production authority；未来 production authority 必须由独立版本化 registry change 提供。

## 指标语义

- `task-success-rate`：`outcome=succeeded` 在非 abstained 任务中的比例。
- `first-pass-success-rate`：只使用非 abstained 且显式 `first_pass` 的任务；字段缺失时 not-measured。
- `wrong-route-rate`：只以 routed receipt 为分母；没有 routed receipt 时 not-measured。
- `abstain-precision`：只以带强制 correctness label 的 abstained receipt 为分母。
- `human-interventions-per-task`：受验证 receipt 的干预次数均值。
- time/escaped-defect/rollback：仅聚合显式观测字段，缺失不补零；escaped-defect 只接受 field，rollback 只接受 runtime/field。

## 权限模型

权限等级为 `read-only < diagnostic < code-write < build-release`。等级比较只判断 ceiling；effect 与 tool
capability 还必须分别落在 manifest permission profile 对应的 allowlist 中，避免只靠等级产生横向扩权。

## 退役边界

receipt 的 retirement signal 仅允许 `retain`、`consolidate-candidate`、`retire-candidate` 或
`insufficient-evidence`。它只是证据信号，不代表删除、禁用或 owner approval。
