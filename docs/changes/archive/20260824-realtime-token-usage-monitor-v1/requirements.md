# 需求基线：realtime-token-usage-monitor-v1

## R1：canonical usage 事件

- 输入为逐行 JSON（JSONL），每条必须包含唯一 `event_id`、`event_type`、`scope_id` 和非负
  `total_tokens`。
- `event_type` 支持 `usage.delta` 与 `usage.snapshot`：delta 表示本次增量；snapshot 表示 scope
  的累计读数。
- 可选字段只用于细分观测：`input_tokens`、`output_tokens`、`cached_input_tokens`、
  `cache_creation_input_tokens`、`reasoning_tokens`、`observed_at`、`provider`、`model`。
- core 不猜测厂商 cache 计费语义；预算累计只使用 adapter 提供的 `total_tokens`。

## R2：实时状态与动作

- 每消费一条事件立即 flush 一条结果，至少包含累计 Token、增量、预算、占比、状态和建议动作。
- 默认阈值：`warn=70%`、`critical=90%`、`exhausted=100%`。
- 动作固定映射：`ok -> continue`、`warn -> checkpoint`、`critical -> compact`、
  `exhausted -> stop`；监测器只建议，不执行外部动作。

## R3：速率与耗尽预测

- 至少两条带 UTC/RFC3339 `observed_at` 的有效事件后，计算平均 `tokens_per_minute`。
- 速率大于零且仍有预算时输出 `eta_seconds`；证据不足时显式为 `null`，不使用墙钟补猜。

## R4：幂等、snapshot 与恢复

- 重复 `event_id` 不重复计费，输出 `duplicate=true`。
- 同一 `scope_id` 的 snapshot 不得倒退；倒退必须 fail closed。
- 同一 `scope_id` 不得混用 delta 与 snapshot，避免相同 usage 被双重累计。
- 可选状态文件必须原子写入，只保存计数、事件 ID、scope snapshot、时间和配置，不保存正文。
- 从状态恢复时预算和阈值必须一致；不一致则拒绝恢复。

## R5：安全与边界

- 拒绝 `prompt`、`messages`、`content`、`text`、`raw_input`、`raw_output` 等正文键。
- 数字必须是整数且非负；布尔值不得冒充整数；未知 event type、非法时间和非法 JSON 失败。
- 默认不联网、不写状态、不后台运行；只有显式 `--state-file` 才写受控路径。

## R6：CLI 与退出码

- 稳定入口：`devkit.sh token monitor --budget-tokens N [--input PATH|-]`。
- 默认输出 JSONL；EOF 后输出 `token_monitor.summary/v1`。
- `--gate` 时最终状态为 exhausted 返回非零；格式/合同错误始终非零。

## R7：兼容与可观测性

- 旧 `token-budget`、`task-cost`、eval usage 和 `monitoring.sh` 行为不变。
- 输出不包含输入原文，provider/model 仅作为可选低敏标签；summary 可被长任务 checkpoint 索引。

## R8：验收

- delta、snapshot、重复事件、恢复、四级阈值、速率/ETA、敏感键和错误路径均有确定性测试。
- 1000 条事件的本地流式处理不依赖网络，且逐条输出可被 JSON parser 读取。
- `validate --strict`、quick/full 相关回归和根仓治理门禁通过后才允许完成声明。

## 停止条件

- 单一失败根因 retry budget 为 2；第三次前 replan。
- 相关 dirty scope 或 HEAD 变化、需要读取厂商私有库、需要主动终止进程或新增网络写时停止。
- stop condition：`pass | replan | split | blocked | abort`。
