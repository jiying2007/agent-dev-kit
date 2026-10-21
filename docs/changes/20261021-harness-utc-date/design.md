# 设计与风险

`run_harness_readiness` 仅在未提供 report-only `as_of` 时取 `datetime.now(timezone.utc).date()`，并通过已有 `effective_as_of` 传递至每个维度的 freshness 计算。这样同一次评估只采样一次日界。

共享 `readiness_evidence.py` 不改：真实入口已总是向它传日期，其私有默认仅由旧测试调用；修改其整文件会改变所有 scope 的 validator 指纹，令不相关的历史 source-change records 失效。保留指纹合同和原始字节，不为通过检查放宽绑定。

新增确定性测试模拟主机日历在 UTC 两侧，不改变实际系统时间、TZ 或 HOME。另以真实 Harness 评估链验证当前 UTC 的委派审核可达；原有历史、未来、过期、scope 与完整源绑定测试继续执行。

当前 source readiness 用实际独立 AI 复审生成新记录；日期取真实审核完成时间。它只证明 source readiness，field_evidence 仍为 not-verified，不能生成 Native/G22/LTA/M5 资格。
