# 原始来源审查与方法取舍

本轮以完整 65 项 ADK Skill 为审查分母，跨工程、测试、安全、嵌入式、上下文、数据获取和技能规范检索原始来源；不是外网质量排行榜，也不声称已穷尽互联网。搜索目录只发现候选，只有实际读取的文件才进入证据。

## 实施的六类方法

| 方法与来源 | 当前 ADK 缺口 | 采用方式 |
|---|---|---|
| Matt Pocock to-tickets：公共契约兼容迁移 | 只强调每个纵切独立可验，缺少大范围机械重构例外 | 条件性 expand / consumer migration / contract，并保留唯一集成与退役条件 |
| Obra writing-good-tests：独立断言 | expected 与被测 helper 共用逻辑可能漏报相同错误 | 契约派生常量/夹具、明确错误变体与合法边界对照 |
| Addy Osmani constraint-driven-development：检查器判读 | 有原退出码仍可能错误接受完整性或业务失败 | 条件性校准 clean / violation / below-threshold / error，执行、完整性与阈值分离 |
| Trail of Bits property/harness 方法 | 用例与覆盖率未明确性质、状态序列和生成器有效性 | 独立不变量、非空输入、有界状态序列及反例回放，不导入 fuzz 工具 |
| sanitizer Skill 与 GCC/LLVM 原文核查 | 编译/exit 0 不能证明运行期检测干净 | 目标适配、已知负例校准、recover 报告与真实 runtime 判读 |
| MCU 栈分析与 GCC/FreeRTOS 原文核查 | 单函数 .su 数值不构成整个任务栈上界 | 区分函数 frame、调用链、动态调整、IRQ/RTOS 和 high-water 的实际单位/范围 |

具体原始文件、commit、Git blob、阅读范围与许可见研究证据。上述内容为独立概括和 ADK 自编示例，没有复制第三方脚本或执行其安装指令。

## 通用方法原始仓库

