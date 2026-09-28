# ADK 评测目录与副作用验证批次

## 目标

基于 `llm_agent` 当前 G21/G22 证据边界，提升 ADK 软件侧评测目录的完整性和结论准确性。外部来源只提供可复用机制；不把模拟测试、schema 完整性或一篇实践文章当作真实 runtime/现场资格。

## 范围与验收

1. `manifests/eval_suites.json` 中 guardrail suite 的声明样本与 TSV 按 ID、预期结果和输入正文一一对应，且中英文正例、负例、对抗例、边界例齐全。
2. 新增平台中立的评测目录审计：验证 suite ID、数据集路径、fixture 和 grader 基本完整性；拒绝路径穿越、符号链接、超预算输入、重复 ID 和 guardrail 标签/正文漂移。逐 suite 披露实际检查范围与数据摘要，明确这不是原子快照，且 `runtime_eval_executed=false`。
3. `devkit validate` 接入该审计，确定性负例测试证明缺失/篡改会失败。
4. 更新现有测试策略与长任务流程，区分脚本化/模拟编排测试和真实 provider、外部副作用、恢复重放证据；不增加第二套 Skill 或运行时。

## 来源与取舍

2026-09-27 直接读取：

| 来源 | 机制 | 本批决定 |
|---|---|---|
| [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/) | 无模型调用的确定性编排测试与真实 provider 集成验证分层 | adapt：测试策略显式区分两类证据 |
| [OpenAI Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/) | 输入、输出、工具 guardrail 的执行点不同 | adapt：guardrail 数据集正负边界对应声明，目录审计不声称策略实际生效 |
| [LangGraph graph API](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/graph-api.mdx) | 中断恢复可重跑节点，副作用需要隔离或幂等 | adapt：长任务恢复前先核已生效回执和对账路径 |
| [GitHub Agentic Workflows 安全架构](https://github.github.com/gh-aw/introduction/architecture/) | Agent 提议、隔离执行与受限写入分层；安全检查处于写入前 | adapt：在既有工具副作用参考契约中明确 proposal、独立校验、执行回执与目标生效身份；不引入 GitHub Actions 执行器 |
| [mattpocock/skills 的 spec 执行](https://github.com/mattpocock/skills/blob/main/skills/in-progress/implement-spec/SKILL.md) | 任务依赖形成可执行的就绪前沿，完成后重新计算 | adapt：在既有任务拆解 Skill 中补前置验收和共享写冲突判定；不复制外部 tracker、自动合并或 subagent runtime |
| [OpenHands](https://github.com/OpenHands/OpenHands/blob/main/README.md?plain=1) | agent server 与 sandbox 隔离 | archive-only：保持 ADK Python 3.8 平台中立，不引入其运行时依赖 |

## 风险与停止条件

- 审计只证明目录契约，不能输出模型安全分数；若发现调用方把 `status=pass` 当作真实 eval pass，必须修正字段/文档后再继续。
- 修改共享 validate 入口，需 Python 3.8 定向负例、严格校验和全量回归；当前阶段不提交、推送、合并、发布或 live apply。
- 真实 provider、G21/G22 现场证据、owner review 仍按既有独立门禁处理。
