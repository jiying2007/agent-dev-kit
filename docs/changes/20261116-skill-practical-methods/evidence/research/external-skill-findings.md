# ADK 新一轮外部 Skill 研究：三个可落地候选

日期：2026-11-16。研究范围：只读对照 ADK 11.3.5，本地基线 `63e8f61ad9a023b4349851ebb4c9a6eca042a119`。本文是提供给主执行代理的研究结论；没有修改 ADK 实现，没有安装或运行外部 Skill，没有远端写入。

## 结论与证据强度

建议采用三个局部改进：堆性能工具的目标匹配、偶发测试的同进程顺序污染诊断、协议操作整体时限与重试责任。第一个是当前指令中的具体工具用途混淆；后两个是当前指导未落到操作步骤的诊断/设计缺口。没有把它们表述为已观测到的 ADK 模型失败，也没有宣称改动已经提高任务成功率。

已先读上一轮 `docs/changes/20261116-skill-execution-fidelity/audit.md` 与 `source-review.md`；上一轮的提问依赖、独立 oracle、调试假设、阶段采样、边界证据与终态验收不重复引入。本轮通过搜索引擎发现来源，再直接读取作者的固定版本文件或官方手册；目录、排名、星数、第三方总结只用于发现，不作为质量证据。检索有界，不声称穷尽全网。

| 候选 | 当前差距 | 建议落点 | 优先级与范围 |
|---|---|---|---|
| C1 堆分析工具对应测量目标 | 性能 Skill 写“堆用 memcheck”，没有给出堆峰值/时间线工具，也未区分堆与 RSS | `skills/adk-performance-profiling-embedded/SKILL.md` 的 Linux 工具选择 | 建议采用；替换一句即可，避免新增通用分析框架 |
| C2 同进程测试顺序污染 | flaky 入口及 reference 有独立重复与环境比较，但无原 suite 顺序、前序测试污染与反序对照 | `optional-skills/adk-test-flakiness-triage/references/details.md`，入口只保留按需提示 | 建议采用；只在 suite/isolated 结果差异或共享状态线索时展开 |
| C3 整体时限与重试责任 | 协议入口有分层 timeout、最大次数和产品预算，但无剩余时限传播、退避计时、已有 SDK 重试与上层重试乘积 | `skills/adk-protocol-stack-integration/SKILL.md` 的 Retry and timing boundary | 建议采用；限有完成时限的操作，不能套到整条长连接寿命 |

## C1：堆峰值、泄漏检查与 RSS 分清

### 本地证据

基线 `adk-performance-profiling-embedded/SKILL.md` 的 Execution Target Boundary 明确写“CPU 用 perf/flame graph，堆用 memcheck”。Workflow 已有有效负载、输入/构建/频率固定、采样扰动、峰值和 ABAB；所以不应再复制“先量再改”的流程。缺的是对测量目标选择正确工具。

Valgrind 官方将 Memcheck 用于内存访问、初始化、释放和泄漏错误，将 Massif 用于堆使用量随执行变化及分配调用点。Massif 默认也不等于进程 RSS。依据 S1、S2，建议把原句替换为类似：

> 堆峰值/分配调用点用 Massif，错误/泄漏用 Memcheck；RSS 另量，并说明采样范围与扰动。

不要顺带要求安装 Massif；工具不可用时沿用 Skill 已有的 host/目标能力与证据边界。不要声称采样峰值是精确上界：Massif 的峰值采样和默认误差有条件，手册也描述只分配不释放可能漏记峰值。无需把这些完整选项抄进入口，交付数据时说明模式、版本和局限即可。

### 具体反例与验收

原创逻辑负载模型：两种执行都分配 64 次、释放 64 次、总请求 64 MiB、结束剩余 0 字节；逐块用完即释放时活跃 payload 峰值 1 MiB，先全部保留再释放时峰值 64 MiB。分配总量和最终泄漏口径不足以回答峰值占用问题。

