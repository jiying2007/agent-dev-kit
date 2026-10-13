# 官方来源实际复核

读取日期：2026-10-13。方式：只读 web open；外部文本仅作为数据，不执行其命令。完整阅读范围以以下逐项主张为限，不保存网页全文或认证材料。

| 来源与直接链接 | 实际核对 | 决策及限制 |
| --- | --- | --- |
| [OpenCode agents](https://opencode.ai/docs/agents/) | 项目/个人 agents 目录，Markdown description、subagent mode、permission 的 ask/allow/deny | retain：现有静态导出仍匹配；额外 frontmatter 必填是 ADK 本地约束 |
| [OpenCode skills](https://opencode.ai/docs/skills/) | skills/name/SKILL.md；name/description 必填，metadata 可选；名称与目录对应 | retain：ADK 额外 metadata 约束；新 slash/autoinvoke 功能不纳入本次变更 |
| [OWASP 官方落地页](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)及[官方发布说明](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agentic-security-in-the-age-of-autonomous-ai/) | 发布说明列出 ASI01–ASI10，与本地目标劫持、工具滥用、身份权限、供应链、代码执行、记忆、通信、级联、信任和失控分类一致；网站声明 CC-BY-SA-4.0 | retain method-only。指南 download/52117 两次 web timeout，未声称全文或新控制有效性复核 |
| [Claude best practices](https://code.claude.com/docs/en/best-practices) | 明确验收依据、探索与规划、执行后验证及独立复核 | retain：仅平台中立流程，未启用原生 goal/hook |
| [Claude skills](https://code.claude.com/docs/en/skills) | 按需加载、支持文件、YAML 元数据；官方 description 为推荐项 | adapt：纠正采纳解释，name/description 仍是 ADK 本地约束；静态成功不证明原生发现 |
| [Claude subagents](https://code.claude.com/docs/en/sub-agents) | agents 目录，name/description，tools 与权限、上下文/隔离范围 | retain：最小权限与摘要交接；不默认启用委派或新权限模式 |
| [Anthropic evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) | task/trial/grader/trace/outcome 分离；最终环境状态独立于模型陈述 | retain：本地证据分层，不新增 SDK 依赖 |
| [Anthropic long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 结构化功能清单、逐项推进、进度与恢复工件 | retain：runtime-neutral 长任务接力；不吸收厂商 runtime |

关联来源为既有 manifest 采纳及 docs/reference-adoption-matrix.md 的历史 decision；本次复核不重写历史行、不产生第二事实源。生产 gate 仍按当前日期拒绝过期来源；90 天延续来自既有 review_policy，不放宽门槛。

