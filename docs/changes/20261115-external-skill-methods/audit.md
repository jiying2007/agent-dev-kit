# 全部 65 项 Skill 的实际审查与处理决定

基线：`v11.3.3` / `5e0e83bcc127665de9a352e9eacfe9b092106cb2`。两组分别审查 39 与 26 个唯一 Skill，合计 **56 core + 9 optional，143 个唯一实际读取路径**；逐项路径、SHA256 与 Git blob 已对齐基线，身份和覆盖均无遗漏。

本轮决定为 **6 项直接方法增强、1 项条件性交接增强、58 项保留**。前两轮已有修复继续保留；保留项表示此次对照没有确认额外的方法缺口，不代表所有宿主或任务效果已认证。以下是审查与处理决定，实施/验证状态另见本变更的实际回执。

研究实际读取来自 **17 个原始仓库** 的 Skill、reference、脚本或规范材料，另以 10 项工具原始文档/代码交叉核查。正文全文与选读范围分别标明，未将目录发现计为文件精读；原仓库评测代码没有执行。

| Skill | 决定 | 具体依据 |
|---|---|---|
| `adk-runtime-router` | 保留 | 保留：可信 inventory、唯一 primary 与 installed/native-loaded 状态分开；不需新增路由层。 |
| `adk-context-engineering` | 保留 | 保留：稳定规则、动态状态和证据隔离，恢复核对已覆盖；不引入固定压缩比例。 |
| `adk-token-context-governance` | 保留 | 保留：先控工作量再测成本，原始证据可回溯；文档字节不当作 Token 收益。 |
| `adk-requirements-triage` | 保留 | 保留：brief/execution/high-risk 分流与避免重复提问已覆盖所检索需求方法。 |
| `adk-structured-requirements-questioning` | 保留 | 保留：Explore/Challenge、决策前沿、有界收敛和 prototype 权限分离已覆盖。 |
| `adk-repo-prompt-analysis` | 保留 | 保留：实际调用点、角色、信任边界与 source SHA 对照；源码推断不冒充运行结果。 |
| `adk-skill-deep-analysis` | 保留 | 保留：有界发现、核验来源与 method-only handoff；不靠 stars 或目录排名。 |
| `adk-lightweight-planning` | 保留 | 保留：只读最小计划、不强制固定任务数；现有计划可直接继续。 |
| `adk-task-breakdown` | 方法增强 | 改进 C1：纵向切片缺跨公共契约重构的条件性 expand→真实消费者迁移→contract 路径及提前删除反例。 |
| `adk-parallel-agent-governance` | 保留 | 保留：ownership、真实依赖前沿、共享写串行和最终整合已明确；不增加无价值 worker。 |
| `adk-worktree-governance` | 保留 | 保留：dirty preservation、条件性隔离、来源和清理授权；不为所有小任务建 worktree。 |
| `adk-context-compress-handoff` | 保留 | 保留：最新目标、排除项、raw pointer 与下一步已明确，交接不自动晋升 durable rule。 |
| `adk-interface-contract-design` | 保留 | 保持已有契约方法；新性质测试在 unit 引用公开契约，不再增加治理层。 |
| `adk-adr-writer` | 保留 | 保留：读者冷读、自审与独立核验已经吸收 doc-coauthoring 的有效机制。 |
| `adk-component-api-stability` | 保留 | 迁移顺序由 core 的 task-breakdown 补足；本 Skill 的 ABI 分流无需重复。 |
| `adk-register-map-design` | 保留 | 寄存器必须由对应硬件手册验证，不照搬通用 bit 操作模板。 |
| `adk-bsp-analysis` | 保留 | 外部 Zephyr 方法不应变成全平台默认；已有证据充分。 |
| `adk-goal-authoring` | 保留 | 保留：原验收分母、阶段/整体与 Goal 恢复状态已经前轮修复，不重复新增状态层。 |
| `adk-planning-execution-loop` | 保留 | 保留：checkpoint 对齐、冲突裁决、无增量停止及外部副作用对账已覆盖 HVE 类方法。 |
| `adk-driver-implementation` | 保留 | fail-at-N unwind 可用但未发现未覆盖的实质需求，保留而不凑增量。 |
| `adk-driver-bringup-checklist` | 保留 | 状态序列探索属于 host seam，不能由此跳过板级 bring-up。 |
| `adk-bsp-porting-playbook` | 保留 | 已有阶段证据和回退，不加入默认烧录或外部框架。 |
| `adk-rtos-task-design` | 保留 | 不重复 RTA 方法；本轮栈证据在 performance 单点补足。 |
| `adk-interrupt-dma-patterns` | 保留 | TSan host 结果不能证明 ISR/DMA 硬件同步；保持适用性边界。 |
| `adk-protocol-stack-integration` | 保留 | 不重复上一轮采集修正；parse/状态性质方法由 unit 按需提供。 |
| `adk-cmake-cross-build` | 保留 | 外部 .conf CONFIG_ 反例提醒不可照搬；构建流程无需泛化新增。 |
| `adk-code-simplification` | 保留 | 保留：public seam、调用者负担和行为不变优先于行数；未确认新的简化方法缺口。 |
| `adk-systematic-debugging` | 方法增强 | 新增自身 sanitizer reference，压缩重复说明以抵消全源预算。 |
| `adk-embedded-debug-transport` | 保留 | 不把调试连接当实际诊断或自动开放写权限。 |
| `adk-embedded-remote-debug-log-triage` | 保留 | 保留 runner/环境/product 分离；不启动 live capture。 |
| `adk-offline-core-dump-triage` | 保留 | sanitizer 是另一路动态证据，不冒充 core dump 分析。 |
| `adk-hardware-debugging` | 保留 | 没有新设备证据不改现有 Cortex-M/地址映射方法。 |
| `adk-performance-profiling-embedded` | 方法增强 | 增加逐函数 frame、dynamic qualifier、调用链/IRQ/port/单位及观测余量边界。 |
| `adk-test-strategy` | 方法增强 | 改进 C2/C3：已有 TDD 和 mock 边界，补独立 expected 及错误变体敏感性；新建/修改/可疑 checker 才校准。 |
| `adk-unit-test-embedded` | 方法增强 | 新增独立性质、有界合法/拒绝序列、状态重置、非空 reachability 与反例回放；不引入框架。 |
| `adk-integration-hil-sil` | 保留 | host 状态枚举不能升级为 HIL；不重复执行 gate。 |
| `adk-embedded-diagnostic-harness` | 保留 | 新示例沿用分类，不新增统一 runtime/checker。 |
| `adk-fault-injection-recovery` | 保留 | Linux fail-nth 为可用条件方法，但无工具/内核证据，不扩至设备。 |
| `adk-artifact-gating` | 保留 | 保留：PASS/READY 及阶段条件已经对齐真实工作流，不重复前轮修复。 |
| `adk-pilot-framework` | 保留 | 保留：smoke/comparative、error/blocked/inconclusive 分开，不把模拟或源码当真实模型效果。 |
| `adk-verification-before-completion` | 方法增强 | 改进 C3：现有退出码/raw pointer 不足以证明 checker 拒绝违规，补条件性阈值/完整性/执行失败校准及有效证据复用。 |
| `adk-code-review-loop` | 保留 | 保留：完整快照、调用点保护条件、Spec↔Code、coverage ledger 与误报核实已覆盖 Sentry/Addy 有效审查方法。 |
| `adk-repo-drift-remediation` | 保留 | 保留：先 issue map、共享写串行、保留用户 dirty 状态；无新增必要步骤。 |
| `adk-static-analysis-c-cpp` | 条件性交接 | 仅补动态 sanitizer 按 Skill 名条件交接和不可用边界，不混淆静态/动态证明或建立硬跨目录链接。 |
| `adk-commit-pr-quality-gate` | 保留 | 保留：message-only/高风险分流及限定证据复用已覆盖，不扩大无关 gate。 |
| `adk-release-versioning` | 保留 | 保留：完整 log/body、真实已验证基线与版本影响已前轮修复，不用最近 tag 猜测。 |
| `adk-production-field-readiness` | 保留 | 没有现场数据不新造 readiness pass。 |
| `adk-embedded-release-orchestration` | 保留 | 本轮 host 方法不改变 release/field 授权和真实回执。 |
| `adk-embedded-storage-layout-migration` | 保留 | 不把 UBIFS 只读/容量症状直接转成迁移任务。 |
| `adk-cross-team-handoff` | 保留 | 保留：冷读理解核验、pending/accepted 与真实收件回执分开；不凭发出就声称交接完成。 |
| `adk-branch-closeout` | 保留 | 保留：操作级授权、actual HEAD/checks、fresh main 与 cleanup 边界完整；不采纳自动分支删除。 |
| `adk-after-action-review` | 保留 | 保留：复盘和晋升分离、必须真实效果，不因外部流行实践就晋升规则。 |
| `adk-memory-curator` | 保留 | 保留：来源冲突、last_verified、raw pointer 及敏感信息边界已覆盖压缩/记忆核心方法。 |
| `adk-archive-governance` | 保留 | 保留：目标 schema/hash/supersedes 与保留依据完整；不任意删除归档。 |
| `adk-knowledge-archive` | 保留 | 保留：来源、权利、不确定性、真实新知识增量；不批量制造重复笔记。 |
| `adk-engineering-growth-review` | 保留 | 保留：index-first、明确跨项目范围、证据趋势不推断人格；不为优化添加模型评测。 |
| `adk-external-practice-absorption` | 保留 | 保留：collector/owner/implementer/verifier 分离，来源身份/许可/生命周期已有；不安装外部 Skill。 |
| `adk-data-fetch` | 保留 | 保留：父 wrapper 和独立安装的两个获取子技能边界清楚，不隐含邮箱权限。 |
| `adk-email-imap-fetch` | 保留 | 保留：EXAMINE、UIDVALIDITY+UID、BODY.PEEK、字节预算与 partial/error 已覆盖；未对真实邮箱运行。 |
| `adk-fetch-url-content` | 保留 | 保留：DNS/origin/redirect/private 拒绝、HTML/base/links 与 partial 明确；未用 Firecrawl 替换已够用路径。 |
| `adk-test-flakiness-triage` | 保留 | 保留：逐例真实报告、缺失/错误不得成功、有界样本和环境值保护已前轮加强；不宣称低概率统计置信。 |
| `adk-security-supply-chain` | 保留 | getsentry 原文和脚本仍有启发，但 ADK 已覆盖；不引入正则匹配即安全结论。 |
| `adk-prose-revision` | 保留 | 保留：report/revise、技术 literal 与限定语保护，不推断 AI 作者；未发现新缺口。 |
| `adk-incident-rca-report` | 保留 | 保留：事实/假设/因果分离、有证据才用 5 Whys；不虚构 owner 或时间。 |
| `adk-skill-composition-governance` | 保留 | 保留：canonical matcher、holdout、source/native/effect 边界与行为评估已经清楚；不引入外部 trigger/eval runner。 |

## 可核验证据

- `evidence/research-core.json`：39 项、88 条实际阅读路径、通用方法来源与拒绝理由。
- `evidence/research-domain.json`：26 项、55 条实际阅读路径、领域来源及官方纠偏依据。
- `evidence/research-root.json`：Vercel 与当前 OpenAI Plugins 的补充原文审查。
- `evidence/independent-source-review.md`：独立的规范、评测实现与新鲜度反例审查。
- `source-review.md`：面向阅读的来源对照与采纳方式。

这些材料证明此次审查覆盖和方法选择，不是模型行为实验、Token 或板端效果结果。没有安装外部 Skill、执行上游脚本或启动新的巡检。
