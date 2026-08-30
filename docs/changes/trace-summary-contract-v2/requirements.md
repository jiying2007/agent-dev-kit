# 需求：trace-summary-contract-v2

## 目标

为 R7 建立严格、平台中立、隐私有界的 workflow trace summary v2 和显式 per-run emitter，使调用方
提供的运行事实可以关联资产 bundle、runtime/model、tool、token/cost/latency、结果和人工介入，同时
不把 library API 冒充为自动 runtime/native target 集成。

## 要求

- bundle 必须是 64 位小写 SHA-256；runtime target/version 和 model version 必填。
- 有 runtime token 证据时，input/cached-input/output 均为非负整数，且 cached-input 不得超过 input；
  没有证据时必须显式 `not-available` + reason，不得填零。
- cost 必须是非负 amount + 三位大写 currency，或显式 `not-available` + reason。
- elapsed、human interventions 为非负整数；first-pass、wrong-skill、abstained 为布尔值。
- 有 outcome 证据时使用封闭 status/category；没有证据时必须显式 `not-available` + reason；并校验
  first-pass/abstain/wrong-skill、verification/guardrail/blocker 关系。
- 延续 v1 的 goal/prompt/tool/handoff/guardrail/verification/blocker/failure/next-goal 基础证据字段，
  其中 v2 的实际关联只使用 `goal_ref`/`next_goal_ref`；旧名固定为无内容 compatibility sentinel。
- schema 及嵌套对象拒绝未知字段；持久字段只接受 identifier/reason-code/ref；禁止 raw prompt、message、
  tool payload/arguments/result 和常见 secret value。
- 提供 `TraceRunFacts -> emit_trace_summary_v2` 显式 per-run API：一次调用只接收一个 `run_id` 并返回
  一个经过统一 privacy validator 和 v2 validator 的 summary。
- token/cost/outcome 未提供时默认写显式 `not-available` reason；emitter 不探测 runtime、不估算指标、
  不推断 outcome、不持久化内容。
- manifest 必须把 per-run 范围限定为“每次显式 API 调用”；自动 runtime/native target emission 仍需
  adapter conformance，不能由 library API 推导。
- 保留 v1 兼容引用；v2 采用独立 schema 和 validator。

## 验收

- JSON Schema Draft 2020-12 元校验通过。
- validator/emitter 正例、负例、敏感字段、默认 unavailable 和零值边界测试通过。
- `tests/run_all.sh` 的 full 和 quick 集均包含 `test_trace_summary.sh`。