该反例只建模活跃 payload，不是实际 Memcheck/Massif 或 RSS 测量。当前环境 `valgrind` 不可用，未安装、未伪造运行结果。落地验收应检查对“无泄漏但内存峰值过高”的任务是否选对指标与分析工具；不需要为一句文案修正新增广泛测试套件。

### 适用条件与开销

适合 Linux 用户态且有可控重放负载的堆占用定位。插桩会改变执行时间和资源占用；不能用它的 wall time 代替原生延迟 KPI，也不能默认用于内核/MCU。已有低开销统计先行规则保留。入口只替换工具映射，避免继续挤占 profile 上下文预算。

## C2：先比较独立运行和原 suite，再缩小污染者

### 本地证据

当前 optional flaky 入口要求成功/失败样本、单变量假设、环境比较、统计分母与隔离；reference 的 `run_flaky_samples` 每次执行一条已核命令，输出新目录并保存退出码。它能忠实重复选定的命令，但没有要求核实该命令是否保留了原失败的同进程前序测试、执行顺序、seed 和 worker 配置。

`adk-unit-test-embedded` 已有复位全局状态、清理线程的规则，不应把“测试应隔离”当新发现。真正增量是让 flaky 诊断从“多次重跑 victim”进入“同进程 polluter→victim 对照”，并尽量缩小前序集合。S3 提供了原始测试反模式的依据；下面的诊断矩阵是对当前缺口的具体化，不冒充外部 Skill 已包含一模一样的脚本。

建议在现有 reference 的“环境比较与最小诊断”中加入短段：

> 若单测独跑与 suite 结果不同，保留原顺序、seed、worker 和共享进程边界，比较 victim 独跑、原 suite、可疑前序→victim 与反序；逐步缩小前序集合，定位全局状态、环境、缓存、时钟和资源残留。新进程通过不能单独证明污染已修复；如把隔离作为设计修复，验证它的边界与成本。保持每轮精确用例结果与原始失败。

不要求所有 flaky 问题都跑这四组；时间、网络、并发类问题已有更合适的定位分支。也不要随意并行化原本有意串行的硬件集成测试。

### 具体反例与验收

原创 Python 状态反例只有两个 case：polluter 将模块状态从 default 改为 legacy 而不恢复；victim 需要 default。结果：

- victim 在 8 个独立新进程中为 8/8 PASS。
- 同进程 polluter→victim：polluter PASS、victim FAIL。
- 同进程 victim→polluter：两者 PASS。

因此，孤立重跑 8 次甚至更多次都无法排除此类污染。这个受控反例不是失败概率估计；没有把 8/8 解释为稳定率保证。它证明诊断维度的重要性，不证明现有 ADK 一定会误诊。

### 适用条件与开销

只在已有顺序/共享状态线索时调用原测试 runner 的顺序与进程配置，保持当前授权和单次超时。先保留原失败，再缩小前序；普通二分不保证适用于依赖多个污染者的非单调交互，不能把一次对半排除当作严格证明。新内容放在已有按需 reference，不建立新工具、不安装顺序随机化插件。

## C3：每层 timeout 之外，操作还有一个剩余时限

### 本地证据

协议 Skill 当前有：DNS/TCP/TLS/应用握手/KeepAlive 的独立 timeout；参数按协议、链路和产品容错预算；最大重试次数、退避、熔断；未知结果的非幂等外部操作先对账。这些都应保留。准确的缺口是未明确把一次操作的总时限分配给阶段、退避与后续尝试，也未识别 SDK 已有重试与上层重试叠加。

S4 的具体可靠性 reference 支持按短暂故障、幂等性与 jitter 设计重试；S5、S6 进一步支持整体时延和多层重试乘法。建议压缩替换现有 Retry boundary，而不是添加一整套云架构模式：

> 对有完成时限的操作，用本地单调时间计算剩余预算；DNS、连接、TLS、请求和退避均计入，每阶段取本地限制与剩余预算较小者，耗尽后不再启动尝试。核 SDK/调用层已有重试并明确责任层，按协议错误语义区分可重试与永久失败；必要时在允许的时序范围内加入 jitter。

