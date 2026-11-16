# 一手来源与本轮取舍

本轮从优质独立 Skill 的具体文件出发，对照全部 65 项 ADK 入口及 53 个直接参考文件。覆盖清单只表示本轮读取与决定，不宣称穷尽互联网或证明所有模型行为。前轮已落地的方法保留，新增工作由真实反例决定。

| 原始来源（固定文件版本） | 本轮核对与决定 |
|---|---|
| [Matt Pocock grilling](https://github.com/mattpocock/skills/blob/7739eaed7f8f3915437a8def198a6d0d7206dbc7/skills/productivity/grilling/SKILL.md)，blob `d2f09a18e6a6c65c55f1271ba08dfeaf06f0bed3` | 保留依赖 frontier；结合原作者仓库 [#1406](https://github.com/mattpocock/skills/issues/1406) 的部分回答/重编号反例，增强 ADK 问题身份与依赖修订。问题报告是具体观察，不代表上游已修复；不照搬穷尽所有分支和重复总确认。 |
| [Anthropic build-eval](https://github.com/anthropics/skills/blob/9d630808e4add0a7146de4af9384155d5dee350a/skills/claude-api/shared/evals/build-eval.md)，blob `ba875b712ba63135c60aaba4710bf84681ddf34b` | 保留环境终态/工件评分、固定对照与原始试验身份；据此实跑 ADK compare 反例。修复完整时间窗口与验收项组成漂移，实测并减少同一次比较内的重复合同验证。不引入 API runner、模型付费调用或新评测框架。 |
| [Obra systematic-debugging](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/systematic-debugging/SKILL.md)，blob `62fc752aaef59a8bbed5d305f4cadc60f8ae07ed` | 保留组件边界证据与单假设实验，ADK 已覆盖，不重复叠加清单。三次失败只能触发重审，不能单凭次数证明架构错误。 |
| [Trail of Bits property-test reviewing](https://github.com/trailofbits/skills/blob/04b241176fd9c10738a61df53d2c677c53e42990/plugins/property-based-testing/skills/property-based-testing/references/reviewing.md)，blob `a2ca783a7dabaece9e383f0ace972bb4fe2f7881` | 保留空洞性质、过度过滤和独立 oracle 审查；前轮已覆盖。实际比较反例由验收派生，不用被测函数生成答案。重复调用可测非确定性，不能机械当恒真；简单独立数学 oracle 也不一律排除。 |
| [Addy documentation-and-adrs](https://github.com/addyosmani/agent-skills/blob/551c59cfddb6428be85364ba7588cf92c4c51448/skills/documentation-and-adrs/SKILL.md)，blob `019bf43d1845051775f83b4d894ee090365091b0` | 保留事实/命令/路径保真，验证示例能运行；文档提交晚于代码只作核查线索，不作为内容仍正确的证明。本轮因此直接编译/执行现有 BSP、接口与 Review 命令。 |
| [Sentry code-review](https://github.com/getsentry/skills/blob/24361e7958f9644d11f1de100654e3b04a509192/skills/code-review/SKILL.md)，blob `621007b4da6639b9574e3e0a18054df73a5de807` | 保留运行错误、真实边界与具体可执行 finding；已有局部反馈核验不重写。独立审查发现按名称拒绝的漏路由后先新增 RED 再修复。风格建议不冒充阻断问题。 |
| [AgentSkills 规范](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx) 与 [描述优化](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/optimizing-descriptions.mdx) | 仅作当前规范页面核对，未将动态 URL 冒充固定版本；沿用渐进加载和实际触发检查。新增重要行为置于导出正文，不能仅依赖被 renderer 剥离的自定义 frontmatter。 |

技术交叉核查：[Linux Kbuild](https://docs.kernel.org/kbuild/kbuild.html) 的 ARCH/CROSS_COMPILE、[Kconfig](https://docs.kernel.org/kbuild/kconfig.html) 的配置演进、[GNU make 并行执行](https://www.gnu.org/software/make/manual/html_node/Parallel.html) 的 jobs 语义，以及 [SemVer](https://semver.org/) 的公共 API 承诺。版本号不证明 wire/ABI 或实际能力，CPU 核数不代表内存预算。

固定 GitHub 页面经 Web open 返回 DisabledError 时，使用已连接 GitHub 的只读文件接口取得上述固定版本与 blob；搜索结果只用于发现和交叉核对，不算已执行技能。无第三方安装、脚本复制或外部模型调用。来源中的宿主专属确认、费用、权限与自动执行规则均不继承为 ADK 权限。
