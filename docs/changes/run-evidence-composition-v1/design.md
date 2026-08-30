# 设计：run-evidence-composition-v1

## 数据流

```text
RunEvidenceObservation
  -> emit_trace_summary_v2
  -> canonical trace sha256 / source_trace_ref
  -> zero or more test receipt bodies
  -> validate_receipt
  -> emit_measurements
  -> validate composition wrapper
```

`RunEvidenceObservation` 组合现有 `TraceRunFacts`、UTC observation/window/as-of 和一组只含
`asset_kind + asset_id` 的 `TestAssetObservation`。Receipt 的 evidence layer、manifest、bundle、runtime、
source trace、routing/outcome、privacy、retirement signal 和 evidence ref 都由 composition 决定，不向
调用方开放平行声明。

## 真实性边界

- Trace canonical digest 使用 typed core 的 `canonical_json_bytes` 和 `sha256_bytes`。
- Receipt invocation ref 使用 trace ref、asset kind/ID 的 canonical digest；receipt ID 使用完整 receipt
  body digest。
- Trace outcome 为 `not-available` 时，asset observations 非空即失败；不构造假的 receipt。
- Asset receipt outcome、abstain、wrong route、first pass 和 human interventions 只投影已验证 trace 字段。
- Test receipt 不含 authority attestation；Agent Value v1 固定 production=false、quality ineligible。
- Composition schema 约束 wrapper；Trace、receipt、measurement 继续由各自 SSOT schema/validator 约束，
  避免复制子合同。

## 权限与副作用

模块是纯 library composition：不写文件、不访问网络、不调用外部 runtime、不持有 verifier callback。
持久化、runtime adapter 和 production authority 不在本变更范围。

## 回滚

删除独立 module、composition schema/resource、定向测试、runbook 和本 change；现有 Trace 和 Agent Value
API 不受影响。

