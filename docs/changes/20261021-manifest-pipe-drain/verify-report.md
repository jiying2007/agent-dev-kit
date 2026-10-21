# 管道修复验证

十一处生产 Manifest membership/guard consumer 已改为完整排空 stdin 的精确固定字符串匹配，并保护以连字符开头的查询值；同类测试 consumer 同步。真实上游错误和 `pipefail` 仍保留。

基线真实大输出记录 producer/matcher `[2,0]`，排空修复后 `[0,0]`；未知值仍为 1，匹配后 producer 故意退出 23 时仍返回 23。八个新增 Python 测试、大 handoff guard 正例及缺真实 guard 的负例均实际通过。独立审核找到并闭合初版漏修的第十一处调用点，未新增扫描排除或修改 Python producer 错误处理。

两次完整回归历史分别是主动中断和 99/101；第二次暴露的 UTC 日界及旧 Harness 来源绑定问题已在独立变更 `20261021-harness-utc-date` 修复/重审。最终同一 8.0.37 源码候选于 2026-10-21T02:09:22.356229Z 完成完整回归：**101/101，exit 0**。原始输出、时间清单、当前日 gate 与整合审核见该变更的 `verify-report.md` 和 `evidence/`。

首轮 Spec/Quality 与后续 NUL 边界调查时间分列于 `review-report.md`。本轮证明了当前可复现的管道机制，没有倒推 2026-10-20 缺少内层 PIPESTATUS 的历史失败根因。后续受保护 CI、发布与 Root 晋级继续由真实执行回执决定。
