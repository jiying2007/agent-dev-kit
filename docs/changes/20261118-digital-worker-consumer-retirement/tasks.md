# 执行与验收

- [x] 定位并删除 Digital Worker 专属历史消费表面。
- [x] 复用 ADK 受控源身份，升级到 11.4.9，保留 11.4.8 未测历史。
- [ ] CI 在该 PR 最新 head 完整成功；Codex/Claude 保留。
- [ ] 独立复审、受保护合并；真实 main CI 及不可变发行。
- [ ] Root 当前 source-only 消费链按最新不可变 ADK 单次晋级。

此 change 不创建额外工作流、兼容别名、调度任务或外部 model runtime。