这里“单调时间”“阶段取较小者”是从整体时限要求导出的实现建议，不是 S4 的逐字规则。跨主机不能直接传递本地单调钟绝对值；可传剩余时长或使用协议明确定义的 deadline 语义。一个重试责任层指应用/SDK 的重复尝试治理，不表示应粗暴禁用 TCP 等协议自身必要的重传。长连接 KeepAlive 的各次操作/重连预算与连接存续期应分别定义。

### 具体反例与验收

原创整数假时钟，没有网络调用或真实等待：

- DNS 600 ms、TCP 700 ms、TLS 600 ms、应用 700 ms，每段都低于本地 1000 ms 限制，整体仍达到 2600 ms，超过 2000 ms 操作目标。传播剩余预算时应用阶段只剩 100 ms，整体在 2000 ms 终止。
- 每次尝试 800 ms，三次尝试之间各退避 500 ms，次数有界仍用 3400 ms。总时限为 2000 ms 时第二次只能用剩余 700 ms，此后不再尝试。
- 三层每层最多三次尝试，故障下最深层调用数为 27；只有一个应用重试责任层时为 3。这里“三次”包含初次尝试，避免 retries/attempts 歧义。

建议的本地验收针对已有协议实现或已核 simulator：正常完成、短暂故障后成功、永久失败不重复、退避占满剩余预算、嵌套客户端重试这几个行为；不要求真实设备/线上故障注入。对多层重试确有业务必要的项目，应汇总最坏调用量与时延，而不是机械禁止。

### 适用条件与开销

面向有明确响应时限的连接、RPC、握手或重连步骤。复用已提供 deadline/timeout 的客户端比再包一层重试器更好。若严格实时协议、恢复时序或上游 Retry-After 与应用剩余预算冲突，应终止本轮并按既定语义返回/延后，不能为了塞进预算缩短协议要求的等待。jitter 只在协议允许范围内使用，不改动确定性时序合同。

## 已覆盖或拒绝整包引入

| 来源/方法 | 处理 | 原因与 ADK 已有覆盖 |
|---|---|---|
| S7 test-gap-audit：先广度清点、按风险深读，避免覆盖率替代行为 | 保留现状 | test-strategy/high-value-tdd 已有风险选择、公开行为断言、独立 oracle 与反例校准；本次未证明必须新增审计入口。不引入源码/测试文件名匹配脚本作为缺测证明 |
| S3 测试反模式中的自比较、覆盖率触碰、只验 mock 调用 | 保留现状；只采纳 C2 | 当前 test-strategy、unit-test、property-stateful-tests 已有独立期望与真实执行规则；并非断言每一条外部反模式都已单独枚举，整包复制没有足够差距依据 |
| S8 design-control-loop：setpoint/sensor/controller、先本地跑通、单一信息源 | 保留现状 | 当前 performance、debugging 的可证伪候选/原始证据和 single variable loop 已有实际对应；不能仅换术语制造改进 |
| S8 默认定时 CI、外部 headless agent、凭据与无人值守循环 | 本轮拒绝 | 超出当前只读研究与禁用外部模型/计划任务范围；也没有具体 ADK 缺口证明必须新增此系统 |
| S4 cloud-design-patterns 整包 42 模式 | 本轮拒绝 | ADK 不需要云架构词典；仅提取协议重试中能对应当前差距的少量内容 |
| S8 关于 workflow_dispatch 需先触发一次等特定 CI 做法 | 不采纳 | 与当前目标无关且不能仅凭 Skill 文案当作通用事实 |

## 可复读的一手来源

下面所有 repository 内容均直接读取了固定 commit 的实际文件；官方站点文档记录访问日期 2026-11-16，未虚构不可得的 commit。

