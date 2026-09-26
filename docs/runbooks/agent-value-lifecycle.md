# Agent/Skill/Profile Value Lifecycle Runbook

本 runbook 用于验证 Agent role contract，并从显式提供、受验证的 Agent/Skill/Profile invocation receipt
派生 measurement。`emit_measurements` API 已可用，但不会自动采集、不会自动持久化 receipt/measurement，也不会据此
宣称全局 runtime usage 已被测量；没有有效输入时，全局状态仍为 `not-measured`。

## 权威边界

- `manifest.json` 是 Agent、core/optional Skill、Profile 身份和组成的唯一 SSOT。
- `manifests/agent_value_contracts.json` 只引用 `agent_id` 并声明 role/value contract；不得复制 Agent 描述、路径、
  default Skill，或创建 Skill/Profile 身份清单。
- `schemas/asset-invocation-receipt-v1.schema.json` 是 receipt 结构合同。
- `schemas/asset-value-measurement-v1.schema.json` 是 measured/not-measured 聚合输出合同。
- `src/agent_dev_kit/agent_value_contracts.py` 是 Agent Value contract/receipt loading 与语义验证的唯一 Python authority。
- `src/agent_dev_kit/agent_value.py` 只负责编排 validated contract/receipt 到显式输入驱动的
  `emit_measurements` 输出及 CLI；它不是 contract facade、runtime collector 或持久化服务。
- `manifests/agent_value_trust_registry.json` 是 runtime/field receipt 的受管签名 verifier registry；默认 authorities 为空。
- `src/agent_dev_kit/agent_value_trust.py` 负责 owner-reviewed registry、receipt/bundle/binary digest 和 Sigstore/cosign identity 验证；它不收集 receipt，也不启用 canonical contract。

## Agent 合同门禁

每个 manifest Agent 必须且只能有一个合同，包含：

- role inputs/outputs
- permission envelope 与 tool capability
- decision authority 与升级边界
- manifest 内有效 handoff 和 required payload
- required evidence、assumption scope、eval suite

权限采用 `read-only < diagnostic < code-write < build-release` ceiling，并同时检查 effect/tool allowlist。
合同不能通过只改 permission 名称或 capability 列表提升 manifest 权限。

## Receipt 语义

一个可用于派生 measurement 的 receipt 必须来自真实观测，且满足：

- `measurement_status=measured`
- `asset_id` 可在当前 manifest 对应 kind 中解析
- `routed` 与 `abstained` 恰好一个为 true
- `wrong_route=true` 只能出现在 routed invocation
- abstained routing 与 abstained outcome 一致
- `human_interventions` 是非负整数
- `receipt_id` 绑定 canonical receipt body；该 hash 只证明内容完整性，不证明来源 authority
- `receipt_id`、`invocation_ref`、`source_trace_ref` 和 `evidence_refs[]` 均为 `ref:<sha256>` opaque reference
- `observed_at` 不得晚于验证时钟
- test receipt 只接受结构/完整性校验，measurement 标记为 `source_verification=structural-only`
- runtime/field receipt 必须由 Python composition root 注入 `evidence_verifier`；默认无 verifier 时 fail-closed
- canonical `evidence_authority_policy` 默认 `disabled/backend=not-configured/authorities=[]`；此时即使任意 verifier
  返回 `True` 也必须拒绝 runtime/field receipt
- 受管 authority attestation 必须绑定 canonical payload digest、当前 `manifest_ref`、asset bundle、evidence layer、
  runtime target 和 source trace；authority ID、layer、target 必须落在启用的 registry scope 内
- receipt 必须落入调用方固定的 aggregation window/as-of，并满足 `max_age_days`
- retirement signal 只是 `retain`、`consolidate-candidate`、`retire-candidate` 或
  `insufficient-evidence` 证据信号，不授权删除或禁用
- `raw_content_stored=false`，不含 prompt、message、credential、raw log、tool payload 或 operator identity

不得创建伪造 receipt 来填补 usage 空白，也不得把 test fixture 重标为 runtime/field。调用方可以把真实观测形成显式、
脱敏 receipt，再交给 validator/emitter；本模块不会自行保存输入或输出。

