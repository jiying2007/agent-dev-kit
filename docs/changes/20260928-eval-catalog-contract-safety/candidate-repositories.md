# 新评测参考候选（2026-09-28，只读）

| 来源 | 直接证据与适用点 | 本地决定 | 后续门禁 |
|---|---|---|---|
| [Pydantic Evals](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/README.md) | Pydantic AI monorepo 中的 case/dataset/evaluator 包；MIT；宿主项目 Python ≥3.10；类型化序列化与自定义 evaluator 适合方法对照 | `adapt-method-only`：静态目录使用封闭 grader/fixture 字段，未导入包 | exact commit、单项许可/依赖、Python 3.8 可迁移性、测试和 owner 决定待审 |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | UK AI Security Institute 的 MIT 评测框架；Python ≥3.10；[SECURITY.md](https://github.com/UKGovernmentBEIS/inspect_ai/blob/main/SECURITY.md)把评测任务/日志的代码执行与密钥泄露列为风险面 | `observe`：参考其“不可信评测工件需安全边界”的审查方法；ADK 不运行外部任务或日志 viewer | exact commit、安全公告、沙箱/日志权限及运行依赖另审 |
| [OpenAI Plugin Eval](https://github.com/openai/plugins/blob/main/plugins/plugin-eval/README.md) | 官方 Codex plugin + 本地 CLI，区分静态分析、测量计划与真实 benchmark；Node.js ≥20、私有包 | `observe`：ADK 已有 Python 3.8 eval/catalog/footprint，保持方法对照 | exact commit、插件 manifest/许可、外部运行及 source-to-live 另审 |

本表是 review-required candidate，不是 `llm_agent` registry/adoption decision、ADK runtime profile、软件效果分数或产品放行。未克隆、安装或运行上述仓库代码。
