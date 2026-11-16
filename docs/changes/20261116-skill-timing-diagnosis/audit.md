# Skills 全量复审与处理决定

基线 v11.3.8 / `913b6b3a0838ccddae252a3a8536ac7d41598810`。三组重新完整读取 **65 个 Skills、153 个文件、421,746 bytes**；主整合逐项验证 Git blob、SHA256、长度，清单与 Git 跟踪的 core/optional 文件严格相等。

本轮选定 4 个已有 Skills 改进，其余 61 个保留并列出依据。上游索引覆盖 **16 个仓库、23 个具体固定版本文件**（包含许可文件；各文件完整/局部阅读范围见原记录）。不以热度或仓库数量证明质量。

## 逐项决定

| Skill | 分组 | 决定与依据 |
|---|---|---|
| `adk-adr-writer` | core | 保留：按风险写ADR，真实备选、保真和冷读边界完整。 |
| `adk-after-action-review` | core | 保留：lite/standard/promotion分流，普通复盘无需长期晋级空字段。 |
| `adk-archive-governance` | core | 保留：hash mismatch保留原值和可信原件，不盲重算；入口需核验。 |
| `adk-artifact-gating` | core | 保留：READY/PASS与workflow阶段区分，真实通过才填PASS已澄清。 |
| `adk-branch-closeout` | core | 保留：同范围授权延续、精确head/check及fresh-main已有，删除单独授权。 |
| `adk-code-review-loop` | core | 保留：原始Git快照取证已落地，局部反馈/完整审查和双裁决保持。 |
| `adk-code-simplification` | core | 保留：以理解负担而非行数判断，保留cleanup与副作用顺序。 |
| `adk-commit-pr-quality-gate` | core | 保留：message-only/PR-readiness/专项门禁按实际影响加载。 |
| `adk-component-api-stability` | core | 保留：源码API/二进制ABI/旧消费者/行为验证分离，保留真实退出码。 |
| `adk-context-compress-handoff` | core | 保留：自包含恢复摘要、raw指针、excluded及最多3动作保持。 |
| `adk-context-engineering` | core | 保留：stable/dynamic/evidence隔离、自包含交接与按需读取已覆盖。 |
| `adk-cross-team-handoff` | core | 保留：lite/formal、真实receiver签收及冷读验收完整。 |
| `adk-engineering-growth-review` | core | 保留：index-first、跨时点证据、不过度采集/外发，单次观察不代表长期能力。 |
| `adk-goal-authoring` | core | 保留：原验收分母、可关闭批次、预算null与bounded resume已有。 |
| `adk-interface-contract-design` | core | 保留：方向性版本/能力协商、生命周期/副作用与双向规格核对完整。 |
| `adk-knowledge-archive` | core | 保留：新归档/治理分离，topic/路径/来源/隐私边界完整。 |
| `adk-lightweight-planning` | core | 保留：只读计划按真实规模最小化，执行意图退出此skill。 |
| `adk-memory-curator` | core | 保留：report-only、授权读取、仅文件名敏感扫描及冲突治理清晰。 |
| `adk-parallel-agent-governance` | core | 保留：独立写集、data-only交接、summary-first与真实并行收益要求已有。 |
| `adk-pilot-framework` | core | 保留：smoke与收益比较、失败/blocked/inconclusive区分，保留重试。 |
| `adk-planning-execution-loop` | core | 保留：inline fast path、同快照复用、未知副作用对账和真实进展已有。 |
| `adk-production-field-readiness` | core | 保留：设备六类证据/OTA回滚/生产签署边界完整；多人human-active定义疑点无真实消费依据，OBSERVE。 |
| `adk-release-versioning` | core | 保留：正式baseline、完整历史、不可变tag与精确资产身份已有。 |
| `adk-repo-drift-remediation` | core | 保留：源事实issue-map、共享配置串行、只读状态与残留理由已有。 |
| `adk-repo-prompt-analysis` | core | 保留：实际callsite、role和动态输入信任边界完整，最小报告。 |
| `adk-requirements-triage` | core | 保留：brief/execution/high-risk分流，既有批准直接进入执行。 |
| `adk-runtime-router` | core | 保留：唯一primary、版本适配与optional真实加载边界完整。 |
| `adk-skill-deep-analysis` | core | 保留：有界source-discovery、固定来源、净增益与可实施handoff已有。 |
| `adk-structured-requirements-questioning` | core | 保留：Explore/Challenge、frontier、部分回答和依赖修订完整。 |
| `adk-systematic-debugging` | core | 改进：二分oracle分类和重跑前证据保全需补，其余因果/单变量/领域方法保留。 |
| `adk-task-breakdown` | core | 保留：纵向切片、expand/migrate/contract及Ready Frontier已有。 |
| `adk-token-context-governance` | core | 保留：真实trace优先、raw回退，源码字节不冒充Token收益。 |
| `adk-verification-before-completion` | core | 保留：checkpoint/goal-final、checker校准、实际运行与资格边界已覆盖。 |
| `adk-worktree-governance` | core | 保留：上一轮Git只读取证已修，保留dirty保护与独立清理授权。 |
| `adk-bsp-analysis` | embedded | 保留：保留：按问题展开的初始化/资源链、权威章节、历史workaround与confirmed/inferred/unknown分离。 |
| `adk-bsp-porting-playbook` | embedded | 保留：保留：目标ABI、独立输出目录、Kbuild实际参数、资源预算及设备handoff完整。 |
| `adk-cmake-cross-build` | embedded | 保留：保留：真实preset/binaryDir/config、JUnit执行状态、零/全skip、资源预算和工具链匹配已有真实测试。 |
| `adk-driver-bringup-checklist` | embedded | 保留：保留：分阶段验收、主动探测/读副作用、异常恢复、not-run与未授权设备写边界。 |
| `adk-driver-implementation` | embedded | 保留：保留：runtime-specific生命周期、IRQ/DMA引用、partial init/cancel/late completion与资源所有权足够明确。 |
| `adk-embedded-debug-transport` | embedded | 保留：保留：已区分被动/主动/状态改变/破坏性通道，含GDB暂停与MMIO读取副作用。 |
| `adk-embedded-diagnostic-harness` | embedded | 保留：保留：expected/harness/product/environment区分，strict/env套件与实际CLI返回语义明确。 |
| `adk-embedded-release-orchestration` | embedded | 保留：保留：prepare/publish/device分权与多MCU部分成功恢复已有明确方法。 |
| `adk-embedded-remote-debug-log-triage` | embedded | 保留：保留：分层健康、输出语义、熔断、恢复后身份与HIL阶段覆盖；按问题加载详细参考。 |
| `adk-embedded-storage-layout-migration` | embedded | 保留：保留：文件系统问题分流、数据保护、host演练和独立operator写操作边界明确。 |
| `adk-fault-injection-recovery` | embedded | 保留：保留：按实际风险选择故障、隔离授权、恢复SLA、功能/数据一致性及有条件watchdog验证。 |
| `adk-hardware-debugging` | embedded | 保留：保留：目标ELF/地址归一化与MCU fault差异，保留实际板端边界。 |
| `adk-integration-hil-sil` | embedded | 保留：保留：实际runner身份、资源隔离、新鲜JUnit/必跑项、实际执行状态与设备后置健康要求。 |
| `adk-interrupt-dma-patterns` | embedded | 保留：保留：ownership、barrier、memory ordering与coherency分别要求；Linux官方coherent不保证顺序可作现有方法解释，未强行增改。 |
| `adk-offline-core-dump-triage` | embedded | 保留：保留：身份/库匹配与GDB提前关闭auto-load、有限可信帧及partial结论完整。 |
| `adk-performance-profiling-embedded` | embedded | 保留：保留：v11.3.8实际运行对象身份、栈边界、有效负载/工作点与不确定性已有执行证据。 |
| `adk-protocol-stack-integration` | embedded | 保留：保留：v11.3.8帧边界/部分IO/截断/缓冲限制/全程deadline与分层状态机已落实。 |
| `adk-register-map-design` | embedded | 保留：保留：v11.3.8已补复位条件/有效位/undefined和安全读取；未发现新执行缺口。 |
| `adk-rtos-task-design` | embedded | 改进：改进：保留现有RTA模型，补实际周期API/单位量化与范围、到点与超期区别、有界超期策略，以及共享timer服务与异步stop/delete生命周期。 |
| `adk-static-analysis-c-cpp` | embedded | 保留：保留：TU/头依赖、实际数据库、非空扫描、解析失败、警告升级与动态证据分层明确。 |
| `adk-test-strategy` | embedded | 保留：保留：风险分级、独立expected/变体、checker校准、资源隔离及真实回执覆盖充分。 |
| `adk-unit-test-embedded` | embedded | 保留：保留：独立oracle、有界状态序列、复位/回放、覆盖局限与host/target边界已具体化。 |
| `adk-data-fetch` | optional | 保留：独立安装父/子Skill、授权范围、缺子技能停止及partial/not-verified状态传递已经完整，未发现本轮可证新增缺口。 |
| `adk-email-imap-fetch` | optional | 保留：EXAMINE、UIDVALIDITY+UID、BODY.PEEK、重连重查和逐项partial已有明确约束；无需新增邮箱写权限。 |
| `adk-external-practice-absorption` | optional | 保留：已有source-only/scoped-adoption/portfolio-intake，来源pin与独立decision边界完整；继续任务不重复intake规则存在。 |
| `adk-fetch-url-content` | optional | 保留：重定向/IP、请求预算、真实内容类型、编码、相对链接/base语义、登录壳与截断状态均明确；不为研究增加爬虫或执行器。 |
| `adk-incident-rca-report` | optional | 改进：简短RCA与证据因果方法保留；时间线缺乏事件/采集时间与时区/时钟偏差的明确区分，有有限可执行设计案例。 |
| `adk-prose-revision` | optional | 保留：report/revise意图、事实与限定保真、原稿风格及无需修改路径完备，反例reference已清楚标记非模型实测。 |
| `adk-security-supply-chain` | optional | 保留：source-only/adoption/runtime分层、source-to-sink、扫描遗漏与许可边界已有具体步骤；未以第三方词频或星数添加新的检查层。 |
| `adk-skill-composition-governance` | optional | 改进：主流程/按需评测保留；生命周期Creation Gate模板10行无证据却预填pass，建议改为待验证默认状态。 |
| `adk-test-flakiness-triage` | optional | 保留：v11.3.8新增原生Condition/readiness/0值/取消与预算边界完整，样本统计和顺序污染限制明确；不重复改动。 |

## 可复核证据

- [覆盖汇总与逐项决定](evidence/portfolio-audit.json)。
- [通用 core 原始审查](evidence/core-audit.json)、[嵌入式原始审查](evidence/embedded-audit.json)、[optional 原始审查](evidence/optional-audit.json)。
- [固定外部来源及采用/拒绝](source-review.md)。测试与发布观察分别记录，审查覆盖不等于所有业务场景已有真实运行效果。