### Prepared managed receipt construction (7.8.0)

真实 runtime/field adapter 不再需要手工拼 `authority_attestation` 与 `receipt_id`。使用
`ManagedInvocationObservation` + `prepare_managed_receipt()`，由 receipt authority 根据显式已观测 facts
确定性生成：

- 当前 manifest 绑定的 `manifest_ref`；
- canonical payload `body_sha256`；
- authority/layer/runtime-target/source-trace scope attestation；
- content-addressed `receipt_id`；
- schema、asset identity、routing/outcome、time window、retirement signal 与 authority scope 的结构校验。

该 API 的输出只是 **prepared-not-verified receipt**：它不会签名、不会调用 verifier、不会产生
`managed-authority-verified` 结论，也不会把调用方声明提升成 runtime/field truth。prepared receipt 仍必须交给
owner-reviewed registry 对应的外部签名流程，并最终通过 `validate_receipt(..., evidence_verifier=...)` 或 portable
managed verifier 复验后，才可进入 `emit_measurements()`。

没有有效 receipt 输入时，正确状态就是：

```json
{"status":"not-measured","runtime_enabled":false,"usage_evidence":"none-claimed"}
```

## 验证命令

验证合同、live manifest，并查看空输入的 `not-measured` measurement：

```bash
rtk bash -lc 'PYTHONPATH=src python3 -m agent_dev_kit.agent_value \
  --manifest-root . --emit-measurements --summary-json'
```

CLI 没有 trust verifier、固定 aggregation window/as-of 注入点，因此只适合验证 `evidence_layer=test` 的
structural receipt，不执行非空 measurement 聚合：

```bash
rtk bash -lc 'PYTHONPATH=src python3 -m agent_dev_kit.agent_value \
  --manifest-root . --receipt path/to/receipt.json --summary-json'
```

runtime/field receipt 必须由受审查的 Python composition root 使用 managed verifier；不要通过 CLI、lambda 或临时 callback 绕过。生产 adapter 可先用 typed builder 准备 receipt：

```python
from agent_dev_kit.agent_value_receipts import (
    ManagedInvocationObservation,
    prepare_managed_receipt,
)

prepared = prepare_managed_receipt(
    ManagedInvocationObservation(
        invocation_ref=invocation_ref,
        source_trace_ref=source_trace_ref,
        asset_bundle_sha256=asset_bundle_sha256,
        runtime_target=runtime_target,
        evidence_layer="runtime",
        observed_at=observed_at,
        asset_id=asset_id,
        asset_kind=asset_kind,
        routed=routed,
        abstained=abstained,
        wrong_route=wrong_route,
        outcome=outcome,
        human_interventions=human_interventions,
        retirement_signal=retirement_signal,
        evidence_refs=tuple(evidence_refs),
        privacy_status="sanitized",
    ),
    manifest,
    reviewed_managed_contract,
    authority_id,
)
# prepared is not trusted evidence yet; sign/register/reverify it before aggregation.
```

验证与聚合继续走 managed verifier：

```python
from agent_dev_kit.agent_value import emit_measurements
from agent_dev_kit.agent_value_contracts import load_contract
from agent_dev_kit.agent_value_trust import build_managed_agent_value_evidence_verifier
from agent_dev_kit.model import Manifest

manifest = Manifest.load(adk_root)
contract = load_contract(adk_root / "manifests" / "agent_value_contracts.json")
# canonical contract 与 trust registry 默认都关闭 authority。部署 composition root 必须先取得
# owner-reviewed、managed、enabled 的 contract input，并让 authority/target/layer 与 registry exact 对齐。
verifier = build_managed_agent_value_evidence_verifier(
    manifest,
    reviewed_managed_contract,
)
measurement = emit_measurements(
    validated_receipts,
    manifest,
    reviewed_managed_contract,
    evidence_verifier=verifier,
    aggregation_window={"from": window_from, "through": window_through},
    as_of=fixed_as_of,
)
```

