# 本地任务

- [x] 核对五条 local_path 方法来源与根仓 pin/远端 HEAD，保护历史 `retrieved_at` 与旧 URL。
- [x] 补规范地址和 exact 元数据；现有 checker 做离线一致性与来源约束。
- [x] Python 3.8 正负例 7/7，覆盖缺身份、关系冲突、非法 SHA/主机、未来日期、同仓重复项冲突、manifest 读取边界，以及可选根仓锁 URL/pin 漂移和显式新鲜度失败。
- [x] 对隔离根仓真实 `reference_pins.json` 的只读核验在 `--as-of 2026-09-28 --max-observation-age-days 0` 下通过，未读取参考 checkout 或更新 pin。
- [x] 新增可选 lock/新鲜度门禁后，当前 Python 3.8 quick 回归 53 项中 52 项通过；唯一失败是未提交工作树的 runtime bundle clean commit 身份，内部 3 项通过。严格校验、release check、来源对照、生态标准、退役引用、文档命令及格式门禁通过。
- [ ] 当前快照 full 回归、独立复审及 clean commit 身份留待统一收口；保持本地未提交。
