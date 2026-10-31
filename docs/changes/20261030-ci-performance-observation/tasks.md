# 对照本次 CI 全量耗时：任务

状态：VERIFYING。实现与定向验证完成；真实独立审核、受保护 CI、合并和发布仍待完成。

- [x] 实现上述既有入口的最小变更。
- [x] 从验收条件补充确定性临时目录/fixture 回归。
- [x] 运行定向验证，保存原始输出并检查差异。
- [ ] 运行适用完整回归和受保护 CI。
- [ ] 取得真实独立 Spec/Quality 审核后，正常合并并核验 main。

环境：当前工作区不含用户的 ~/codex Knowledge Provider/Execution Policy，相关运行时记录为 NEEDS_REVIEW；不冒充 Dot 运行记录，不创建运行时策略或知识收据。

验证记录（2026-10-30，Python 3.12）：performance budget 的既有严格失败、超预算 report-only 告警、实际 full timing 对照及缺失 timing 负例通过。`test_hosted_workflow_hygiene.sh` 与 `test_workflow_contract.sh` 通过；维持既有失败传播与 best-effort artifact upload，缺失 timing 由报告步骤明确告警。

同轮完整回归初次为 98/101，耗时 288491 ms；两项 workflow 失败已逐项复测通过，旧版 Harness 独立审核失效仍阻断。该单次本地耗时不代表性能改善、稳定分布或托管 CI；公开 CI 将记录自身实际 observed/budget。最慢 release archive 测试已使用进程内缓存的最小真实 fixture，未为缩短耗时删减负例或签名/恢复断言。

负面查证：本工作区未找到 `knowledge/L2-domain/lessons.md`；没有可复用的已登记独立审核自动任务。未调用 Codex/Work、付费模型或额外代理。
