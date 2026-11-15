# 65 个 Skill 的任务方法源审查

基线：`c57f4f8a7983f52257c0587eb85881a006e6dc07`。以下来自实现分工实际读取的主文件、适用 references 及相关代码；独立审查另行给出。范围是 56 core + 9 optional，不把 catalog 命中等同于工作方法审查，不把源码检查等同于模型或设备实测。

“保留”表示已有具体任务方法、本轮没有确认必须修改的缺陷，不是无缺陷认证。14 个 Skill 的正文或既有 references 有实质修复，其余 51 个保留；共用 catalog 检索修复覆盖全部 65 个。

## 需求、实现、测试和文稿（functional_skills_audit，14）

| Skill | 实际核查与决定 |
|---|---|
| `adk-requirements-triage` | 保留 brief/执行交接分流、可逆假设和验收；明确任务不重复访谈。 |
| `adk-structured-requirements-questioning` | 保留 Explore/Challenge、决策依赖、已有答案复用与无增量收敛。 |
| `adk-lightweight-planning` | 保留相关入口定位、最少步骤和真实验证；实施请求交执行职责。 |
| `adk-task-breakdown` | 保留纵向切片、真实阻塞依赖、Ready Frontier 和共享写入唯一 owner。 |
| `adk-planning-execution-loop` | 保留原计划恢复、inline 执行、局部失败收敛、通过范围复用；CLI 恢复另修。 |
| `adk-code-simplification` | 修复伪通用参数、行数/正则冒充质量判断、早返回跳过后续清理。 |
| `adk-systematic-debugging` | 保留复现、最短红绿反馈、单变量证伪和偶现分布，不强凑假设层数。 |
| `adk-code-review-loop` | 主入口保留；reference 补真实入口/调用者/错误清理追踪与可验证 finding，修复重复异义 Verdict。 |
| `adk-test-strategy` | 修复策略与已授权实施的交接；不能用设计清单关闭写测试任务。 |
| `adk-unit-test-embedded` | 修复验证层互斥、仅交清单和伪参数；交真实测试/fixture/命令结果，明确 compile-only。 |
| `adk-verification-before-completion` | 保留 checkpoint/goal-final、原验收分母及当前证据，不再新增门禁。 |
| `adk-adr-writer` | 保留按风险选深度、真实取舍/后果和读者独立理解验证。 |
| `adk-prose-revision` | 保留 report/revise、可定位修改、术语/数字/否定条件保真。 |
| `adk-incident-rca-report` | 保留事实/假设/未知分离、适用因果链和可复验改进，拒绝虚构损失/负责人。 |

## 嵌入式与资料获取（domain_skills_audit，25 个唯一项）

本分工还复核了上表的 unit-test-embedded；以下不重复计数。

| Skill | 实际核查与决定 |
|---|---|
| `adk-bsp-analysis` | 保留 boot/init/match/probe 与资源依赖追踪、TRM/errata 和迁移风险。 |
| `adk-bsp-porting-playbook` | 保留平台差异、最小启动、外设渐进接入、制品与恢复验证。 |
| `adk-cmake-cross-build` | 保留真实 toolchain/preset、host/compile-only/emulator/board 分流及 ELF/map 核验。 |
| `adk-driver-implementation` | 保留资源 owner、partial init、IRQ/DMA、cancel/late completion 和退出清理。 |
| `adk-driver-bringup-checklist` | 保留 minimal/functional/soak 阶段和轮询到 IRQ/DMA 的定位顺序。 |
| `adk-register-map-design` | 保留手册来源、位域/访问语义、W1C/read-clear/FIFO 与竞态，不造芯片数据。 |
| `adk-interrupt-dma-patterns` | 保留速率/预算选型、buffer ownership、cache/barrier、背压和 teardown。 |
| `adk-rtos-task-design` | 修复响应时间迭代/适用前提、ISR 计数和 trace/WCET 边界，保留有依据的零阻塞。 |
| `adk-component-api-stability` | 修复源码 API 与旧二进制 ABI 混淆、符号表证据局限、目标工具选择和退出码。 |
| `adk-performance-profiling-embedded` | 修复诊断强制 A/B、指标口径、invalid/inconclusive/no-gain；补 KWS 比较并防止读取失败采样的旧结果。 |
| `adk-hardware-debugging` | 保留 fault/PC/LR/栈到根因的证伪链、内核能力差异、复位/低功耗唤醒路径。 |
| `adk-offline-core-dump-triage` | 修复候选线索与制品匹配混用，补 batch GDB、sysroot/库顺序及 partial 解释。 |
| `adk-embedded-debug-transport` | 保留按通道可用性连接、版本与采样窗口、最小日志和后续分析交接。 |
| `adk-embedded-remote-debug-log-triage` | 保留 host/network/transport/shell/app 分层、ADB 双证据、失联恢复与时间线。 |
| `adk-embedded-diagnostic-harness` | 保留 invoke_ret/前提/预期失败解释、环境与产品缺陷分离、focused suite。 |
| `adk-protocol-stack-integration` | 保留状态机、编解码边界、长度/超时/幂等及丢包断链验证和目标工具分流。 |
| `adk-integration-hil-sil` | 保留真实 runner、host/SIL/HIL 区分、设备/端口隔离、真实健康恢复。 |
| `adk-fault-injection-recovery` | 保留风险驱动注入、单变量、恢复 SLA/一致性验证，不强迫无关破坏实验。 |
| `adk-static-analysis-c-cpp` | 修复仅选变化源文件遗漏头文件消费者；保留编译上下文、完整数据库回退与管道失败。 |
| `adk-embedded-storage-layout-migration` | 保留内容/布局/FS 分流、partition/volume/OTA 链、数据保护和真实设备恢复验证。 |
| `adk-embedded-release-orchestration` | 保留制品身份、分阶段发布和多 MCU 部分成功/激活/健康/回滚。 |
| `adk-production-field-readiness` | 保留 BOM/批次、产测/校准/标识、诊断包、RMA 与恢复实证。 |
| `adk-data-fetch` | 保留 URL/邮箱子流程选择和安装/来源范围；解析缺口在子 Skill 修复。 |
| `adk-fetch-url-content` | 补正文/编码/结构/链接提取和空页面、截断、partial 结果。 |
| `adk-email-imap-fetch` | 补筛选到有界 UID 获取、UIDVALIDITY、MIME 解码、逐封失败和续读身份。 |

