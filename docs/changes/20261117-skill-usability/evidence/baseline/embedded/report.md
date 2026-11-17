# Embedded 20 Skill 独立只读审查

## 冻结边界与结论

- 源码：`/workspace/scratch/fe8de3b42084/adk-skill-usability`，HEAD `78c3be7f6f9b5ee2e557de54156532fb3169198d`（v11.3.13）。
- 审查时间：2026-11-17 UTC；外部原始资料核对至 06:22 UTC。
- 角色：独立只读审查；未修改仓库文件，未提交、推送、操作真实设备或启动 Agent runtime。
- 范围：`groups.json:groups.embedded` 的全部 20 项；完整阅读 20 份 SKILL.md、全部 10 份随包 references、4 份 README 和 4 份 OpenAI UI metadata。读取根 AGENTS.md、docs/agent-operating-rules.md、README、相关 Manifest/调用/导出与测试实现。未读取其他审查者结论。
- 冻结 4 项可实现问题：1 项 RTOS 分析适用条件缺失、3 项确定性调用边界缺陷。未将本轮静态/host 证据称为原生 Skill 使用成功或板端认证。
- 两目标离线导出均保留本组 20/20 正文及 10/10 references；39 项定向现有测试通过，0 skip、0 failure、0 error。
- 20 项首个声明触发/排除短语的隔离 matcher 检查全部符合当前声明；另选 20 个真实任务表达，18 个选中预期 Skill，BSP 与“实现 RTOS SPI 驱动”两项 abstain。这不是随机样本，不作总体路由准确率。

所有 raw/中间结果位于本目录：`routes.json`、`rta.json`、`exports.json`、`tests.json`、`targeted-tests.log`。`coverage.json` 提供逐项结构化覆盖。复现入口为 `audit_repro.py`。

## F-EMB-01 / P2 — RTA 的适用条件遗漏互异优先级

**位置与片段**：`skills/adk-rtos-task-design/SKILL.md:33–38`。第 33 行列出单核、抢占式、固定优先级、周期/有界 sporadic、deadline ≤ period、无未建模 jitter/自挂起；第 36 行仅对 `j in higher-priority tasks` 求和。未排除同优先级任务，第 38 行据收敛和 `R <= deadline` 给出模型内可调度结论。

**实际任务**：审查采用 FreeRTOS 默认固定优先级抢占、同优先级时间片调度的两个周期任务。二者均 `priority=2, C=6, T=D=10`，同步释放，无共享资源/IRQ 干扰，故 `B=I=0`。这符合主文列出的条件。

**可复现反例**：按公布递推式逐项计算，两个任务的 higher-priority 集合均为空，均得到 `6 → 6`、`R=6 <= D=10`。但单核在共同 deadline 前仅有 10 单位 CPU 时间，两个作业需 12 单位；即使理想零调度开销也不可调度。`rta.json` 保存计算结果和独立的容量反证。该脚本是公式的 host 算术转写，不是 FreeRTOS 仿真或真机测量。

**正向对照**：互异优先级的 `A: C=2,T=D=10,priority=2` 与 `B: C=3,T=D=10,priority=1`，得到 `R_A=2`、`R_B:3→5→5`。这保留现有模型的合法使用。

**原始依据**：主文自己引用的 Davis/Burns 2008 §2 明确每个任务分配唯一优先级；FreeRTOS 官方调度文档明确默认对相同优先级任务轮转。相关 URL 和核对时间见后文资料记录。数学反证独立于该实现细节。

**为何现有测试未发现**：`tests/test_skill_governance.py:217–226` 仅检查 `response-time`、`ISR interference` 等文本；`tests/test_skill_rtos_methods.py:63–104` 只执行 tick 转换/范围与两个变异反例。没有检查 RTA 的同优先级适用边界。全部现有定向测试通过不能否定本问题。

**最小修复**：在现有适用条件明确“固定且互异的任务优先级”；把同优先级 FIFO/时间片列入另选模型或补充分析的情形。无需新增计算器、Skill 或 Gate，不要求把合法同优先级系统一律改成不同优先级。

**验收**：

1. 互异优先级正向对照及现有 `Ci=2,Bi=1,Di=5` 示例仍可计算。
2. 相同优先级 `C=6+6,T=D=10` 不得依据当前 hp-only 公式宣称可调度；须指出模型不适用，并可用 12>10 反证。
3. 相同优先级但可调度的任务组也须使用相应模型，不把“当前式不适用”偷换成“必不满足 deadline”。
4. 保留 WCET 上界、IRQ/开销不重复计数和 host/板测区别。

## F-EMB-02 / P2 — RTOS 的宽泛触发词越过声明领域

