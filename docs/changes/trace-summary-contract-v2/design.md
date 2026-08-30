# 设计：trace-summary-contract-v2

## 决策

- v1 保持兼容；v2 是独立严格合同，不切换现有 target/OTel adapter 的兼容引用。
- v2 使用 `goal_ref`/`next_goal_ref`；既有 official governance 要求的 `goal`/`next_goal` 仅保留为
  固定 `not-applicable`/`null` sentinel，不承载文本。
- JSON Schema 负责字段存在性、identifier/ref、类型、封闭枚举、未知字段和数值下界。
- Python validator 负责 JSON Schema 无法直接表达的 `cached_input <= input` 和结果关系。
- tool evidence 仅保留工具名、调用次数和枚举结果，不接收 argument/result/payload；总调用数必须等于
  各工具 `call_count` 之和。
- validator 同时拒绝常见 credential/private-key/token 敏感值以及 NaN/Infinity cost。
- `raw_content_stored` 固定为 false；privacy status 只能是 sanitized、redacted 或
  no-sensitive-content。
- emitter 输入是 immutable typed dataclass `TraceRunFacts`；tool/handoff/guardrail/verification 也使用
  typed fact，输出只由 caller-observed 字段和固定 compatibility/privacy sentinel 组成。
- token/cost/outcome 各自接受 available typed fact、`MetricUnavailable(reason)` 或缺省值；缺省只转换为
  对应 `not-available` reason，不转换为零、失败或成功。
- emitter 每次显式调用返回一个已验证 summary，不写文件、不联网、不查询 pricing、不采集 runtime。
  `per_run` 只描述 API 调用粒度；target adapter 的自动 emission/native conformance 是独立 gate。

## 回滚

删除 v2 schema、validator/emitter、测试和 manifest 中 v2 条目即可；v1 和现有 adapter/target 引用不受影响。