## 连续执行与上下文（efficiency_usability_audit，6 个唯一项）

本分工还审查了上表的 planning-execution-loop；以下不重复计数。

| Skill | 实际核查与决定 |
|---|---|
| `adk-runtime-router` | 保留可信 inventory、明确任务续行和延迟加载。E1 路由不可达仍是能力缺口；修正文档中的 micro 越过路由说法，未启用新的执行路径。 |
| `adk-goal-authoring` | 修复只读 resume 丢字段、拒绝 closed/blocked 原批次和虚构预算；strict check 不放宽。 |
| `adk-token-context-governance` | 修复普通上下文任务被强制使用 ADK 内部验证；保留保真/原文回退/真实 usage 区分。 |
| `adk-context-engineering` | 保留 stable/task/evidence/on-demand 分层、可信来源及最小任务包；纯执行作 supporting。 |
| `adk-context-compress-handoff` | 保留新旧目标、在途/阻塞/历史、下一动作和原文指针；丢失问题修在 CLI，不再堆模板。 |
| `adk-memory-curator` | 保留来源范围、stale/duplicate/conflict、脱敏和候选交付；report-only 不是缺失写权限。 |

## 交付、知识与方法（root，20）

| Skill | 实际核查与决定 |
|---|---|
| `adk-cross-team-handoff` | 保留 lite/formal、真实 owner/receiver、可独立验收和签收，不强制普通交接重型 RACI。 |
| `adk-knowledge-archive` | 保留有价值的事实/证据/边界提炼、脱敏与既有 topic，避免生成无用归档。 |
| `adk-worktree-governance` | 保留 stay-current/isolated 分流、dirty 归属、冲突隔离、真实整合与清理边界。 |
| `adk-commit-pr-quality-gate` | 保留 message-only/PR/high-risk 分流、同快照证据复用和实际问题收口。 |
| `adk-repo-drift-remediation` | 保留源事实、漂移地图、风险排序、最小修复与共享配置串行整合。 |
| `adk-release-versioning` | 保留目标版本政策、变更归档、制品/回滚与 ADK 专有 promotion 分界。 |
| `adk-branch-closeout` | 保留 status/create-pr/merge/keep 分流、精确 HEAD/CI，不强制展示无关选项。 |
| `adk-after-action-review` | 保留 lite/standard/promotion、真实失败和下一次行动，无复用价值不造候选。 |
| `adk-archive-governance` | 保留现有 meta/topic/hash 修复、supersedes、目标查询与复验，不替代新笔记。 |
| `adk-engineering-growth-review` | 保留 index-first、跨时点证据、行动/复验信号，避免全历史扫描和无据评价。 |
| `adk-skill-composition-governance` | 保留 collision-only/composition-change、近邻负例、主辅职责和真实行为证据区分。 |
| `adk-repo-prompt-analysis` | 保留实际调用点/role/变量追踪、最小来源范围，不以描述替代实现。 |
| `adk-skill-deep-analysis` | 保留有界发现、方法对比、净差异/反例和已有实施交接，避免重开搜集。 |
| `adk-parallel-agent-governance` | 保留并行收益判断、唯一写入 owner、最小任务包与最终整合，不创造额外 worker。 |
| `adk-interface-contract-design` | 保留输入/错误/幂等、生命周期、显式序列化、正常/边界/异常用例和规格实现双向核对。 |
| `adk-artifact-gating` | 保留跨仓 artifact 状态、验证与真实签收；不扩展到单仓普通任务。 |
| `adk-pilot-framework` | 修复空目标、泛化前提、旧路径和任务验收缺位；分 smoke/compare，环境阻塞不误判能力失败。 |
| `adk-external-practice-absorption` | 保留 source/scoped/portfolio/behavior 分流、复用已审来源、批准后直接交实施。 |
| `adk-test-flakiness-triage` | 保留环境/时序单变量、样本与失败率边界、quarantine 解除条件，防止重跑刷绿。 |
| `adk-security-supply-chain` | 保留 source/adoption/runtime 分层、可执行路径/来源到敏感操作分析、secret 与扫描覆盖限制。 |

## 未证明的效果与保留项

- 真实模型任务成功率、首次完成率、Token、费用、时延以及各宿主加载行为均 `not-measured`；没有自动安装、额外模型调用或现场测量。
- E1 低风险实现路径尚未建立；本轮只纠正文档冲突。需要可信风险输入与拒绝路径设计，不能依据“小任务”字样放宽执行。
- clang-tidy/cppcheck/GDB/abidiff 的目标执行未发生；GCC 反例、TU 枚举、Bash 控制流和公式演算只证明各自所测范围。
- 全部 65 项可检索与全部职责已读是两个独立事实，均不能证明已消除所有缺陷。
