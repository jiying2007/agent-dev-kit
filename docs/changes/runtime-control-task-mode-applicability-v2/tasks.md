# Tasks: Runtime Control Task Mode Applicability V2

- [x] T1 固定 V1 readonly 误报复现，记录根因和负结果。
- [x] T2 增加 V2 policy/decision schema 与 Engine 语义验证。
- [x] T3 实现 task mode gate applicability，保留 V1 legacy lane。
- [x] T4 增加 readonly、implementation、release、安全和兼容回归测试。
- [x] T5 运行定向测试、schema 验证、compile、strict validate 和相关门禁。
- [x] T6 完成首轮 whole-diff review，记录验证证据和残余风险，提交主 Agent 交叉审查。
- [x] T7 修复 CR4：把 task/artifact mode 绑定 goal intake attestation/provenance，禁止 evaluate 覆盖。
- [x] T8 增加 attestation tamper、非法 mapping、final override 与 replan-only 正负测试。
- [x] T9 修复 CR5：intake 绑定 goal/request/routing/authority，policy 增加 managed authority registry。
- [x] T10 Production 默认无 verifier；unverified readonly 自动提升 implementation floor。
- [x] T11 增加 trusted ID + arbitrary digest + self-hash 伪造反例与 test-only verifier 结构正例。
- [ ] T12 在受管 composition root 接入外部 routing decision/signature verifier；完成前端到端 authority trust 保持 open。

## 工具边界

- 当前环境没有 `ruff` 可执行文件；未联网安装依赖。以 `py_compile`、`git diff --check`、定向测试和 strict validate 覆盖本轮代码质量门禁，`ruff` 留给支持的 Python 3.11/3.12 release 环境复核。
