# Run Evidence Composition

`agent_dev_kit.run_evidence` 把一次调用方已观测的 test run 组合成同源 Trace Summary、test-layer
Agent/Skill/Profile receipts 和不可 promotion 的 value measurement。

## 边界

- 每次调用只处理一个 `TraceRunFacts.run_id`，不跨 run 保存状态。
- API 不读写文件、不联网、不探测 runtime、不接受 verifier callback。
- `source_trace_ref` 是 Trace canonical JSON 的内容寻址 ref；receipt 的 manifest、bundle、runtime 和 trace
  binding 由 composition 生成，调用方不能另行声明。
- 只允许 `evidence_layer=test`；输出固定 `evidence_scope=test-only`、
  `quality_evidence_eligible=false`、`owner_review_required=true`、`lifecycle_authority=none-evidence-only`。
- Trace outcome 不可用时只能生成 trace-only wrapper，不能伪造 asset receipt 或 value。

## Python API

```python
from agent_dev_kit.run_evidence import RunEvidenceObservation, TestAssetObservation, emit_run_evidence

result = emit_run_evidence(
    RunEvidenceObservation(
        trace_facts=trace_facts,
        observed_at=observed_at,
        assets=(TestAssetObservation("skill", "adk-requirements-triage"),),
        aggregation_from=window_from,
        aggregation_through=window_through,
        as_of=as_of,
    ),
    manifest,
    agent_value_contract,
)
```

调用方持久化前可再次调用 `validate_run_evidence`。Validator 会重算 trace ref、receipt body binding 和
measurement，任何 trace、receipt、window 或 measurement tamper 都 fail closed。

## 验证

```bash
rtk bash tests/test_run_evidence.sh
rtk bash tests/test_trace_summary.sh
rtk bash tests/test_agent_value.sh
```

真实 runtime/field composition、production authority、自动 instrumentation 和持久化必须走后续独立
adapter/conformance change；不得扩大本 API。
