# 实施与验证

- [x] 检索 release/distribution 全部调用点、读取现有源码/归档限制；verify：调用点扫描及 negative-results.md。
- [x] 保留 ignored 输入、改名发布、source 摘要漂移反例；verify：修复前 12 用例真实失败，见 negative-results.md。
- [x] 实现固定 tree 快照构建；verify：13 项发布完整性回归及 hidden-index-flags.log。
- [x] 完整有界 source 清单校验；verify：22 项归档预算、13 项发布完整性、14 项 strict JSON 回归。
- [x] 统一公开 publish 验证和三资产集合；verify：真实 artifact dry-run 与捕获上传字节，见 release-gate.log。
- [ ] 独立 Spec/Quality 审核；verify：摘要绑定审核记录。
- [ ] 版本、全回归、受保护合入、immutable Release 与 Root 固定；verify：精确 SHA 的主线/发布证据。
