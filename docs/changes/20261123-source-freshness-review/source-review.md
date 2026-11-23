# 2026-11-23 来源逐条复核

回读现行发布者页面或固定 Git 对象，摘录限于可核验结论。原方法采纳保留，变化项注明新边界。复核日期按治理时区 Asia/Hong_Kong 记录。

| 来源 ID | 复核发现和裁决 | 有效至 |
| --- | --- | --- |
| openai-codex-customization-skills | Skill 元数据先发现、选中后加载正文，团队分发使用 plugin。AGENTS.md 单列为仓库指令，优先级采用专门文档。 [发布者证据](https://learn.chatgpt.com/docs/customization/overview#skills) | 2027-01-22 |
| openai-agents-sdk-starting-point | 起点表按 hosted Agents API、应用内 Agents SDK、直接 Responses API 和 ChatKit 区分。只用于分类，保持本地编排。 [发布者证据](https://developers.openai.com/api/docs/guides/agents#choose-your-starting-point) | 2027-02-21 |
| openai-agents-tracing | Tracing 章节列明工具、交接、护栏和 span，观测表将 traces 用于调试，完成后再定评分。 [发布者证据](https://developers.openai.com/api/docs/guides/agents/integrations-observability#tracing) | 2027-02-21 |
| openai-agent-evals | 评估工作流的 trace grading 验证路由、工具调用和规则遵循，数据集和评分器做可重复回归。 [发布者证据](https://developers.openai.com/api/docs/guides/agent-evals) | 2027-02-21 |
| openai-reasoning-models | 旧 latest-model 页面已移动到 GPT-6.2。独立检查前缀指南、Compaction 和 Structured Outputs，保留真实支持的缓存、压缩和结构化输出。移除该条对 tool preambles 的归属。 [发布者证据](https://developers.openai.com/api/docs/guides/keep-prefix-unchanged) | 2027-01-07 |
| openai-apps-sdk-review-tool-hints | 提交页已迁移。Plugin Reference 定义三项注解，Plugin guidelines 单列工具使用和隐私。注解用于风险审计，实际授权由本地策略处理。 [发布者证据](https://developers.openai.com/plugins/reference#annotations) | 2027-01-07 |
| openai-codex-requirements-toml | 配置参考对本地、企业设备和 Work cloud 给出不同作用域和优先级。Security Cookbook 核对 MCP 身份、deny-read 和保守 prefix rule。 [发布者证据](https://learn.chatgpt.com/docs/config-file/config-reference#requirementstoml) | 2027-01-07 |
| openai-codex-sandbox-defaults | 桌面和 CLI 的 workspace-write 与审批分开配置，Full access 风险独立，云端权限入口不同。 [发布者证据](https://learn.chatgpt.com/docs/sandboxing) | 2027-01-22 |
| openai-codex-rules | 规则定义支持 match/not_match 内联样例，重叠选择最严决策，管理员可下发限制规则。 [发布者证据](https://learn.chatgpt.com/docs/agent-configuration/rules) | 2027-01-22 |
| openai-codex-agent-approvals-security-dangerous-settings | 危险选项分别扩大非 loopback 代理监听和 Unix socket 白名单边界，网络模式与自动审查另有约束。 [发布者证据](https://learn.chatgpt.com/docs/agent-approvals-security#dangerous-settings) | 2027-01-07 |
| openai-codex-mcp-options | MCP 配置含 startup/tool timeout、required、工具过滤与审批。OAuth scopes 改用 scopes，空列表仍可由库决定，回调字段按配置参考。 [发布者证据](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) | 2027-01-07 |
| openai-codex-app-server-api-overview | API 文档标明 thread/shellCommand 与实验版 process/spawn 不继承 sandbox，文件、配置和插件操作按各方法归类。 [发布者证据](https://learn.chatgpt.com/docs/app-server) | 2027-01-07 |
| openai-context-engineering-session-memory | Cookbook 比较 trimming 与 summarization，示例围绕当前 issue、压缩交接摘要和恢复。ADK 保留本地契约及证据门禁。 [发布者证据](https://developers.openai.com/cookbook/examples/agents_sdk/session_memory#why-context-management-matters) | 2027-02-21 |
| openai-docs-mcp-quickstart | Quickstart 保留 Codex、VS Code、Cursor 和 Claude Code 的 Docs MCP 配置、验证方式和指令提示。保留只读可选依赖与精确镜像字段。 [发布者证据](https://developers.openai.com/learn/docs-mcp#quickstart) | 2027-01-22 |
| openai-responses-migration | 迁移文档继续支持 Responses 作为新 API 路径，既有 Chat Completions 仍受支持。保留待本地试点的观察状态。 [发布者证据](https://developers.openai.com/api/docs/guides/migrate-to-responses) | 2027-01-22 |
| openai-codex-hooks | 非受管 hook 按定义 hash 信任，修改后需要重审，受管 hook 的来源和信任单独记录。 [发布者证据](https://learn.chatgpt.com/docs/hooks) | 2027-01-07 |
| openai-codex-hooks-common-output-fields | 共同字段和 hookSpecificOutput 的适用事件明确列出，SubagentStart 的 continue 语义不同。保留事件级校验。 [发布者证据](https://learn.chatgpt.com/docs/hooks#common-output-fields) | 2027-01-07 |
| openai-codex-slash-commands | 命令参考包含 /compact、/approve 等行为和配置条件。观察按实际宿主执行结果记录。 [发布者证据](https://learn.chatgpt.com/docs/developer-commands?surface=cli) | 2027-01-07 |
| openai-codex-as-mcp-server | 官方移除 Codex 作为 MCP server。App Server 使用独立 JSON-RPC，官方标为实验，现有本地平台中立 run/reply 合约仅保留方法。 [发布者证据](https://learn.chatgpt.com/docs/mcp-server) | 2026-12-23 |
| openai-codex-plugin-build | 插件打包定义兼容 manifest、应用映射和 skills 目录。保留未来候选方法，现有运行开关照旧。 [发布者证据](https://developers.openai.com/plugins/build/plugins) | 2027-01-22 |
| openai-codex-plugin-marketplace | 本地 marketplace 路径必须在根内，条目显式声明 installation、authentication、category。 [发布者证据](https://developers.openai.com/plugins/build/plugins) | 2027-01-22 |
| openai-codex-best-practices | 官方指南保留明确任务上下文、验证、项目指令、可复用 Skill 和成熟工作流自动化。 [发布者证据](https://learn.chatgpt.com/guides/best-practices) | 2027-01-22 |
| openai-codex-agent-skills | 名称和描述决定发现，所需的脚本和资源按需载入，Skill 文件夹可作为插件分发。 [发布者证据](https://learn.chatgpt.com/docs/build-skills) | 2027-01-22 |
| openai-tools-guide | 工具指南继续给出 tools 的放置、工具种类和 tool_choice。维持本地显式启用策略。 [发布者证据](https://developers.openai.com/api/docs/guides/tools) | 2027-02-21 |
| openai-chatgpt-developer-mode | 旧 Developer mode URL 转向自定义 MCP，现行文档保留工具消歧、输入输出 JSON 审阅和写确认。描述质量引用插件指南。 [发布者证据](https://developers.openai.com/api/docs/guides/custom-mcp-server) | 2027-01-07 |
| openai-mcp-chatgpt-api-integrations | MCP 文档示例核对 search/fetch、structuredContent 和 OAuth。提示注入治理引用本地规则与工具审查，保持 data-only 约束。 [发布者证据](https://developers.openai.com/api/docs/mcp) | 2027-01-22 |
| openai-agentic-macro-evals | 示例以合成轨迹与已保存的低层评分聚合模式，建议提升高信号失败为回归。保持方法采纳范围。 [发布者证据](https://developers.openai.com/cookbook/examples/partners/macro_evals_for_agentic_systems/macro_evals_for_agentic_systems) | 2027-02-21 |

| 来源 ID | 复核发现和裁决 | 有效至 |
| --- | --- | --- |
| github-gh-aw-safe-outputs | Reviewed safe-outputs.md at 1d9b4b43897d2d462e12360dd0bcdedafbe1ba5e confirmed structured requests, separate permission-controlled jobs, optional external authorization, and the default create-issue with explicit opt-out. Adopt only request/execution separation and validation. No workflows or writes are enabled by this reference. [固定证据](https://github.com/github/gh-aw/blob/1d9b4b43897d2d462e12360dd0bcdedafbe1ba5e/docs/src/content/docs/reference/safe-outputs.md) | 2026-12-23 |
| mcp-registry | Reviewed README and LICENSE at c6f2f61431b4e24bcdd9225f6f7bcb47da3688d6 confirmed preview status, verified namespaces, and Apache-2.0, unrelicensed MIT and non-spec documentation CC-BY-4.0 boundaries. A listing or verified publisher supplies metadata for a separate trust decision. [固定证据](https://github.com/modelcontextprotocol/registry/tree/c6f2f61431b4e24bcdd9225f6f7bcb47da3688d6) | 2026-12-23 |
| otel-genai-semconv | Reviewed README at ae8214a8f3a98786071736855093b74621174dc4 found the Schema URL still TODO. Keep the disabled adapter at cc07f722069974139dab497d80d145144b19daca and sensitive capture disabled. The observation records a newer upstream revision without changing the adapter pin. [固定证据](https://github.com/open-telemetry/semantic-conventions-genai/blob/ae8214a8f3a98786071736855093b74621174dc4/README.md) | 2026-12-23 |
| owasp-agentic-skills-top10-2026 | Reviewed README, risk taxonomy and LICENSE.md at d6f7d7d0de314f52a83a85d1828e06ab096e595c confirmed AST04 parsing, AST05 external instructions and CC-BY-SA-4.0. Keep the crosswalk observe-only. No prose, format, whitepaper findings or compliance claims are imported. [固定证据](https://github.com/OWASP/www-project-agentic-skills-top-10/tree/d6f7d7d0de314f52a83a85d1828e06ab096e595c) | 2026-12-23 |
| agent-skills-in-the-wild-2026 | Reviewed arXiv:2607.00911v2 confirmed the study's cohort, mostly one-time reuse, project-specific operational adaptation and relatively stable behavioral constraints. Adopt the maintenance distinction as a method. Local effectiveness, dataset reuse, and paper or code redistribution require separate evidence. [固定证据](https://arxiv.org/html/2607.00911v2) | 2027-01-22 |
| vscode-agent-skills-2026 | Reviewed published docs and vscode-docs b9040dd0042aaa8062407f56f87ad9aac07e5c35 confirmed harness-specific discovery and explicit invocation testing. The deprecated chat.agentSkillsLocations applies to Local sessions, and editor forwarding does not apply to independent harness clients. Publisher documentation schedules Local harness removal for February 2027. Keep observe-method-only. [固定证据](https://github.com/microsoft/vscode-docs/blob/b9040dd0042aaa8062407f56f87ad9aac07e5c35/docs/agent-customization/agent-skills.md) | 2026-12-23 |

补充证据包括 [AGENTS.md 优先级](https://learn.chatgpt.com/docs/agent-configuration/agents-md)、[Compaction](https://developers.openai.com/api/docs/guides/compaction)、[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)、[插件隐私和工具设计](https://developers.openai.com/plugins/plugin-guidelines)、[Codex Security Cookbook](https://learn.chatgpt.com/docs/enterprise/security-cookbook)。

关联条目 `openai-codex-agents-sdk-multi-agent-workflows` 尚未到期。独立复审发现其退役状态和文档索引与现行证据不一致，已一起同步，继续保持 `watch`。此项另计于 33 条到期记录。 [官方撤除说明](https://learn.chatgpt.com/docs/mcp-server)
