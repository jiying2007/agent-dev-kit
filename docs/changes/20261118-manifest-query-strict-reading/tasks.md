# 验收任务

- [x] 实现统一严格 Manifest 读取及歧义数据、链接、超大输入负例。
- [x] 同步 11.4.10 七处版本身份和历史未测 candidate 记录。
- [ ] 原受保护 PR 的 required CI 与独立审核（首轮发现隔离 Runtime fixture 未携带现有 strict_json，和本地 Docker 质量工具 pin 漂移，均修复后重新核验；另有一次 CMake 15s 时限达到，需复测确认是否环境耗时）。
- [ ] 合并、自动发行不可变 11.4.10、release contract 与证据验证。
- [ ] Root 使用真实发行 source-only 晋级并验收 fresh-main CI。
