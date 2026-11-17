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

## 按需诊断纯投影

`agent_dev_kit.trace_summary.diagnose_trace_summary(value)` 先调用同一 `validate_trace_summary`，
再返回独立的 `facts` 与 `findings`。它不修改输入，同一输入重复调用结果相同；不读取任务包、
网络、时间或随机数，不调用模型、不估价、不写状态。不接受未经校验的额外字段或原始日志正文。

```python
from agent_dev_kit.trace_summary import diagnose_trace_summary

diagnostics = diagnose_trace_summary(summary)
```

`facts` 保留原 outcome、failure_pattern、first_pass_success、全部 tools/handoffs/guardrails/verification、
Token/cost、elapsed_ms、human_interventions、wrong_skill、abstained 和 blockers。缺测值与 reason
原样保留；合法实测零值不变。Trace 没有记录的 `attempt_count`、`recorded_model_call_count`、
`tool_outcome_counts` 明确为 `not-available / not-recorded-in-trace-summary`。
成功与失败混合的工具 `partial` 不提供精确失败次数；`first_pass_success=false` 不提供重试次数。

每条 finding 包含 `code`、指向原 Trace 的 `location` 和独立复制的原 `fact`。
重复名称不合并，全部匹配项按原数组位置保留；检查的已有 opaque `evidence_ref` 随事实保留。

| Code | 记录条件 |
|---|---|
| `outcome-status` | outcome 不是 succeeded，包括原始 not-available 原因 |
| `metric-unavailable` | Token 或 cost 明确 not-available |
| `tool-outcome` | 工具汇总为 partial、failed、blocked、cancelled 或 not-available |
| `handoff-outcome` | handoff 为 failed、blocked 或 cancelled |
| `guardrail-failed` | guardrail 为 failed |
| `verification-status` | 每个 failed 或 not-run 检查 |
| `blocker` | 每个已有 blocker |
| `failure-pattern` | 已有 failure_pattern 不是 none |
| `wrong-skill` | 已有 wrong_skill 为 true |

finding 是事实索引，不是新的成功裁决、风险分数或因果分析。重复调用数不能证明浪费或盲重试，
墙钟与 handoff 数不能证明并行等待、节省或模型效果。无需关注的项目仍可在 `facts` 与原 Trace 回读。

只有 [task import 的显式 `--diagnostics`](task-evidence.md#按需查看诊断) 会用同次已核验账本补充
三个计数字段，并加上已有 trace/events refs；它不改变 RunEvidence 或资格值。现有任务比较调用
仍采用默认路径，不自动生成诊断。
