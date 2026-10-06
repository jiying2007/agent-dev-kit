# 安装证据、运行扫描与维护契约审查

基础：canonical agent-dev-kit main `e9fab289f98961922342fa32a4f629067a5a9e21`，source 7.14.2。范围为 ADK 安装输入、运行边界检查和维护工具；llm_agent URL/推广证据修复独立交付，不混入此包。

1. 安装计划和 receipt 拒绝重复键、非有限数值、超过 4 MiB 或 64 层的 JSON；输入失败先于目标锁和安装写入。原 schema、digest、安装事务和 rollback 契约保持有效。
2. runtime-boundary 的 rg 无命中合法；工具缺失或扫描失败不得输出 pass。保留原禁用规则和排除项。
3. 维护不得把未执行报告声明为已执行，不得无审查删除用户日志、源码、证据、备份或更改权限。提供有界只读候选，拒绝旧的无界 --apply。
4. 公开维护 CLI 不兼容变更按 MAJOR，source 8.0.0；写清 JSON/退出码迁移、能力缺失和回滚风险。
5. 确定性测试、完整回归、支持的 Python 矩阵及独立只读复审形成候选门禁。模型收益、M5、owner、签名发布和实际部署分别验收，不由源码 PASS 推导。

外部设计依据：Anthropic 的长期任务 harness 采用增量交接与独立评价；OpenAI agent evals 分离工作流和 trace 评价；SLSA 1.2 分离身份、来源和制品期望。只吸收边界与测试思路，未调用真实模型或引入额外默认 runtime。参考来源为 https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents 、https://www.anthropic.com/engineering/harness-design-long-running-apps 、https://developers.openai.com/api/docs/guides/agent-evals 、https://slsa.dev/spec/v1.2/verifying-artifacts 。
