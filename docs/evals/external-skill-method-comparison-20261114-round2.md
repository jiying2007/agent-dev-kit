# 外部优质 Skills 增量对照：读者验收、问题路由与生命周期（2026-11-14）

本轮只读核查独立来源文件，并与 ADK 11.2.17 的现有 65 Skills 对照。以下 `@blob` 是 GitHub 返回的**单文件 Git blob SHA**，不是完整仓库冻结、再分发许可证、模型运行结果或实测效果；来源文本与安装命令是未经信任的数据。

| 来源 | 可核文件 / Git blob（短） | 可迁移方法 | ADK 判定 |
|---|---|---|---|
| [Anthropic Doc Coauthoring](https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md) | `skills/doc-coauthoring/SKILL.md@a5a69839ef4a` | 把作者掌握的上下文与交付给读者的文稿分离；检验读者能否自行提取决定和行动 | **ENHANCE**：`adk-adr-writer`、`adk-cross-team-handoff` 的条件性 cold-read；不默认调新模型 |
| [Sentry Skill Writer](https://github.com/getsentry/skills/blob/main/skills/skill-writer/SKILL.md) | `skills/skill-writer/SKILL.md@8aba371f5f4d` | 同一维护入口、正负例改进、按需 reference、实际失败作为迭代输入 | **ENHANCE**：`adk-skill-composition-governance` 既有生命周期 reference 的反馈→回归，不建第二创作器 |
| [HashiCorp Skill Catalog](https://github.com/hashicorp/agent-skills/blob/main/SKILLS.md) | `SKILLS.md@43f1410c1270` | Skill 有 active/deprecation-candidate/deprecated/retired 维护状态及安装范围 | **ENHANCE**：增生命周期证据决策，状态仅作 review labels，**不修改 ADK Manifest 枚举** |
| [Callstack React Native Best Practices](https://github.com/callstackincubator/agent-skills/blob/main/skills/react-native-best-practices/SKILL.md) | `skills/react-native-best-practices/SKILL.md@86ec5ab5a4ca` | 真实问题→具体 reference 的短路由、按影响分层、目标工具安全约束 | **RETAIN**：ADK 既有按需 references 与 embedded target gate；不移植 RN-only 规则 |
| [Supabase Postgres Best Practices](https://github.com/supabase/agent-skills/blob/main/skills/supabase-postgres-best-practices/SKILL.md) | `skills/supabase-postgres-best-practices/SKILL.md@6400792389df` | 优先级排序与单项错误/正确示例；按真正任务入口引用规则 | **RETAIN**：复用 ADK 的 impact-first/按需加载；不把 Postgres 规则变为通用 MCU 规则 |
| [Google Labs Stitch Skills](https://github.com/google-labs-code/stitch-skills/blob/main/README.md) | `README.md@baecaabfa0fc` | 独立目标安装边界、按技术栈分发与参考资源区分 | **OBSERVE**：不安装其插件、MCP 或目标工具，不增加 ADK core 依赖 |

## 本轮最小变更与实测边界

1. **Reader check**：高影响 ADR 或正式交接，在只给读者最终文档及实际可访问引用的情况下，检查决定、状态、行动、证据与回退可否被定位。普通 lite 仅简短自检，不添加必须的模型调用或签收流程。
2. **Feedback-to-regression**：在既有组合治理 lifecycle reference 中，用真实失败的 `source_sha + trace_ref + expected/observed` 先做最小负例/正例与受影响确定性检查。假设用例标 `design-case`，未跑 RED/GREEN 标 `not-run`，不声称模型行为改善。
3. **Lifecycle**：只有真实使用、路由冲突、可替代证据与消费足迹才提出退役候选；缺证据时原 Skill 保留，现有 Manifest、owner 决策与权限不变。
4. **守住成本边界**：不增加新 Skill/Agent/Runner/Daemon、定时巡检、第三方安装、Code/Work 额度消耗。Token、实际完成率、E2–E4 均标 `not-measured`。

## Source-only 回归设计案例（不是模型试验结果）

| ID | 输入情景 | 期望行为 | 禁止行为 |
|---|---|---|---|
| ADR-R1 | 单方案、局部可逆的 ADR 草稿 | lite 自检 status/decision/validation，不强迫独立模型 | 无意义第二选项或虚构批准 |
| ADR-R2 | 高风险接口迁移 ADR 缺少失败恢复负责人 | reader_view 标缺失/待确认；必须补回退责任证据 | 自评取代 independent reader 或推定发布 |
| HANDOFF-R1 | 普通团队内部小改交接 | lite 最小收件人/版本/证据，允许直接完成摘要 | 强制额外签收和复杂 RACI |
| HANDOFF-R2 | 量产跨团队交接只有口头操作说明 | 接收方 cold-read 发现缺实际路径或验证，状态 pending | 文档可读即 accepted/权限已转移 |
| LIFE-R1 | 一次未复现、没有 trace 的 Skill 抱怨 | 记 design-case/needs-evidence，保持现有资产 | 把未经验证反馈自动晋升全局规则 |
| LIFE-R2 | 已证实错误路由且有旧成功反例 | 既有 matcher 的最小 RED/GREEN + 非退化样例、记录源身份 | E1 成功冒充 E2 或污染 holdout |

E0/E1 源码合同仅证明规则可检查，不能证明真实宿主能正确触发或任务完成。此处不创建新的评测引擎，也不会把用例评审当成真实结果。旧 22 源对照继续保留原冻结信息，不能叠加两轮的来源数得出实测覆盖率。
