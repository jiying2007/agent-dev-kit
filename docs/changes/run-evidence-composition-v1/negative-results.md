# Negative Results：run-evidence-composition-v1

| Before/attack | 旧风险 | 当前结果 |
|---|---|---|
| Trace outcome `not-available` 但请求 asset receipt | composition 可能把未知 outcome 补成失败或成功 | 拒绝；只允许 trace-only |
| `abstained=true` 自动写 `abstain_correct=true` | 把 abstain 行为误当为正确性证据 | 拒绝 asset composition；正确性需未来独立观测合同 |
| 同一 run 重复 asset | measurement 双计数 | 在 receipt 生成前拒绝 |
| 合法 receipt 重算 ID 后篡改 routing/outcome | 单独 schema 可通过但不再是 trace 投影 | validator 对 trace 逐字段重算并拒绝 |
| 替换 trace ref、evidence refs、invocation ref 或 measurement | wrapper 仍可能表面合法 | canonical ref 与 measurement 全量重算后拒绝 |
| observed time 在固定窗口外 | 跨窗口重放 | Agent Value window gate 拒绝 |
| runtime/field authority 注入 | test evidence 越级 | API 没有 layer/verifier/authority 输入面，固定 test-only |

这些负例只证明本地 test composition 的确定性和权限边界，不证明 native runtime 或 field evidence。
