# 设计说明：official-freshness-utc-date-v1

## 架构影响
- official docs inline validator 的 default date 改为 UTC canonical date。

## 数据与配置影响
- summary JSON additive 增加 `evaluated_at` 与 `date_basis=utc`；旧 consumer 可忽略。

## 兼容性与迁移方案
- expiry 比较仍为 date-only 且 inclusive；无需迁移。

## 验证策略
- 两个相反 TZ 运行 summary，断言评估日期完全一致并等于 Python UTC date。
- 重跑 official docs、workflow、strict 和 full regression。
