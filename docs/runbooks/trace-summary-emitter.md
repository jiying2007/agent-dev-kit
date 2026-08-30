# Trace Summary V2 Emitter

`agent_dev_kit.trace_summary.emit_trace_summary_v2` 是平台中立的显式 per-run library API。调用方为一个
run 构造一个 immutable `TraceRunFacts`，API 返回一个经过统一 privacy validator 和 v2 schema/关系
validator 的 summary；API 自身不写文件、不联网、不读取 provider pricing，也不启动或探测 runtime。

## 最小调用

```python
from agent_dev_kit.trace_summary import (
    GuardrailFact,
    TraceRunFacts,
    emit_trace_summary_v2,
)

facts = TraceRunFacts(
    run_id="run-20260830-001",
    task_id="task-example",
    asset_bundle_sha256="a" * 64,
    runtime_target="local-agent-runtime",
    runtime_version="2026.08.30",
    model_version="model-version-1",
    goal_ref="ref:" + "1" * 64,
    primary_skill="adk-verification-before-completion",
    prompt_version="prompt-v1",
    orchestration_mode="single-agent",
    tools_used=(),
    handoffs=(),
    guardrails=(GuardrailFact("privacy-boundary", "passed"),),
    verification=(),
    elapsed_ms=0,
    first_pass_success=False,
    human_interventions=0,
    wrong_skill=False,
    abstained=False,
    privacy_status="no-sensitive-content",
    blockers=(),
    failure_pattern="none",
    next_goal_ref=None,
)
summary = emit_trace_summary_v2(facts)
```

上述调用没有提供 token、cost 和 outcome 事实，结果会分别记录带 reason 的 `not-available`，不会用零、
失败或成功代替缺失证据。只有调用方确实观测到数据时，才传入 `TokenUsageFact`、`CostFact` 和
`OutcomeFact`；也可用 `MetricUnavailable(reason)` 提供受控 reason code。

## 边界

- 一个 API 调用只处理一个 `run_id`，不聚合多个 run，也不维护跨调用状态。
- `tool_calls` 仅由调用方提供的 typed `ToolUseFact.call_count` 确定性求和。
- 所有输出都经过 `privacy_ref.validate_no_secrets`；raw prompt、message、tool arguments/results/payload、
  secret-like value 和未知字段会 fail closed。
- API 可用不等于 target 已自动集成。runtime adapter 只有完成 native conformance 后，才能声明自动
  per-run emission。
- 持久化、retention、Evidence Graph 关联和外部 exporter 由调用方的已审查边界负责，本 API 不扩权。
