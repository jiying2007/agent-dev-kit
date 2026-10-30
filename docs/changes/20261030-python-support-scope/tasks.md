# 区分 Python 兼容与验证范围：任务

状态：VERIFYING。实现与定向验证完成；真实独立审核、受保护 CI、合并和发布仍待完成。

- [x] 实现上述既有入口的最小变更。
- [x] 从验收条件补充确定性临时目录/fixture 回归。
- [x] 运行定向验证，保存原始输出并检查差异。
- [ ] 运行适用完整回归和受保护 CI。
- [ ] 取得真实独立 Spec/Quality 审核后，正常合并并核验 main。

环境：当前工作区不含用户的 ~/codex Knowledge Provider/Execution Policy，相关运行时记录为 NEEDS_REVIEW；不冒充 Dot 运行记录，不创建运行时策略或知识收据。

验证记录（2026-10-30，Python 3.12）：Python launcher 契约及新增 4 项分类测试通过；涵盖低于包下限、3.8/3.9/3.10 EOL、3.11/3.12 CI 范围，以及未验证的新解释器。`validate --strict` 通过。真实 Python 3.8/3.11 执行由公开 CI 矩阵验证；分类 fixture 不冒充这些解释器的实际运行。

同轮完整回归初次为 98/101：两项 workflow 契约失败已修正并逐项复测通过；余下一项 Harness readiness 因源码变更拒绝旧审核凭据。保留原兼容下限及 strict 开关语义，新的诊断字段不签发 upstream/security/runtime/product 资格。

负面查证：本工作区未找到 `knowledge/L2-domain/lessons.md`；没有可复用的已登记独立审核自动任务。未调用 Codex/Work、付费模型或额外代理。

