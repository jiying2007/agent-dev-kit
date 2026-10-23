# 实施与验证

- [x] 检索 compiler/native/atomic IO/path owner 调用点；记录缺失知识来源与基线反例。
- [x] 添加 export 同根/根外 symlink 与正常替换恢复回归；verify：对应 Python 单测。
- [x] 实现路径身份复用、锁后及替换前校验；verify：导出与安装定向回归。
- [x] 添加 Native 多输出别名、硬链接、目录、FIFO、输入冲突及晚发 I/O 失败回归；verify：无害 CLI/单测。
- [x] 实现全输出预检、staging 和补偿恢复；verify：上述反例关闭且正向控制通过。
- [ ] 独立 Spec/Quality 审核；verify：逐文件摘要绑定的真实审核记录。
- [ ] 与发布合同变更串行整合，完成必要全回归和精确主线发布验证；verify：本地与远端原始证据。
