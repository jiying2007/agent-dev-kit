# Requirements

## R1 State contract

- 输入 `long_task_state/v1`，包含 goal/stage/status、heartbeat、staleness seconds、retry budget、
  checkpoint、required/evidence refs、open items、completion claim 和 stop condition。
- `--as-of` 使用带 timezone RFC3339；默认 UTC now；输出披露 evaluated_at。

## R2 Anti-stall

- heartbeat 超过 threshold 或 retry used >= limit 时不得 continue/completed，建议 `replan`。
- 连续 `no_progress_heartbeats` 达到 limit 时，即使 heartbeat 新鲜也必须 replan。
- future heartbeat、非法计数、未知状态 fail closed。

## R3 Completion

- completed 只在 `completion_claim=pass`、open items 为空、checkpoint verified、required evidence
  全部存在时 `completion_allowed=true`。
- 证据缺失或 claim 不一致输出 fail + `replan`，不得以 status 字段自证。

## R4 Token integration

- 可选嵌入 `token_monitor.summary/v1`。
- in-progress 映射：ok=continue、warn=checkpoint、critical=compact、exhausted=stop。
- completed 且证据闭环时 Token 耗尽不推翻已完成事实，但输出 token status 供后续会话收口。

## R5 Safety

- evaluator 只读且不持久化；`recommended_action` 是 advisory，不是执行授权。
- 不回显 open item 文本、prompt/messages/content/raw input/output。

## R6 CLI

- `devkit.sh execution guard --state <json> [--as-of <rfc3339>] [--gate]`。
- JSON summary schema `execution_guard.decision/v1`；gate 对 replan/stop/blocked/abort 返回 3。

## R7 Acceptance

- fresh/stale/future/retry/token/completed evidence 正负路径均有测试。
- strict、quick/full、docs alignment、change verify 通过。
