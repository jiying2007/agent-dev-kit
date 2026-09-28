# 设计与来源取舍

2026-09-28 直接读取 [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/)：确定性测试只覆盖本地/SDK 拥有的编排行为，外部 provider 行为需独立集成验证。[OpenSpec v1.13.2](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.13.2) 修正了跳过检查被当作通过的报告问题。两者用于校准结果披露，不导入运行时或外部代码。

| 来源机制 | 本地决定 | 边界 |
|---|---|---|
| 确定性测试披露受测行为 | adapt：给路由报告增加 `evaluation_scope`、`route_accuracy`、`safety_evaluated`、`safety_accuracy` | 不声称模型或安全策略验证 |
| 跳过检查不能默认为通过 | adapt：逐用例 `actual_safe=null`、`safety_evaluated=false` | 路由 `status` 仍只代表 Skill 匹配 |
| [OpenAI Plugin Eval](https://github.com/openai/plugins/tree/main/plugins/plugin-eval) 的聊天入口与本地 CLI 分层 | observe：ADK 已有 CLI、目录审计和体积报告 | 不引入 Node.js CLI、plugin runtime 或新的评分器 |
| [Langfuse 版本化数据集](https://github.com/langfuse/langfuse-docs/blob/main/content/docs/evaluation/experiments/datasets.mdx) | adapt：报告绑定 `manifest_sha256` 和 `task_set_sha256`，支持同一任务集结果对照 | 摘要来自解析后的有序任务序列，不是原始 JSONL 字节；`source_snapshot_atomic=false`，不引入平台服务 |
| [OpenSpec v1.13.2](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.13.2) 的验证范围修复 | adapt：既有完成验证 reference 补新增、修改、删除、重命名需求的核对规则，以及 skipped 不计通过 | 不导入 OpenSpec CLI 或新状态机 |

新增字段为报告附加信息，不改变现有评分计算或 schema version；调用方若要判定安全，必须消费另一个实际执行安全判定的报告。回滚只需撤销字段和文档，没有状态迁移。

完成验证 reference 增加 457 UTF-8 字节，七个包含该 Skill 的 profile 的潜在完整源码各增加 457 字节；入口文件大小和 `incident-response` 不变。`profile_context_ratchets.json` 按当前源码实测更新。这是源码体积审查，不是实际提供商 token 或运行时初始上下文测量。
