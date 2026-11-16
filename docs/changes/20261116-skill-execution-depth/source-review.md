# 外部 Skills 方法研究与 optional 全量审查

日期：2026-11-16。ADK 基线：`5f442723`（v11.3.7）。
本轮检索使用两种搜索引擎；源码以原作者 GitHub 的当前分支与固定 commit/blob 复核。
覆盖 10 个外部仓库的 15 个具体实现/参考/评测文件，另读必要许可证与仓库身份。不是对这些仓库全部 Skills 的审计，也不宣称穷尽互联网。
已全文读完 ADK 的 9 个 optional 入口及其 5 个 reference，共 14 文件。外部脚本未执行，未调用外部付费模型。
身份明细见 `evidence/research-sources.json`；无需将原文整包带入运行时。

## 已实施并验证的两项方法增量

1. **执行对象身份**（Microsoft ONNX Runtime、Alibaba MNN）：源码和构建 hash 不能单独证明运行中加载了目标共享库或目标 dispatch 分支。为性能诊断/比较补按需读取的路径核验：正在执行的 binary/shared library 身份、适用 build-id、符号或分支证据；遇到漂移时用不受候选影响的对照配置帮助归因。不得把知道库已映射等同于知道热点分支已执行，也不得照抄 MNN 的平台路径和固定参数。
2. **异步 readiness 修复**（obra/superpowers）：只在日志/受控复现已经支持 readiness 竞争时，以项目原生 event/barrier 或有界条件等待替代猜测延时。核本次操作身份，使用 monotonic deadline，保留 timeout/cancel 行为，明确谓词允许合法零值；实际 debounce、节流和时序要求仍单独验证。外部示例的固定 10ms、Date.now、泛 truthiness 和历史提速均不照搬。

两者是源码方法缺口，不是已复现的 ADK 用户事故；具体 host 反例与修复结果另由实施验证记录。

## 来源选择

| 来源与具体文件 | 方法评价与ADK处理 |
|---|---|
| Anthropic skill-creator / scripts/run_eval.py | 原始轨迹与重复评测有价值，但当前 future 异常追加 false，negative case 全错误时可能算通过；仅静态代码路径结论。ADK 已区分 invalid-eval，保留现有方法，不引入执行器。 |
| Sentry prompt-optimizer / SKILL.md、meta-optimization-loop.md | 因果编辑、最小差异候选、同切片比较、留出、平台/振荡/非prompt瓶颈停止条件；已有覆盖，RETAIN。 |
| Sentry security-model / SKILL.md | 实际 enforcement、稳定不变量、源码关联和过期检查；现供应链边界已有覆盖，RETAIN。 |
| Matt Pocock writing-for-agents | 条件引用是一等接口，每分支一个触发，环境可查信息不重复缓存；现有按需加载方向正确，RETAIN，不全局改写。 |
| Matt Pocock codebase-design / DESIGN-IT-TWICE.md | 候选接口须实质不同，可按风险使用；拒绝将3+代理和完整探索设成所有任务默认。 |
| Trail of Bits fp-check / bug-class-verification.md | 按内存、整数、并发、状态等类别核可达性和真实后果；保留既有安全复核，不引六层通用重流程。 |
| Trail of Bits mutation-testing / equivalent-mutants.md | 存活变异需类型、可达性、下游消费和区分输入；未覆盖不等于不可达，UB不能因测试绿判等价。现非本轮主要变更，OBSERVE。 |
| Addy Osmani performance-optimization eval | 用实际基线、瓶颈、可测修复与回归信号评分；不以工具调用顺序替代结果，现ADK已覆盖。 |
| Vercel React best practices / async-parallel.md | 独立读取重叠执行；有依赖、变更和风险操作保留顺序。React专项规则不进入嵌入式core。 |
| Microsoft Playwright CLI / SKILL.md | find与原始输出能局部取上下文；无相应已授权browser任务，不因此新增工具依赖或Skill。 |
| Microsoft ONNX Runtime / ort-build | 构建参数可静默改变实际执行kernel，适合补执行对象核验；增量构建方法已有覆盖。 |
| Alibaba MNN / cpu/shared/build-test-and-benchmark、cpu/optimize | 实际加载库、dispatch、有效工作、同档正确性与温漂对照有价值；只提炼通用方法，不复制项目参数与强制同二进制策略。 |
| obra/superpowers / condition-based-waiting | 条件等待适合补可复现异步就绪故障；拒绝泛化固定poll间隔或来源的历史性能指标。 |

### 许可证记录

Anthropic skill-creator 的局部 LICENSE.txt 已核 Apache-2.0；MNN LICENSE.txt 已核 Apache-2.0；ONNX Runtime LICENSE 已核 MIT；Trail of Bits LICENSE 已核 CC-BY-SA-4.0。Vercel 的当前 Skill frontmatter 声明 MIT（仓库 metadata 空，不能推断无许可证）。
其余 Sentry/Playwright 的 GitHub license metadata 为 Apache-2.0，Matt/Addy/obra 为 MIT，属于 metadata 读取记录；本轮不导入这些原文或脚本。JSON 记录固定 blob 并明确没有导入。
MNN 根 LICENSE 返回404后按tree找到 LICENSE.txt；Matt和Trail的旧索引路径也经过真实tree纠正，404没有被当成无来源。

## 9 个 optional 逐项结论