**位置与片段**：`skills/adk-rtos-task-design/SKILL.md:6–13`。`任务设计`、`实时任务`、`调度分析` 均为无领域条件的触发词；排除词仅有较长的 `无 RTOS 的裸机项目` 与 `普通线程划分且无实时约束`。本 Skill 没有使用已存在的 `implicit_context` 机制。

**可复现任务**：

| 输入 | 当前生产 matcher 结果 | 合理边界 |
|---|---|---|
| `请做一个季度销售团队任务设计。` | `adk-rtos-task-design`，`source=skill_trigger` | 不选择 RTOS 专项 |
| `项目没有 RTOS；请评估裸机主循环任务设计。` | 同上 | 明示无 RTOS，应排除 |
| `请设计 RTOS 任务优先级、周期和共享资源。` | `adk-rtos-task-design`，`source=routing` | 应继续匹配 |

`routes.json` 中 `rtos-*` 保存完整结果。本结论只证明 ADK 确定性 matcher 的错误选择，没有测量下游模型是否实际加载正文。错误选择会把专用调度流程推荐给适用范围之外的任务；不能据此声称已测得 token 损耗。

**为何现有测试未发现**：`tests/test_skill_trigger_matrix.py:397–436` 的全量检查采用每项首个正/负短语，RTOS 首个正例已含 `RTOS任务`，负例又是 metadata 原文。`tests/test_boundary_conditions_match.sh:219–223` 的正常 RTOS 正例不能覆盖通用任务与自然否定表达。隐式领域检查已有单元测试，但目前只由主动声明该字段的 Skill 使用。

**最小修复**：在本 Skill 上收窄通用触发词或使用现有 `implicit_context`；同时让 `无 RTOS/没有 RTOS` 的自然表达明确排除。用最短可行 metadata 改写，不复制全局 matcher，不增设流程/审批。

**验收**：上述两条负例不选 RTOS；RTOS/FreeRTOS 周期与调度正例继续选中；显式单 Skill 诊断、其他 Skill 的隐式上下文语义不发生无关变化。

## F-EMB-03 / P2 — 仓内 BSP 正向调用用例实际无法选择 BSP analysis

**位置与片段**：

- `skills/adk-bsp-analysis/SKILL.md:6–11` 只提供 `BSP 分析`、`BSP 代码梳理` 等相邻短语。
- `manifest.json:routing.intents` 没有 BSP analysis 专用 intent（有 BSP porting）。
- `tests/fixtures/content-architecture/routing-authority-cases.json:5` 已把以下输入登记为 `bsp-analysis-positive`，期望 `adk-bsp-analysis`。

**现成任务 / 当前结果**：

```text
梳理这个 BSP 的启动、probe、clock/reset 依赖和历史 patch，不修改代码
→ match=false, decision=abstain, reason=needs-triage, task_mode=readonly
```

该输入正是 Skill 描述/Workflow 支持的源码结构、资源依赖、历史追踪任务。`routes.json:coverage[adk-bsp-analysis]` 保存生产 `match_text` 结果，不是模型推演。隔离输入 `BSP 分析` 可正常选中。

**为何现有测试未发现**：`scripts/check-content-architecture.py:227–240` 明确只结构性验证 fixture 的 case type、Skill 存在和 runtime role，不调用 matcher 执行 prompt；全量首短语检查也无法覆盖这一表达。这里不把 structural fixture 冒充旧测试失败，问题是已有意图用例没有接到可执行调用覆盖。

**最小修复**：由共享调用逻辑的单一集成作者给 BSP analysis 补有领域/行动含义的调用路径，并将现成 `bsp-analysis-positive` 作为实际 matcher 用例执行；不使用裸 `BSP` 抢占 BSP 移植、驱动实现或硬件联调。Skill 工作流本身无须扩写。

**验收**：现成 BSP prompt 选中 analysis，mutation 仍 deny；“BSP 移植/启动链迁移”仍选 porting；“实现 SPI 驱动”仍选 implementation；“先只读梳理 BSP，不改驱动”不能被当实现授权。

## F-EMB-04 / P2 — DMA 排除词内的斜杠生成错误的独立屏蔽短语

**位置与片段**：`skills/adk-interrupt-dma-patterns/SKILL.md:15–16`：

```yaml
non_triggers:
  - 轮询已经满足已量化 latency/CPU budget 的场景
```

`src/agent_dev_kit/_matcher_kernel.py:18–24,43–48` 将 `/` 分隔为备选短语；`356–369,563–568` 的 non-trigger 优先于正向路由。所以当前文字实际有两个独立屏蔽词，包括 `CPU budget 的场景`。

**可复现任务**：

