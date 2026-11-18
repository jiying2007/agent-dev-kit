# 验收任务

- [x] 实现统一严格 Manifest 读取及歧义数据、链接、超大输入负例。
- [x] 同步 11.4.10 七处版本身份和历史未测 candidate 记录。
- [ ] 原受保护 PR 的 required CI 与独立审核（首轮 99/102、第二轮 101/102：隔离 Runtime fixture 与 Docker 工具版本漂移已修复；两次剩余仅为严格 C90 示例在完成构建后抵达 CTest 时耗尽 15s 总预算，故只将这条冷编译＋CTest 用例提升至有界 30s，并保持所有真实检查）。
- [ ] 合并、自动发行不可变 11.4.10、release contract 与证据验证。
- [ ] Root 使用真实发行 source-only 晋级并验收 fresh-main CI。
