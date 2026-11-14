# 外部独立 Skills / 参考仓库方法深度对照（2026-11-14）

本文件逐条记录**已读取的实际文件身份**（Git blob SHA）、可迁移方法、ADK 已有能力及本轮决策。Blob 是单文件内容标识，**不等同于冻结完整仓库 commit、许可证审查或执行安全认证**。只读引用不授权复制外部源码、安装依赖、运行 hooks/MCP 或触发网络写入。

## 方法决策
- `ENHANCE`：确有 ADK 既有能力的具体缺口，只补现有 Skill/reference/测试；不创建新的平行治理器。
- `RETAIN`：ADK 已有对应路径（例如 Review、Debug、TDD、Zephyr 目标 gate），本轮不增加重复层。
- `OBSERVE`：平台不适用或缺乏实际可核 Skill 代码，本轮不引入。
- 真实模型行为、真实安全发现率、Token/缓存收益、延迟、用户任务完成率仍全部 `not-measured`。只有 source-contract 和确定性测试可由 CI 验证。

| 来源 | 已核文件与 blob | 方法要点 | ADK 决策 |
|---|---|---|---|
| [OpenAI Skill Creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) | `openai/skills/skills/.system/skill-creator/SKILL.md@72bc0b97e7a6` | 精简入口、按任务脆弱度调整自由度 | RETAIN：既有 progressive disclosure / typed contract |
| [Anthropic Skill Creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | `anthropics/skills/skills/skill-creator/SKILL.md@65b3a402dbd0` | 训练/留出集、真实触发率、重复对照 | ENHANCE：现有 skill-behavior-evaluation + 已冻结预注册分组 |
| [Microsoft Waza](https://github.com/microsoft/waza/blob/main/README.md) | `microsoft/waza/README.md@0fa966655f37` | 可复现任务、评分器、环境证据 | RETAIN：复用 effect_trials / raw trace，不建第二评测器 |
| [Microsoft Skills](https://github.com/microsoft/skills/blob/main/README.md) | `microsoft/skills/README.md@c6705f4eec81` | 领域能力与测试门禁分离 | RETAIN：Manifest Profiles / contract / deterministic test |
| [Sentry Prompt Optimizer](https://github.com/getsentry/skills/blob/main/skills/prompt-optimizer/SKILL.md) | `getsentry/skills/skills/prompt-optimizer/SKILL.md@b8132d287dbb` | 任务成功标准、模型/上下文来源精确记录 | ENHANCE：预注册同模型/工具基线和成本字段 |
| [Sentry Security Model](https://github.com/getsentry/skills/blob/main/skills/security-model/SKILL.md) | `getsentry/skills/skills/security-model/SKILL.md@a1cc5a33ac40` | 版本化信任边界与安全不变量 | ENHANCE：来源审查引用现有可信模型，不额外建政策文件 |
| [Sentry Skill Scanner](https://github.com/getsentry/skills/blob/main/skills/skill-scanner/SKILL.md) | `getsentry/skills/skills/skill-scanner/SKILL.md@c4faa021ceb7` | 脚本、注入、权限、依赖以及误报证据 | ENHANCE：审查 covered/omitted/unavailable 和 finding truth |
| [Cloudflare Security Audit](https://github.com/cloudflare/security-audit-skill/blob/main/skills/security-audit/SKILL.md) | `cloudflare/security-audit-skill/skills/security-audit/SKILL.md@92178dad304d` | 轻量咨询/full audit 分流与边界证据 | RETAIN：既有 Review Coverage Ledger / source-only 模式 |
| [Trail of Bits FP Check](https://github.com/trailofbits/skills/blob/main/plugins/fp-check/skills/fp-check/SKILL.md) | `trailofbits/skills/plugins/fp-check/skills/fp-check/SKILL.md@b7e7278cbae1` | 确认/误报/证据不足分开判定 | RETAIN：Review 真实性门禁，扫描结果不能直接当漏洞 |
| [Trail of Bits Post-Patch Validation](https://github.com/trailofbits/skills/blob/main/plugins/post-patch-validation/skills/post-patch-validation/SKILL.md) | `trailofbits/skills/plugins/post-patch-validation/skills/post-patch-validation/SKILL.md@fff1346bc3b8` | 原漏洞＋同根因变体＋合法行为保留 | RETAIN：11.2.14 已吸收至 Review/Test references |
| [Trail of Bits Spec-to-Code](https://github.com/trailofbits/skills/blob/main/plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md) | `trailofbits/skills/plugins/spec-to-code-compliance/skills/spec-to-code-compliance/SKILL.md@b10d8a081c39` | 规格→实现与实现→规格双向核对 | ENHANCE：接口契约与完整 Review 新增双向 ledger |
| [Trail of Bits C Review](https://github.com/trailofbits/skills/blob/main/plugins/c-review/skills/c-review/SKILL.md) | `trailofbits/skills/plugins/c-review/skills/c-review/SKILL.md@709884da1cea` | C/C++ 代码/内存与并发威胁的审查覆盖 | RETAIN：user-space 范围不强套 bare-metal MCU |
| [NVIDIA SkillSpector](https://github.com/NVIDIA/SkillSpector/blob/main/README.md) | `NVIDIA/SkillSpector/README.md@6d48df00ac42` | 危险能力/隐藏指令/外传/扫描盲区与误报 | ENHANCE：扫描覆盖与 source-to-sink，而非新增扫描依赖 |
| [Zephyr Agent Skills](https://github.com/beriberikix/zephyr-agent-skills/blob/main/SKILL.md) | `beriberikix/zephyr-agent-skills/SKILL.md@03df00f7bbe4` | Kconfig/Devicetree/board 的精准领域路由 | RETAIN：只在真实 Zephyr toolchain 适用，非通用 MCU 默认 |
| [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills/blob/main/skills/react-best-practices/SKILL.md) | `vercel-labs/agent-skills/skills/react-best-practices/SKILL.md@237988de4a66` | 按真实影响排序和按需读取局部规则 | ENHANCE：Token 治理先判质量/安全、后排高成本热点 |
| [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/blob/main/README.md) | `addyosmani/agent-skills/README.md@7f610b8ca80f` | 生命周期反合理化与验收 | RETAIN：已有 Goal/Loop/TDD/Verification，避免套第二流程 |
| [Matt Pocock Skills](https://github.com/mattpocock/skills/blob/main/README.md) | `mattpocock/skills/README.md@f7038f139299` | Grill Me / 领域模型 / 最小实现 | RETAIN：已有提问与领域语义反例；尚无真实优劣实测 |
| [Google Skills](https://github.com/google/skills/blob/main/README.md) | `google/skills/README.md@e068f998b225` | 按产品/领域选择知识 | RETAIN：Profile + 按需加载，非当前产品的运行依赖 |
| [Android Skills](https://github.com/android/skills/blob/main/README.md) | `android/skills/README.md@6636206616de` | 官方 Android 专项规则 | OBSERVE：Android-specific API 不自动用于 Linux/RTOS/MCU |
| [Espressif Skills](https://github.com/espressif/skills/blob/main/skills/.gitkeep) | `espressif/skills/skills/.gitkeep@e69de29bb2d1` | 当前 skills 目录未有可审查实现 | OBSERVE：仅记录当前空目录，不宣称成熟 Skill |
| [.NET Skills](https://github.com/dotnet/skills/blob/main/README.md) | `dotnet/skills/README.md@78c47fd0f3a4` | Skill 价值的 Token/耗时/失败率度量 | ENHANCE：效益判断依赖实际运行迹线，不拿源码字节数代替 |
| [Kotlin Agent Skills](https://github.com/Kotlin/kotlin-agent-skills/blob/main/README.md) | `Kotlin/kotlin-agent-skills/README.md@7e1122e35bb6` | 按语言约束选择专业知识 | OBSERVE：Kotlin 领域知识不成为 ADK embedded 常驻 Skill |

## 验收边界与不吸收项
- **评测**：候选描述/触发词优化只使用训练案例，独立留出案例不可反复调参；必须保留真实模型输出、权限、tool calls、Token/缓存/耗时和独立 grader。当前没有运行模型，不生成假的 E2–E4 绿灯。
- **安全**：实际目标的信任边界、政策版本、受影响 principal/resource/source→sink 和扫描盲区需能追溯。未运行扫描时 `unverified/not-scanned`；规则命中不能自动定为漏洞，0 findings 也不能代表全覆盖。
- **Spec-to-Code**：同时记录要求在代码中的实现证据，以及代码新增、但规格未声明的可观察行为；缺证据和未检查范围不算符合。覆盖比例不代表缺陷发现率。
- **嵌入式**：Linux user-space C 审查工具、Zephyr Kconfig/Devicetree、Android API 的目标限制必须独立验证，不能以平台相似为理由强制导入。
- **成本与维护**：保留单一 Manifest/Runtime Router/Evidence/CI 权威，优先减少重复模型调用、长 reference 提前加载和不必要的评测重复；高风险审查不可为了省 Token 降级。

最终验收以 ADK 受保护 PR 的完整回归与主线发布为准，**不等于以上每个外部项目通过了正式授权、逐行审计或可再分发许可证检查**。
