# 失败证据

- 2026-09-28 main CI `36420786576`：Python 3.8/3.11/3.12 的 regression job 均在 `test_agent_value` 失败，日志报 `receipt observed_at exceeds the configured max_age_days`。
- 固定 receipt 时间为 `2026-08-29T12:00:00Z`，main CI 开始于 2026-09-28 12:16 UTC 之后；PR CI 早于该窗口边界，故曾通过。失败是测试时钟漂移，不是生产 freshness 校验错误。
- `release-tag-promotion` 因 main CI 失败而跳过；不得手工移动 tag、绕过 CI 或把旧签名证据绑定到新 SHA。
