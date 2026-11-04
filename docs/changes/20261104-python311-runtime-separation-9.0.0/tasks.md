# 有界验证状态

- [x] 创建独立 9.0.0 重大候选分支，不改已审核 8.2.3 凭据。
- [x] Python >=3.11 最低版本与两版本 CI/本地 Docker 声明，删除 3.8 条件依赖和兼容 module。
- [x] 明确 Runtime Bundle 不包含 ADK Python 源码的结构测试与使用文档。
- [ ] 精确 HEAD 原生 Python3.11/3.12 全量测试、静态、CodeQL、dependency、平台和 branch-gc 全部 PASS。
- [ ] 9.0.0 精确源码的独立 Spec/Quality + Harness 七维审查凭据与源 SHA 绑定。
- [ ] 受保护合并、fresh-main CI、immutable v9.0.0 Release 及真实签名证据。
- [ ] Root 解除旧三版本 promotion matrix 假设，并以真实 v9.0.0 release 对 gitlink/lock/interface/evidence 等做受保护原子迁移。
- [ ] 消费端真实无 Python 运行时依赖与业务效果需 native evidence；静态打包检查不充当生产事实。
