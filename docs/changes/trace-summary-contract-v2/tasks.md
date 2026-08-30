# 任务：trace-summary-contract-v2

- [x] 定义严格 trace summary v2 JSON Schema。
- [x] 实现 schema 加载、隐私字段拒绝和跨字段 validator。
- [x] 在 trace/eval manifest 中登记 v2、兼容与 emitter 边界。
- [x] 增加正例、负例、敏感字段和零值边界测试。
- [x] 接入 full/quick `run_all` 聚合入口。
- [x] 运行定向、quick 和适用仓库门禁并记录新鲜证据。
- [x] 实现 typed per-run emitter API，并把 token/cost/outcome 缺证据显式建模为 `not-available`。
- [x] 增加 emitter per-run、默认 unavailable、隐私和不一致事实 fail-closed 测试。
