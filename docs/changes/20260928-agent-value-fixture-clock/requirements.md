# Agent Value 固定时间夹具修复

- 目标：使 Agent Value 回归不随真实日期跨过 30 天 freshness 窗口而失效。
- 范围：仅修复 `tests/test_agent_value.py` 的测试时钟与确定性过期反例；不改生产 receipt 验证、窗口配置或发布门禁。
- 验收：7.12.4 源码版本前进门禁与 Python 3.8/3.11/3.12 的主 CI 回归通过，固定夹具在指定 `as_of` 下通过，超过 30 天仍明确拒绝。
- 回退锚点：main `9dc8c6794f835e9bf8bfb6e8c6eeba8d3013a731`，其源码未放宽 freshness，但测试在 2026-09-28 12:00 UTC 后失效。
