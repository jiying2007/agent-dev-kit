# 需求：run-evidence-composition-v1

## 目标

提供平台中立、显式调用、无副作用的 Run Evidence composition API。调用方为一个 run 提供 typed
observation，API 生成一个已验证 Trace Summary v2、零到多个 test-layer Agent/Skill/Profile receipt，
并使用现有 Agent Value emitter 生成 test-only、不可作为 quality promotion 证据的 measurement。

## 要求

1. 每次调用恰好生成一个经过 `validate_trace_summary` 的 Trace v2 summary。
2. `source_trace_ref` 必须等于 trace canonical JSON 的 SHA-256 opaque ref。
3. receipt 只能是 `evidence_layer=test`；本 API 不接受或生成 runtime/field authority、attestation 或
   production eligibility。
4. receipt 的 manifest ref、asset bundle、runtime target 和 source trace 必须由 composition 从当前
   manifest/trace 复制或计算，调用方不能覆盖。
5. 同一个 run 内重复 Agent/Skill/Profile asset observation 必须 fail closed；invocation ref 由 trace ref、
   asset kind 和 asset ID 确定性生成。
6. trace outcome 不可用时只允许 trace-only composition；不得为 asset 生成 outcome、零值或成功/失败
   receipt。
7. receipt 必须经过现有 schema、canonical body binding、manifest identity 和 privacy validator。
8. 有 receipt 时必须提供固定 aggregation window 和 as-of；receipt 必须位于窗口内。measurement 必须为
   `evidence_scope=test-only`、`quality_evidence_eligible=false`、`owner_review_required=true` 和
   `lifecycle_authority=none-evidence-only`。
9. API 不持久化、不联网、不探测或启动 runtime、不启用自动 instrumentation。

## 验收

- 正常 trace-only、单 asset、Agent/Skill/Profile 多 asset 组合通过。
- trace digest/source ref、receipt canonical ID、manifest/bundle/runtime/trace binding 可重算。
- 重复 asset、未知 asset、缺 outcome 但请求 receipt、窗口越界、隐私输入和 tamper 均失败。
- runtime/field、production authority 和 quality eligibility 不存在输入或输出提升路径。