```text
请检查 DMA 缓存一致性，这是受 CPU budget 的场景限制的系统。
→ 隔离 match=false, reason=matched_non_trigger, phrase=CPU budget 的场景
→ 自动 match=false, reason=needs-triage, negated_intents=[interrupt_dma_patterns]
```

`routes.json:boundaries[dma-budget-fragment]` 保存完整结果。另一反例是已满足 polling 预算但 DMA 数据仍旧的检查请求，亦被排除。CPU 预算是否达标不能替代 DMA ownership/cache 正确性；Linux 官方 DMA API 文档对 streaming buffer 的 CPU/device 同步要求不以 IRQ/轮询方式作为免责条件。

**为何现有测试未发现**：首条非触发短语本身按当前语义被拒绝就满足 `test_full_inventory_description_and_isolated_trigger_contract`；`test_realtime_skills_use_target_budgets_not_fixed_thresholds` 只验证目标预算/ownership 等文本。没有将“有效 DMA 任务 + non-trigger prose 内片段”组成交叉反例。

**最小修复**：替换这条宽泛排除词，限定到真正不涉及 IRQ/DMA 的纯轮询任务，避免 prose 使用被解释为备选分隔符的 `/`。不需改动全局斜杠语法，更不应全局降低 non-trigger 优先级。此修复可减少正文/metadata 字节。

**验收**：`dma-budget-fragment` 及满足轮询预算但需 DMA coherency 检查的请求选中本 Skill；不涉及 IRQ/DMA 的纯轮询请求仍不选中；现有 FromISR/DMA 旧数据与显式禁止使用该 Skill 的负例保持原结果。

## 20 项覆盖概览

所有行均已完整阅读正文，检查其 Manifest 注册/调用边界及两种导出。`无新增 finding` 仅表示本轮已完成的审查未得到可支持的新缺陷，不表示完整功能/硬件认证。

| Skill | 方法/可执行性重点 | 已执行额外证据 | 结论与剩余边界 |
|---|---|---|---|
| adk-register-map-design | SVD resetValue/resetMask、W1C、read side effects、unknown/undefined | 已公布 mask 表达式的真实 host C 测试 | 无新增 finding；未运行外部 SVD 生成器/MMIO |
| adk-bsp-analysis | Linux/RTOS/bare-metal 分支、按问题追调用/资源/历史；1 reference | 现成 BSP fixture 的生产 matcher 回放 | F-EMB-03；未提供实际产品 BSP 供追踪 |
| adk-driver-implementation | runtime-specific 生命周期、timeout/cancel/late completion、IRQ/DMA handoff | 隔离声明正负例与自然任务路由 | 生命周期未发现新缺陷；自然“实现 RTOS SPI 驱动” abstain 已留 raw，未扩大本批修复 |
| adk-driver-bringup-checklist | minimal/functional/soak 分段，主动探测与被动证据 | 路由/导出 | 无新增 finding；未连接设备，不称 bring-up 通过 |
| adk-bsp-porting-playbook | Kbuild identity、独立 output、ARCH/toolchain/jobs、配置/DT 入口 | 真 GNU make + 小型记录 fixture 运行原命令，成功与失败控制 | 无新增 finding；fixture 不是真实 BSP/交叉编译/启动 |
| adk-rtos-task-design | RTA、tick/overflow/wrap、DelayUntil、timer callback 生命周期 | tick host C 测试、RTA 算术反例与正向对照、领域负例 | F-EMB-01/02；无实时调度或板端证据 |
| adk-interrupt-dma-patterns | CPU/device ownership、direction/cache/barrier、teardown；2 references | DMA 预算/轮询与正例的生产/隔离 matcher 回放 | F-EMB-04；未执行 DMA/IRQ 实验 |
| adk-protocol-stack-integration | stream/datagram、partial I/O、bounded buffer、总 deadline/retry；1 reference | 路由/导出 | 无新增 finding；无 PCAP/协议实现，不伪造 tshark/链路结果 |
| adk-cmake-cross-build | cache 身份复用、preset/manual、compile-only 与 JUnit 资格 | 真 CMake/Ninja/CTest、身份变化与 fresh directory、skip/disabled/失败/空/旧报告控制 | 无新增 finding；host fixture 不证明目标 MCU 执行 |
| adk-embedded-debug-transport | 通道识别与效果分类，halt/attach/MMIO side effect；README/UI metadata | 路由/导出 | 无新增 finding；未探测 SSH/ADB/串口/探针 |
| adk-embedded-remote-debug-log-triage | 分层健康、breaker、artifact/HIL 分流；1 reference + README/UI metadata | 路由/导出；本地文本排除自然表达 probe 已存 raw | 未将该附带观察升级本批 finding；未进行远程取证 |
| adk-hardware-debugging | ELF/PC 所属、KASLR/module 映射、M0/M23 不套通用 fault；1 reference | 路由/导出 | 无新增 finding；无目标 oops/ELF/fault register 证据 |
| adk-performance-profiling-embedded | 有效负载、运行对象/dispatch、PMU 语义、.su/高水位；1 reference | Linux 自有进程的运行库/已删除映射控制，host GCC stack 示例 | 无新增 finding；没有候选优化收益/板端栈峰值结论 |
| adk-unit-test-embedded | observable contract、独立 oracle、state reset、test backend；2 references | 已公布 121 序列/426 步 FIFO 反例、回放与修复对照 | 无新增 finding；不把 host 枚举称 fuzz/HIL |
| adk-integration-hil-sil | host/SIL/HIL/qualification 分开，JUnit not-run/skip/disabled/required | 真实 CTest 报告采集及 skip 控制 | 无新增 finding；没有 rig/device/HIL 执行 |
| adk-embedded-diagnostic-harness | expected code/invoke_ret、strict/env 和产品/harness 缺陷区分；README/UI metadata | 路由/导出 | 无新增 finding；未知项目 CLI 仅是模板，没有执行虚构命令 |
| adk-fault-injection-recovery | 对照、命中观察、检测/恢复/资源与 SLA 分开 | GCC/ld malloc wrap host fixture，未命中/unknown/错误清理正反例 | 无新增 finding；没有设备故障注入/恢复时延资格 |
| adk-static-analysis-c-cpp | TU/header 消费者、compdb/target、诊断非零与动态证据界限 | 路由/导出；prototype 排除 probe 已存 raw | 未将该附带观察升级本批 finding；未运行目标 cppcheck/clang-tidy |
| adk-embedded-release-orchestration | prepare/publish/device 分界、多 MCU 部分成功恢复；1 reference + README/UI metadata | 路由/导出 | 无新增 finding；无真实签名/publish/flash/资格证据 |
| adk-embedded-storage-layout-migration | PEB/min-I/O/offset/LEB/volume 对齐、preserve/rollback、host vs device | 路由/导出 | 无新增 finding；无真实镜像/目标 geometry/迁移回执 |