| 原始仓库 / 固定 commit | 实读文件数 | 决定与理由 |
|---|---:|---|
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/5863806dd4e15c63174bee4e7515a4256792ecfa) / `5863806dd4e1` | 1 | 增强：全局重构可用 expand→migrate→contract；普通新功能仍用纵向切片。 |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/39b723ceebf81474d0557c1fecd01eddab585563) / `39b723ceebf8` | 2 | 增强：实际 checker 将工具退出、报告完整性及严重度阈值分开，拒绝缺字段、未知等级和扫描错误。 |
| [obra/superpowers](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7) / `22f0b463e7a5` | 2 | 增强：断言值来自独立契约；每个可疑测试应能暴露一个明确错误变体。 |
| [getsentry/skills](https://github.com/getsentry/skills/tree/a582c51ee29d0f35e6ac321340796f77d43da733) / `a582c51ee29d` | 2 | 保留：审查读取完整改动、调用者和保护条件以消除误报；PR 循环区分 actionable 与 pending/draft/no-check。 |
| [microsoft/hve-core](https://github.com/microsoft/hve-core/tree/0e5623a16e06c5b1353bbf77ad4cba49db4c28b1) / `0e5623a16e06` | 1 | 保留：只执行依赖满足的计划项，按任务保留证据，执行完成和审查完成分开。 |
| [google/agents-cli](https://github.com/google/agents-cli/tree/6eedbdc2f44c388cbfc5f305eb83b9924cfefebb) / `6eedbdc2f44c` | 1 | 保留：逐例保存 trace 与实际 outcome，候选改动检查目标与回归；错误不能靠汇总分数掩盖。 |
| [muratcankoylan/Agent-Skills-for-Context-Engineering](https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/tree/9ff0c99108b36d3b886defd825d8ac1f47dba374) / `9ff0c99108b3` | 1 | 保留：压缩显式保留工件身份、当前状态和增量合并，原始上下文可回溯。 |
| [anthropics/skills](https://github.com/anthropics/skills/tree/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064) / `1780c5e5a552` | 1 | 保留：让读者只基于成品回答理解问题；作者历史不应代替文档本身的说明。 |
| [openai/skills](https://github.com/openai/skills/tree/49f948faa9258a0c61caceaf225e179651397431) / `49f948faa925` | 2 | 保留：CI 诊断优先真实失败日志；处理 gh 字段/下载不兼容与日志不可用。 |
| [firecrawl/skills](https://github.com/firecrawl/skills/tree/1d4b0728d0f448cafef2eb8370c907fde7cb6f42) / `1d4b0728d0f4` | 2 | 保留：已知页面直读、复用已抓取结果、保留请求身份后恢复大输出；外部内容作为不可信数据。 |
| [sweetrb/apple-mail-mcp](https://github.com/sweetrb/apple-mail-mcp/tree/2e2f245016a6b59fc361783e6bbc865591d18c07) / `2e2f245016a6` | 1 | 保留：选读工具契约说明 EXAMINE/BODY.PEEK、UIDVALIDITY+UID、原始字节及大小边界。 |

sweetrb/apple-mail-mcp 为明确选读 IMAP/只读契约，其余上表记录按研究清单全文读取；文件数不含许可文件，不意味着相应 backend、runner 或宿主已验证。openai/skills 是所读取的历史目录快照；根研究还沿当前目录指引读取 openai/plugins，不把旧目录当唯一现行来源。

## 补充生态与独立反例审查

- [Vercel Optimize](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/vercel-optimize/SKILL.md)：全文核验指标先行、候选约束与版本化来源，通用原则已由 ADK 性能与证据方法覆盖；不引入 Vercel CLI、账号、付费观测、固定并行数和重复询问流程。该 commit 根 LICENSE 返回 404，未据此推断可复制实现。
- [OpenAI Plugins frontend-testing-debugging](https://github.com/openai/plugins/blob/d420d13051bffe4543ed39e30fa46b87148e47dd/plugins/build-web-apps/skills/frontend-testing-debugging/SKILL.md)：全文核验真实用户流程、交互后状态和运行期证据；ADK 现有完成验证已覆盖一般原则。Browser API、截图排版与插件推荐属于源宿主，不变成 ADK 依赖。
- [AgentSkills client implementation](https://github.com/agentskills/agentskills/blob/83021e2be457a9b6679148719c1f6074f0ad975e/docs/client-implementation/adding-skills-support.mdx)：允许正文激活；结合 ADK 实际 renderer，新增必要条件放正文与自身 reference，不能只存在于自定义 frontmatter。规范本身不授予宿主权限。
- [Anthropic trigger evaluator](https://github.com/anthropics/skills/blob/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064/skills/skill-creator/scripts/run_eval.py)：独立只读核到异常可进入 negative 未触发计分的分支；不导入该 runner，不将触发分数当任务成功。现有 ADK 无效试验/效果边界已覆盖，避免重复叠加流程。
- [Sentry skill-evals](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/skill-writer/references/skill-evals.md)：保留按需参考和评测材料不进入普通执行上下文的原则；不采用 AXIS、Codex adapter 或 full-auto 默认。
- [Trail of Bits code-improver evals](https://github.com/trailofbits/skills/blob/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/code-improver/evals/README.md)：任务结果与新格式工件评分须分开；旧结果不能证明改版效果。其污染扫描也不能凭退出 0 补足未读取的 trace。CC BY-SA 4.0 来源只独立概括方法，不复制实现。

完整来源记录保留已拒绝做法、工具/许可缺口和精确版本。固定 GitHub 页面在 Web fetch 被拒时使用现有 GitHub 只读连接器取原文件，不把搜索摘要冒充原文；旧搜索路径不归入当前 commit。

## 领域方法原始文件与官方交叉核查

| 来源组 / 固定 commit | 实读文件数 | 方法与决定 |
|---|---:|---|
| [trailofbits-property](https://github.com/trailofbits/skills/tree/149d7b21f4067765b82e67029730b42d228ef4b4) / `149d7b21f406` | 4 | 契约性质、生成约束、独立预期、可重放缩减输入、把实现缺陷/性质错误/契约歧义分开。；adopt-method-only |
| [trailofbits-handbook](https://github.com/trailofbits/skills/tree/149d7b21f4067765b82e67029730b42d228ef4b4) / `149d7b21f406` | 4 | 窄目标 harness、每轮状态重置、独立回放、匹配源码的 SUT 覆盖和 sanitizer 检测有效性。；adopt-method-with-primary-doc-corrections |
| [obra-debugging](https://github.com/obra/superpowers/tree/22f0b463e7a5e579904dd6211a520321035526f7) / `22f0b463e7a5` | 2 | 复现、跨边界证据、沿调用链追源、单变量实验。；retain-existing |
| [sentry-scanner](https://github.com/getsentry/skills/tree/a582c51ee29d0f35e6ac321340796f77d43da733) / `a582c51ee29d` | 3 | 逐文件/加载入口、危险脚本与结构自动执行路径、source-to-sink 意图确认。；retain-existing |
| [zephyr-build](https://github.com/beriberikix/zephyr-agent-skills/tree/ed63cdfb8cdfbeb5946ea39c33f4aa6bcf3a5cce) / `ed63cdfb8cdf` | 2 | 跟踪构建系统、Kconfig 和最终 build/zephyr/.config；目标配置与实际生成物对照。；retain-with-rejected-claim |
| [zephyr-performance](https://github.com/beriberikix/zephyr-agent-skills/tree/ed63cdfb8cdfbeb5946ea39c33f4aa6bcf3a5cce) / `ed63cdfb8cdf` | 3 | map 与逐线程运行时栈观测结合；功耗模型输入和真实数据分开。；adopt-stack-interpretation-only |
| [intel-linux-perf](https://github.com/intel/skills/tree/22bf0c0d0167f4da18e2effbfd2661b2481b3cd8) / `22bf0c0d0167` | 1 | 先低开销统计再热点/锁/调度采样，按实际 CPU/event/capability 选择。；retain-existing |

上述 Sentry scanner 脚本为明确选读两段，其余领域记录全文读取。对应 10 项工具原始依据涵盖 GCC 14.2/LLVM sanitizer、LibFuzzer、GCC 栈输出、固定版本 FreeRTOS Kernel、Zephyr 配置与 thread analyzer、Hypothesis 和 Linux fault injection；工具文档核查不计为工具已运行。

跨源核查拒绝了几类不准确或不适配做法：ASan 虚拟地址保留量不能等同 RSS，默认关闭 fuzz 内存限制不适用；任意字节指针强转可能引入对齐/aliasing 问题；被大量丢弃的性质输入不能直接算通过；Zephyr `.conf` 的 `CONFIG_` 语法以官方文档为准。现有 driver/fault 恢复已覆盖的内容予以保留。

## 实测与未测量

六类方法将用本仓自编的有界程序和已安装工具验证。它们能够验证公开示例、判读和拒绝路径，不构成模型使用 Skill 的真实 A/B。Token、成本、模型成功率、原生宿主发现/触发及板端性能仍未测量；上游 benchmark 不转写为 ADK 结果。
