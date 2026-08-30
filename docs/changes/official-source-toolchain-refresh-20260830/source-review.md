# 2026-08-30 OpenAI 官方来源复核

## 证据方法与边界

- Codex：当日运行 Codex manual helper，返回 `Manual status: local manual was updated`；
  缓存只在 ignored `.cache/openai-docs`，不归档整份外部正文。
- API/Cookbook：尝试配置 `openaiDeveloperDocs` MCP；当前会话无法热加载后，
  按技能回退策略直接打开每个 `developers.openai.com` URL，28/28 均可解析。
- Codex canonical URL 中 5 条当前重定向到 OpenAI 维护的 ChatGPT Learn 页面；
  inventory 仍保留原 canonical URL，且 ADK 只采纳平台中立治理模式。
- Cookbook 与 partner 内容是参考样例，不是产品保证、兼容承诺或默认启用授权。
- retrieved/review：`2026-08-30`；expires：`2026-11-28`；窗口 90 天。

## 逐条复核结果

| Source ID | Review | 结果 |
|---|---|---|
| openai-structured-model-outputs | adopted | unchanged：strict schema、拒绝和 parse-failure 边界仍成立 |
| openai-function-calling-strict | adopted | unchanged：strict tool schema 与 call/output correlation 仍成立 |
| openai-tool-search | adopted | unchanged：延迟加载和 namespace summary 仍成立 |
| openai-file-search-retrieval | watch | watch-retained：只作检索设计参考，不默认启用 hosted file search |
| openai-codex-app-automations | adopted | unchanged-with-redirect：定时任务、sandbox 和 review gate 仍成立 |
| openai-codex-app-worktrees | adopted | unchanged-with-redirect：隔离、handoff 和清理边界仍成立 |
| openai-agent-improvement-loop | adopted | unchanged：trace/eval/repair 改进环仍成立 |
| openai-codex-github-action | adopted | unchanged-with-redirect：CI runner、secret 与 sandbox 边界仍成立 |
| openai-codex-code-review-sdk | adopted | unchanged：结构化 review 与 inline anchor 校验仍成立 |
| openai-skills-api-operational-practices | adopted | unchanged：版本锁定、确定性输出和网络 allowlist 仍成立 |
| openai-optimizing-llm-accuracy | watch | watch-retained：复杂优化仍要求先有 eval baseline |
| openai-codex-agents-sdk-multi-agent-workflows | watch | decision-updated：`codex mcp-server` 已 deprecated；新适配优先 App Server，旧示例仅 legacy reference |
| openai-prompt-caching | adopted | unchanged：稳定前缀、动态尾部和 cache observability 仍成立 |
| openai-agents-orchestration-handoffs | adopted | unchanged：handoff 与 manager-owned agent-as-tool 区分仍成立 |
| openai-graders | adopted | unchanged：grader taxonomy 仍成立 |
| openai-prompt-optimization-golden-examples | adopted | unchanged：正负 golden examples 先于 prompt promotion 仍成立 |
| openai-codex-iterative-repair-loop | adopted | unchanged：Review -> Repair -> Validate 闭环仍成立 |
| openai-model-optimization-workflow | adopted | unchanged：eval-baseline-first 优化顺序仍成立 |
| openai-prompt-engineering-roles | adopted | unchanged：developer/user/context authority 边界仍成立 |
| openai-prompt-engineering-formatting | adopted | unchanged：稳定 section 与动态 context 分离仍成立 |
| openai-stored-completion-monitoring | watch | watch-retained：需 retention、redaction 与 owner approval 后才可启用 |
| openai-agentic-governance-test-dataset | adopted | unchanged：正负、对抗、边界数据集仍成立 |
| openai-eval-driven-system-design | adopted | unchanged：改进阶梯与 eval/training 数据分离仍成立 |
| openai-model-selection-guide | adopted | unchanged：KPI/SLO、成本、时延、A/B 与回滚记录仍成立 |
| openai-ai-native-engineering-team-docs | adopted | unchanged-with-redirect：fresh docs/diagram/release summary 仍可作交付模式 |
| openai-data-controls-responses | adopted | unchanged：retention、ZDR 与 hosted tool 边界仍成立 |
| openai-responses-migration-statefulness | adopted | unchanged：statefulness、encrypted reasoning 与 call_id 边界仍成立 |
| openai-prompt-cache-retention | adopted | unchanged：retention 选项和 cache-miss-safe 布局仍成立 |

