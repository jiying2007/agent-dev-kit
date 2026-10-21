# Harness 审核日期一致性

完整回归实际发现：主机为 America/Los_Angeles，UTC 已到 2026-10-21 而本地仍为 2026-10-20；canonical UTC review 的当天 metadata 被本地 `date.today()` 误判为未来。这是生产评估入口的日界不一致，不是测试硬编码日期。

目标：Harness 默认 report/gate 以 UTC 当前日评估，与 canonical review 时间一致；保持 gate 禁止显式 as_of、未来/过期拒绝、所有来源摘要和审核规则。只修改实际入口的默认日期，已存在的显式 effective_as_of 传递继续覆盖各维度；不改共享 validator 或其指纹规则。

验收：本地日历早一天和晚一天都输出同一 UTC 日；当前真实声明的 AI 审核不被误当未来；未来、过期、变更后旧审核、缺字段等负例不回归。版本更新使旧 README 绑定正确失效，本轮必须实际独立审核当前 Harness 来源，新增记录，不修改旧历史授权或旧审核。