## 最低验证集合与实施归属

1. RTOS 独有文件：改适用条件/metadata，扩展 `tests/test_skill_rtos_methods.py` 中必要的模型适用正反例；保留既有 tick 测试。RTA 测试应验证模型边界与数学反证，不镜像生产正文生成一个新计算器。
2. IRQ/DMA 独有文件：只替换错误 non-trigger。共享触发测试由单一集成作者加入两个 DMA 正例和真实纯轮询负例。
3. BSP 路由/共享 matcher/Manifest/触发测试：统一由集成作者负责；复用已存在的 BSP fixture，不修改此 fixture 来迎合当前 abstain。
4. 运行本报告四类定向回归及相关共享 routing/contract 测试；正文/metadata 变更后再次核两个目标的本组导出。若实现触及共享 matcher/Manifest，按仓规则由集成作者执行所需完整门禁。
5. 源 footprint 既有 ratchet 不放宽；优先原句替换和删除错误范围，不添加额外流程、Agent 或安全条款。

本次已跑的 39 项现有测试选择保存在 `tests.json`。不需要因为还有未提供的硬件、外部工具而扩展本次测试范围；这些限制只约束完成声明。

## 原始资料记录

| 来源 | 核对内容 | URL | 核对时间 |
|---|---|---|---|
| R. I. Davis / A. Burns, RTSS 2008，作者机构原始 PDF | §2 的单核固定优先级模型为每任务互异优先级；hp(i) 定义 | https://www.cs.york.ac.uk/rts/static/papers/R:Davis:2008a.pdf | 2026-11-17 06:22 UTC |
| FreeRTOS 官方文档源码 | 默认单核 fixed-priority/preemptive，对相同优先级 round-robin time slicing | https://github.com/FreeRTOS/FreeRTOS-Website-Content/blob/main/content/en-us/Documentation/02-Kernel/02-Kernel-features/01-Tasks-and-co-routines/04-Task-scheduling.md | 2026-11-17 06:22 UTC |
| Linux Kernel 官方 DMA API HOWTO | streaming DMA buffer 的 CPU/device 同步与 ownership；完成通知方式不替代同步 | https://docs.kernel.org/core-api/dma-api-howto.html | 2026-11-17 06:15–06:22 UTC |

首次通过 York 页面 PDF 链接抓取遇到重定向失败，随后直接打开 www 域原始 PDF 成功，已核读 §2；未将失败抓取当证据。所有技术结论限制在实际读到的资料与本地可重放反例。