`build_managed_agent_value_evidence_verifier` 会把 contract authority 与 repository registry 的 backend、layer、runtime target、canonical receipt digest、Sigstore bundle digest、certificate identity/OIDC issuer 和 digest-pinned `cosign` 绑定。任一不一致都 fail-closed。opaque ref、content hash、临时 lambda 或未注册 authority 本身不能替代这个裁决。

回归：

```bash
rtk bash tests/test_agent_value.sh
rtk bash tests/test_agent_value_trust.sh
rtk bash tests/test_runtime_boundary.sh
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/run_all.sh --quick --fail-fast
```

### Portable managed evidence package verification (7.7.0)

Cross-repository consumers may need to verify immutable runtime/field receipt bundles without writing evidence into the pinned ADK source tree. Use `build_portable_managed_agent_value_evidence_verifier(..., registry, bundle_root=...)` for that case.

The portable builder changes **only** the filesystem root used to resolve registry `bundle_path` values. It does not relax or replace any trust check: the reviewed enabled contract, registry schema, authority/backend/layer/target scope, canonical receipt digest, signature-bundle digest, certificate identity/OIDC issuer, and digest-pinned cosign binary are still mandatory. `bundle_root` itself must be a real directory and must not be a symlink; each registry path remains safe-relative and is confined beneath that root.

This enables a consumer such as Root to keep a digest-bound evidence package beside its own runtime evidence, reverify signed receipts, and recompute the Agent Value measurement from those receipts while the ADK gitlink remains immutable. A precomputed measurement JSON alone is still not trust evidence.

## 质量与退役判断

质量判断优先使用 task success、first-pass success、wrong-route、abstain precision、人工介入、可信变更时间、
escaped defect 和 rollback 等 outcome 指标。Agent/Skill/Profile 数量、invocation/PR/report 数量及 Token 总量
只能用于容量和成本诊断，不能证明资产质量。

每个可选 KPI 同时报告 applicable/observed sample size 与 coverage。first-pass、可信变更时间、escaped defect、
rollback 未达到完整覆盖时保持 `not-measured/incomplete-coverage`，不能用部分样本生成 measured value。顶层
`evidence_scope` 区分 `test-only/runtime-verified/field-verified/mixed`。7.8.0 在 7.7.0 portable bundle-root 复验基础上增加 typed prepared receipt builder；
但 v1 contract 的 authority 仍强制 `production=false`，因此 `quality_evidence_eligible` 对所有 scope 继续固定为 false，
并始终输出 ineligibility reason、`owner_review_required=true`、`lifecycle_authority=none-evidence-only`。

未来若要支持 production quality evidence，仍必须新增独立 versioned contract/schema change，明确生产 authority 语义；
不得通过 registry copy、临时 contract 或 callback/lambda 把 `production` 改为 true。

合并或退役至少需要多个真实 measured invocation、代表性的成功与失败、wrong-route/abstain 分析、替代/删除
影响和 owner review。单条 receipt、测试 fixture 或静态 contract 都不能证明退役合理。

## 失败处理与回滚

- coverage 失败：先检查 manifest 是否新增/删除 Agent，再补或移除对应引用合同；不要复制 manifest 元数据。
- identity 失败：确认 receipt 的 kind 与当前 manifest 一致；历史资产必须走受治理的 supersession/retention 路径。
- permission/handoff 失败：以 manifest ceiling 为准；需要扩大权限或关系时必须走独立 owner-reviewed manifest 变更。
- privacy 失败：拒绝 receipt，回到 emitter 侧做字段删除或脱敏，不在 validator 中放宽 schema。
- trust 失败：runtime/field receipt 没有 verifier、verifier 拒绝或异常时保持 fail-closed；不能降级为 test 后继续宣称 runtime usage。
- measurement 缺字段：保留对应 KPI 的 `not-measured` 原因，不补零、不用数量或 Token proxy 替代。
- 回滚：删除本能力新增文件并从 `tests/run_all.sh` 移除 `test_agent_value.sh`；不会影响 runtime 或 target。
