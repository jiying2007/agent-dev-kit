# 工具副作用与评测数据集闭环

## 目标与边界

- 目标：把有副作用的工具和 handoff 设计成可审查的授权、重试与回执契约；修复评测清单指向不存在的 guardrail 数据集。
- 范围：`adk-interface-contract-design`、其参考契约、评测 fixture 和治理测试。平台中立；不增加运行时依赖、外部服务、MCP 或 profile。
- 风险：文档约束过严可能误伤只读工具；因此只对有外部副作用的调用要求完整矩阵。数据集只作治理样本，不冒充真实模型的 guardrail 性能。
- 验收：严格校验、Skill 治理测试、完整 ADK 回归通过；所有 `eval_suites.json` 的 `dataset_path` 存在；除 source version 外不改变 manifest 的运行时资产声明，不触及 Codex live。
- 版本：PR 的 source-version gate 要求相对 `main` 前进；按仓库 `versioning sync-identity` 将 7.12.1 升至 7.12.2，所有投影同步，不在本 change 内声明产品发布。

## 来源与取舍

检索时间：2026-09-27。下列链接均为直接阅读的上游文档，作为机制证据而非 ADK 运行依赖。

| 来源 | 可复用机制 | 决定 |
|---|---|---|
| [OpenAI Agents SDK guardrails](https://openai.github.io/openai-agents-python/guardrails/) | 首个 agent 的输入 guardrail 与每次函数工具调用的 tool guardrail 生效点不同；handoff 需要单独检查 | adapt：在接口契约中明确授权时点和 handoff 边界 |
| [OpenAI Agents SDK HITL](https://openai.github.io/openai-agents-python/human_in_the_loop/) | 副作用工具可在执行前暂停审批；恢复状态须由可信服务端持有、校验 owner 与并发消费 | adapt：记录参数/目标身份绑定、拒绝和恢复语义 |
| [LangGraph graph API](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/graph-api.mdx) | 恢复会重新执行受影响节点，暂停前副作用需要幂等或隔离 | adapt：要求 op-id、回执、对账，不承诺 exactly-once |
| [OpenHands 项目](https://github.com/OpenHands/OpenHands/blob/main/README.md?plain=1) 与 [sandbox-server](https://github.com/OpenHands/sandbox-server/blob/main/README.md) | 将 agent server 与 sandbox 控制面分开；独立 server 的开发要求 Python 3.12/3.13 | archive-only：可参考隔离边界，但不引入其运行时或依赖，保持 ADK Python 3.8 原生能力 |
| OpenAI Agents SDK / LangGraph runtime | 运行时 SDK、托管 trace、session、graph | reject：ADK 只吸收平台中立契约，不引入第二运行时 |

## 非目标

- 不声称现有 ADK 自动实现审批、幂等或持久化；这些由具体消费者在集成层完成并取证。
- 不把本数据集当成模型安全测评分数；它是 schema 与治理样本完整性检查。