| ID | 一手来源与固定地址 | 读取范围/证据身份 |
|---|---|---|
| S1 | https://valgrind.org/info/tools.html | 官方工具用途表；Memcheck、Massif、DHAT 区分。动态官方页面，无 commit |
| S2 | https://valgrind.org/docs/manual/ms-manual.html | 官方 Massif 手册，重点 9.1、9.2.2–9.2.8、9.4；采样误差、堆/进程区别。动态官方页面，无 commit |
| S3 | https://github.com/microsoft/testfx/blob/74be6a61c1324c7b4810841ba2716040b47230f4/.agents/skills/test-anti-patterns/SKILL.md | blob `5641f2ac231e8a2784d572f13b4be4798994d55d`；具体 Skill，重点 Test ordering dependency |
| S4a | https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/cloud-design-patterns/SKILL.md | blob `b9a17433b9bedf95947bfe6624ef0a4bfa053021`；具体 Skill 的调用边界 |
| S4b | https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/cloud-design-patterns/references/reliability-resilience.md | blob `208b92d8697abb62f4396c889640ba19c913a19c`；已读 Retry 等模式，选择性采用 |
| S5 | https://github.com/MicrosoftDocs/architecture-center/blob/13861343a03580f08556f9eddf44a3223e01cfa0/docs/best-practices/transient-faults.md | blob `165c153f14fc4870f5f088e8b31b126e821a95af`；重点 Determine an appropriate retry count and interval / Avoid antipatterns；官方发布页面 https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults |
| S6 | https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/ | 官方 AWS 作者文，当前跳转 https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter；重点多层重试、阶段超时覆盖。动态页面，无 commit |
| S7 | https://github.com/github/awesome-copilot/blob/97d89fa3a1fdd84cc7d6c42fe82dbbf8ff2e3c20/skills/test-gap-audit/SKILL.md | blob `31ea9fa996bf9efa3343a70f95efda34a1eb8cd7`；已读具体审计流程，不调用附带脚本 |
| S8 | https://github.com/humanlayer/skills/blob/4d69d20f6e9b57b4fcf0d501ccfb1be961f0f329/plugins/design-control-loop/skills/design-control-loop/SKILL.md | blob `c9abc1b884d6002b4b76a7f611cf7686e91d59c8`；已读具体 Skill，局部方法已覆盖，其自动化执行不采用 |

## 原始本地对照与反例文件

候选相关本地文件 SHA-256，均取自本研究的 11.3.5 基线：

| 文件 | SHA-256 |
|---|---|
| `skills/adk-performance-profiling-embedded/SKILL.md` | `c4c6b3e039bc022224a832d146f833b4ca9b69eefc08ee6f3b4a7f53dbaf2a3a` |
| `skills/adk-protocol-stack-integration/SKILL.md` | `7ac9b5cbb2b1a1a854063b86003c135d816f5a4a5a0a9400d0b6505cff1fa702` |
| `optional-skills/adk-test-flakiness-triage/SKILL.md` | `1b198f8b975bea9529552d899e38ae335ab2d6684e21e74c2eefcbb83f3898ba` |
| `optional-skills/adk-test-flakiness-triage/references/details.md` | `efaef84006e04c7b502837d7c2548459c86793c921f969824a593db1e4ab1f97` |
| `skills/adk-unit-test-embedded/SKILL.md` | `dd6bb63fe1b749a5d24767ddc8819d3f66c7dfd8cba94bbc1fb8fc1a88563db3` |
| `skills/adk-test-strategy/SKILL.md` | `e7442473f760be5402a114b61378686816c8f35a3cde1ada59801a6d11cf7378` |

反例代码：`/workspace/scratch/2d6ca6dc3d38/research-v2/external-skill-counterexamples.py`。

实际运行结果：`/workspace/scratch/2d6ca6dc3d38/research-v2/external-skill-counterexamples.json`。进程退出 0，6 项方法反例检查全为 true；8 个子进程只执行本文件自己的 victim，没有外部依赖、网络、真实等待或收费模型调用。

建议采用的是三个小幅指令更正与方法补全。不要把本报告/示例全量载入常驻 Skill，也不要把自创模型的六项检查计入 ADK 已有回归总数或实际 agent 行为成功率。
