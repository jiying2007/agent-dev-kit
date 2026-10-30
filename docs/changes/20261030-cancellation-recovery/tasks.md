# 取消期间保留事务恢复材料：任务

状态：VERIFYING。实现与定向验证完成；真实独立审核、受保护 CI、合并和发布仍待完成。

- [x] 实现上述既有入口的最小变更。
- [x] 从验收条件补充确定性临时目录/fixture 回归。
- [x] 运行定向验证，保存原始输出并检查差异。
- [ ] 运行适用完整回归和受保护 CI。
- [ ] 取得真实独立 Spec/Quality 审核后，正常合并并核验 main。

环境：当前工作区不含用户的 ~/codex Knowledge Provider/Execution Policy，相关运行时记录为 NEEDS_REVIEW；不冒充 Dot 运行记录，不创建运行时策略或知识收据。

验证记录（2026-10-30，Python 3.12）：新增 5 项取消恢复测试通过，既有 7 项安装升级测试通过。覆盖 backup/publication 之后的 KeyboardInterrupt/SystemExit、补偿中断、receipt 发布后中断、保留材料及后续拒绝覆盖，普通成功与完整补偿无残留。README 增加三条任务入口，未宣称真实用户省时或 live 恢复验证。

同轮完整回归初次为 98/101：两项 workflow 契约失败已修正并逐项复测通过；余下一项 Harness readiness 拒绝旧版 source-bound 独立审核。候选 8.1.4 尚未取得新源码的独立审核；没有重写旧回执、放宽门禁或将实现者自检记作独立审核。

负面查证：本工作区未找到 `knowledge/L2-domain/lessons.md`；没有可复用的已登记独立审核自动任务。未调用 Codex/Work、付费模型或额外代理。
