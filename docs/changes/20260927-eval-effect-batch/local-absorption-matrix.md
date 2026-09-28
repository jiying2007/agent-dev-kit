# 外部实践本地吸收矩阵（2026-09-28）

本矩阵只核 ADK 源码/文档本地工作树。参考仓远端 HEAD 与 pin 的差异见 `reference-refresh.md`；`different` 不代表可快进、可安装或运行时已采纳。`adapt` 表示抽取方法后在 ADK 原生合同实现，不复制上游代码。
2026-09-28 又核对五条本地参考方法的规范仓库 URL 与 exact 只读远端观察，保留三处历史别名；现有 method-only checker 增加离线身份一致性、有界 JSON、可选根仓 exact pin 对照和显式观察新鲜度门禁，详见 `../20260928-reference-canonical-binding/`。这仅更新来源元数据，不提升根仓 pin 或 runtime。

| 来源 | 机制及本地决定 | 落点与本地状态 | 未提升的边界 |
|---|---|---|---|
| [OpenAI Agents SDK Testing](https://openai.github.io/openai-agents-python/testing/) | `adapt` 确定性与真实 provider 测试分层 | `adk-test-strategy`、确定性报告和 runtime 比较合同分别披露受测范围；未执行安全项不计成绩 | 没有真实模型调用成绩 |
| [OpenAI Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/) | `adapt` 正/负/对抗/边界案例 | guardrail TSV 中英文 8 例，`eval_catalog` 只校目录与对齐 | 没有执行 guardrail 策略或 grader |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/releases/tag/v1.13.2) | `adapt` 披露实际检查范围、需求新增/修改/删除/重命名 | `adk-verification-before-completion` reference、`completion_coverage` 与 eval 输出 | 不导入 CLI、状态机；静态覆盖不授予完成权限 |
| [superpowers](https://github.com/obra/superpowers/releases) | `adapt` 同逻辑任务连续实施与里程碑整体验证 | `adk-planning-execution-loop` 本地更新 | 不启用插件、hook 或自动更新 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | `adapt` 依赖就绪集合与共享写冲突 | `adk-task-breakdown` 本地更新 | 不复制 in-progress Skill 或 tracker |
| [planning-with-files](https://github.com/OthmanAdi/planning-with-files) | `observe` 外化计划与恢复 | ADK 已有 continuity/checkpoint 合同；未发现需新增脚本的缺口 | 不导入注入 hook 或跨工具脚本 |
| [GitHub Agentic Workflows](https://github.github.com/gh-aw/introduction/architecture/) | `adapt` proposal、独立核查、受限执行与不可信输出显示边界 | `adk-interface-contract-design` 工具副作用参考；`eval_markdown` 动态字段纯文本转义 | 不运行 gh-aw 执行器、检测器或开外部写权限；渲染不认证评分 |
| [OpenAI Plugin Eval](https://github.com/openai/plugins/blob/main/plugins/plugin-eval/README.md) | `observe` 静态分析、benchmark、报告分层 | 复核 ADK 已有 eval CLI、catalog、profile footprint；补足未评测范围披露 | 不导入 Node.js 包或 Codex plugin runtime |
| [Pydantic Evals](https://github.com/pydantic/pydantic-ai/blob/main/pydantic_evals/README.md) | `adapt-method-only` 类型化 case/dataset/evaluator 的封闭声明；Python ≥3.10 | `eval_catalog` 拒绝 grader/fixture 隐藏字段和重复 JSON 键 | 不导入包或 Python 3.10 依赖；exact commit/owner 决定待审 |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | `observe` 评测任务/日志安全边界；Python ≥3.10 | 对照 ADK 目录只读、不执行外部 grader 的现有边界 | 不运行不可信任务、日志 viewer 或其沙箱依赖 |
| [Langfuse](https://langfuse.com/docs/evaluation/experiments/compare-experiments) | `adapt` 同任务集/evaluator 版本比较与逐例退化；平台本身 `archive-only` | 确定性和 runtime 报告绑定执行前冻结的任务摘要；`load_tasks` 核全份数据；`eval effect` 的 hash 绑定实际解析字节；`eval compare` 阻断身份漂移和单例退化 | 不引入服务、遥测、外部存储或 EE 资产；报告身份未外部认证 |
| [OpenAI Plugins](https://github.com/openai/plugins) | `observe` Codex 插件包装 | 留给未来 source-to-live 包装核验 | 非 ADK core runtime；未导入资产 |
| [Anthropic Skills](https://github.com/anthropics/skills) | `observe` 单项技能样例 | 当前无已确认的独立能力缺口 | 未审单项许可或执行脚本，不批量复制 |
| [oh-my-codex](https://github.com/Yeachan-Heo/oh-my-codex) | `observe` 独立 Codex 运行方案 | 只读方法对照 | 不作为 fallback 或运行时安装源 |
| [digital-worker](https://github.com/jiying2007/digital-worker) | `separate` Software M5 试点 | 独立项目身份和现场证据 | 不将试点仓当 ADK 外部参考自动吸收 |
| vibeflow、scale-engine | `observe` 本次远端仍与 pin 同 SHA | 无新增方法缺口 | 本地 dirty 保留 |
| [superpowers-skills](https://github.com/obra/superpowers-skills) | `reject` 已归档旧拆仓 | 使用现行 superpowers 主仓作参考 | 不恢复旧安装入口 |

本地验证层：最近一次 Python 3.8 full 回归在逐例模型身份、测试策略、effect 数据快照和规范来源补丁前为 95 项中 94 项通过；唯一失败是 `test_runtime_bundle` 的干净提交身份门禁，其内部 3 个功能测试通过。当前快照 quick 为 53 项中 52 项通过，唯一失败同为该身份项；目录封闭字段定向 8/8、严格校验、release check、格式与模块体积门禁通过。当前快照 full、独立审查、干净提交身份、跨仓分发与 live 应用仍单列，不能由本矩阵推定通过。