| Skill | 决定 | 全文审查结论 |
|---|---|---|
| adk-data-fetch | RETAIN | 三个独立安装项与结果映射已明确，partial/not-verified不会被父入口吃掉。 |
| adk-email-imap-fetch | RETAIN | EXAMINE/BODY.PEEK、三元邮件身份、重连UIDVALIDITY、预算与逐条错误已覆盖。 |
| adk-fetch-url-content | RETAIN | origin/IP/redirect、主正文、相对链接、编码/大小、部分结果和不可信输入边界清楚。 |
| adk-external-practice-absorption | RETAIN | 最新source-root修复、执行模式与已批准续做路径已就位；不用重复intake。 |
| adk-incident-rca-report | RETAIN | 事故稳定后才成文，事实/因果/假设/未决分开；短因果链不强制5-Why。 |
| adk-prose-revision | RETAIN | report/revise、事实/字面量保护、无需改动结果、八类反例覆盖合理。 |
| adk-security-supply-chain | RETAIN | 研究/引入/运行分层，source-to-sink、覆盖与不确定性明确；不加扫描器。 |
| adk-skill-composition-governance | RETAIN | collision-only、唯一primary、已有matcher/effect_trials、holdout与invalid-eval已覆盖成熟方法。 |
| adk-test-flakiness-triage | ENHANCE | 保留现有采样/顺序污染/统计边界，在已有reference补按证据触发的就绪条件等待方法。 |


## 固定源码索引

| 仓库 | 文件与固定版本 | 采用决定 |
|---|---|---|
| `anthropics/skills` | [skills/skill-creator/scripts/run_eval.py](https://github.com/anthropics/skills/blob/1780c5e5a552fd4d1c9d6a7b0cab26b0c2bef064/skills/skill-creator/scripts/run_eval.py) | OBSERVE |
| `getsentry/skills` | [skills/prompt-optimizer/SKILL.md](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/prompt-optimizer/SKILL.md) | RETAIN |
| `getsentry/skills` | [skills/prompt-optimizer/references/meta-optimization-loop.md](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/prompt-optimizer/references/meta-optimization-loop.md) | RETAIN |
| `getsentry/skills` | [skills/security-model/SKILL.md](https://github.com/getsentry/skills/blob/a582c51ee29d0f35e6ac321340796f77d43da733/skills/security-model/SKILL.md) | RETAIN |
| `mattpocock/skills` | [skills/productivity/writing-for-agents/SKILL.md](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/productivity/writing-for-agents/SKILL.md) | RETAIN |
| `mattpocock/skills` | [skills/engineering/codebase-design/DESIGN-IT-TWICE.md](https://github.com/mattpocock/skills/blob/5863806dd4e15c63174bee4e7515a4256792ecfa/skills/engineering/codebase-design/DESIGN-IT-TWICE.md) | OBSERVE |
| `trailofbits/skills` | [plugins/fp-check/skills/fp-check/references/bug-class-verification.md](https://github.com/trailofbits/skills/blob/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/fp-check/skills/fp-check/references/bug-class-verification.md) | RETAIN |
| `trailofbits/skills` | [plugins/mutation-testing/skills/mutation-testing/references/equivalent-mutants.md](https://github.com/trailofbits/skills/blob/149d7b21f4067765b82e67029730b42d228ef4b4/plugins/mutation-testing/skills/mutation-testing/references/equivalent-mutants.md) | OBSERVE |
| `addyosmani/agent-skills` | [evals/cases/performance-optimization.json](https://github.com/addyosmani/agent-skills/blob/39b723ceebf81474d0557c1fecd01eddab585563/evals/cases/performance-optimization.json) | RETAIN |
| `vercel-labs/agent-skills` | [skills/react-best-practices/rules/async-parallel.md](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/react-best-practices/rules/async-parallel.md) | RETAIN |
| `microsoft/playwright-cli` | [skills/playwright-cli/SKILL.md](https://github.com/microsoft/playwright-cli/blob/b21724888b8100b05ef8dee3a92f2bb03bf4dcde/skills/playwright-cli/SKILL.md) | OBSERVE |
| `microsoft/onnxruntime` | [.github/skills/ort-build/SKILL.md](https://github.com/microsoft/onnxruntime/blob/d889b8bdebd234bcf8d343aa6b4deae5d729d42d/.github/skills/ort-build/SKILL.md) | ENHANCE-CANDIDATE |
| `alibaba/MNN` | [skills/cpu/shared/build-test-and-benchmark.md](https://github.com/alibaba/MNN/blob/b6a32165e2855106b76852fba80793d58a829663/skills/cpu/shared/build-test-and-benchmark.md) | ENHANCE-CANDIDATE |
| `alibaba/MNN` | [skills/cpu/optimize/SKILL.md](https://github.com/alibaba/MNN/blob/b6a32165e2855106b76852fba80793d58a829663/skills/cpu/optimize/SKILL.md) | OBSERVE |
| `obra/superpowers` | [skills/systematic-debugging/condition-based-waiting.md](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/systematic-debugging/condition-based-waiting.md) | ENHANCE-CANDIDATE |

执行对象身份与条件等待已进入候选 Skill，并由实际 ELF/共享库选择、已删除/退出进程和 Condition 等待反例验证；来源项目本身的效果未复现，未导入其脚本或整包。官方 Git、CMSIS-SVD 与 socket 文档另用于核方法边界；链接在原始分组记录。真实模型 A/B、Token、费用、端到端时延和板端/HIL 仍为 not-measured。
