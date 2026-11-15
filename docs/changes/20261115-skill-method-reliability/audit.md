# 全部 65 项 Skill 深审与处理决定

本轮实施基线为 `1282c78b145afca670cf8e5733d80bd3c61f5cfb`（11.3.2，PR #267）。两组初审分别读取原本地候选 `092abfed…` / `597e1ddb…`；逐路径核验表明这些实际读取的 Skill 与消费者内容同合并基线一致。保留原读取身份，不改写历史执行 SHA。

覆盖 56 core + 9 optional，共 65 个唯一身份：**8 项方法修复、2 项共享消费者实现修复、55 项保留**。保留表示本轮没有确认需要修改的具体缺陷，不表示全平台运行认证。前序 catalog 的全部 65 项检索改进继续保留。

- [领域 23 项实际阅读与决定](evidence/coverage-domain.json)
- [任务与可选 42 项实际阅读与决定](evidence/coverage-task.json)

以下按 Manifest 顺序列出本轮决定；原 JSON 保存实际读取的正文、references、README 与相关消费者路径。

| Skill | 决定 | 具体依据 |
|---|---|---|
| `adk-runtime-router` | 保留 | 唯一primary、可信inventory和fit检查明确；未以micro标签创建低风险执行权限。 |
| `adk-context-engineering` | 保留 | 稳定规则与动态证据分开，按需回读raw pointer，恢复信息边界完整。 |
| `adk-token-context-governance` | 保留 | 压缩保留高风险原文回退，ADK源码检查已有适用范围，不把字节数当Token实测。 |
| `adk-requirements-triage` | 保留 | brief、execution-handoff和high-risk分流避免重复访谈，已有明确任务交还实施。 |
| `adk-structured-requirements-questioning` | 保留 | Explore/Challenge按决策依赖推进，明确退出条件和只读探索边界。 |
| `adk-repo-prompt-analysis` | 保留 | 结论追实际调用点、角色和动态输入，不从description推断实现或执行外部脚本。 |
| `adk-skill-deep-analysis` | 保留 | 有界发现与只读方法对照保留来源、反例和实施交接，未知效果不冒充实测。 |
| `adk-lightweight-planning` | 保留 | 只读计划按实际行动规模裁剪，直接实施请求退出，不强制无用步骤。 |
| `adk-task-breakdown` | 保留 | 单切片、多切片和机器派工区分，真实依赖/共享文件决定并行边界。 |
| `adk-parallel-agent-governance` | 保留 | 收益准入、单写者、最小工作包与最终整合均明确，不用子任务成功替代目标。 |
| `adk-worktree-governance` | 保留 | 明确stay-current与隔离条件，保护dirty状态并保留创建/清理授权来源。 |
| `adk-context-compress-handoff` | 保留 | 摘要保留最新目标、排除项、原证据和最多三个下一动作，不提升为长期事实。 |
| `adk-interface-contract-design` | 方法修复 | 已复现rg输出文件名前缀导致跨头文件相同错误码漏检，改为有边界的字面值候选扫描。 |
| `adk-adr-writer` | 保留 | 按风险记录真实取舍，reader-only检查不伪造独立核验，定向修改保留事实。 |
| `adk-component-api-stability` | 保留 | 已分别验证源码 API、旧消费者原字节 ABI 与行为，工具错误和缺类型信息不会作为兼容通过。 |
| `adk-register-map-design` | 保留 | W1C/read-clear/FIFO 与 reserved 位避免盲目 RMW，并绑定访问宽度、字节序与手册版本；无确认的新缺陷。 |
| `adk-bsp-analysis` | 保留 | 已区分 Linux/RTOS/裸机入口，并以源码、硬件章节和历史证据串联资源依赖；本轮无确认的新方法缺陷。 |
| `adk-goal-authoring` | 共享实现修复 | 公开resume拒绝的过长/重复状态列表曾被state-check接受，共享字段约束并保留原reason。 |
| `adk-planning-execution-loop` | 共享实现修复 | 其公开state-check入口现在采用恢复同一字段边界，避免成功预检后无法恢复。 |
| `adk-driver-implementation` | 保留 | 覆盖 partial init、资源回收、IRQ/DMA ownership、cancel/reset 与 late completion；本轮未确认具体实现反例。 |
| `adk-driver-bringup-checklist` | 保留 | 已有 minimal/functional/soak 分层、主动探测与 MMIO 读副作用判定，未把最小 bring-up 冒充量产验证。 |
| `adk-bsp-porting-playbook` | 保留 | 启动链分层、目标制品身份、最小启动验证与恢复路径已有明确顺序；未确认需改的新反例。 |
| `adk-rtos-task-design` | 保留 | 复核已修的固定优先级响应时间递推、阻塞/IRQ 干扰项及适用前提；未将 trace 样本等同 WCET 上界。 |
| `adk-interrupt-dma-patterns` | 保留 | ISR API 优先级、CPU/device 所有权、cache-line/方向及取消迟到完成已有区分；本轮未得额外可复现缺陷。 |
| `adk-protocol-stack-integration` | 方法修复 | 真实 TShark 证明原 -q 示例成功却无分析输出；改为有帧输出的离线过滤，零目标证据标 partial，主动采集有界且失败不消费旧文件。 |
| `adk-cmake-cross-build` | 方法修复 | 真实 CTest 反例证明空/全禁用/筛空原命令退出 0；修正为空集失败并保留目标执行后端和 skip 边界。 |
| `adk-code-simplification` | 保留 | 现有简化示例已保留后续cleanup，真实行为基线与调用负担替代行数判断。 |
| `adk-systematic-debugging` | 保留 | 最小可失败信号、单变量因果与停止条件完整，不强制凑Why层数或无关反例。 |
| `adk-embedded-debug-transport` | 保留 | 连接与根因分析边界分开，attach/halt/continue 和 MMIO 读副作用未被误归为被动观察。 |
| `adk-embedded-remote-debug-log-triage` | 保留 | 分层连通性、ADB 语义确认、失联后停止扩大及恢复重做 preflight 已形成具体流程；本轮无新增机制反例。 |
| `adk-offline-core-dump-triage` | 保留 | 已有 binary/libs/BuildID 关联、指定 GDB 和先设 sysroot 的 batch 顺序；缺符号与映射保持 partial。 |
| `adk-hardware-debugging` | 方法修复 | 直接对 runtime PC 使用 vmlinux 地址查询缺少所属和重定位前提；改为先核内核/模块/段，再选 ELF 和可信地址映射。 |
| `adk-performance-profiling-embedded` | 保留 | 已分开瓶颈诊断与候选比较、真实活动负载和各 KPI 口径，KWS 划分/阈值及 host/板端证据限制明确。 |
| `adk-test-strategy` | 保留 | 已区分只读策略和授权实施，测试层级与实际风险匹配，保留真实red/green和资源隔离。 |
| `adk-unit-test-embedded` | 保留 | 已区分设计清单与实际测试交付，使用公开可观察 seam 并保留 host/compile-only/SIL/HIL 多层组合限制。 |
| `adk-integration-hil-sil` | 方法修复 | 修复真实 CTest 的空集成功，统一发现/运行配置与筛选，同时保留 host/SIL/HIL、skip/not-run 和最终健康边界。 |
| `adk-embedded-diagnostic-harness` | 保留 | 按 expected code/invoke_ret 与前置条件判断，区分 harness、产品和环境失败，不一概把非零设备码当失败。 |
| `adk-fault-injection-recovery` | 保留 | 故障类型按项目风险选择，watchdog 验证条件化，检测/恢复时延和恢复后功能检查未被省略。 |
| `adk-artifact-gating` | 方法修复 | 主文approved状态无法通过现有workflow的PASS门禁，统一现有状态语义与模板必需字段。 |
| `adk-pilot-framework` | 保留 | 现有smoke/收益比较与任务产物验收已分离，环境阻塞不等于能力失败。 |
| `adk-verification-before-completion` | 保留 | checkpoint与goal-final按适用风险分开，同快照证据及未验证边界明确。 |
| `adk-code-review-loop` | 保留 | feedback/targeted/whole-diff分流、真实快照和独立性保留，未把局部复核当整体通过。 |
| `adk-repo-drift-remediation` | 保留 | 问题地图和源事实先于治理修复，用户改动保护及共享触点串行规则保持。 |
| `adk-static-analysis-c-cpp` | 保留 | 已按实际 compilation database 选择 TU 和头文件消费者，空库/解析失败不会作为零告警成功，未重复上轮修复。 |
| `adk-commit-pr-quality-gate` | 保留 | message-only与PR/high-risk分流，复用适用回执而不重复无关验证。 |
| `adk-release-versioning` | 方法修复 | 真实Git复现历史漏项、首发吞错及非发布tag误选；显式基线/首发并保留完整hash与正文。 |
| `adk-production-field-readiness` | 保留 | 现场 readiness 要真实烧录/boot/产测/OTA/回滚材料，生产率试点又单列基线和时间口径；本轮未确认新方法错误。 |
| `adk-embedded-release-orchestration` | 保留 | prepare/publish/device-deploy 与多 MCU 部分成功恢复已分开，逐组件身份/健康/回滚证据清楚；无新确认缺陷。 |
| `adk-embedded-storage-layout-migration` | 保留 | 已有分区保留策略、配置/产物/运行态对齐、host dry-run 与真实迁移回执分离；未发现新确认缺陷。 |
| `adk-cross-team-handoff` | 保留 | lite/formal与pending/accepted界限明确，文档完成不推断实际签收或权限转移。 |
| `adk-branch-closeout` | 保留 | 只执行请求的收尾操作，远端未知先对账，合并后fresh-main与清理边界明确。 |
| `adk-after-action-review` | 保留 | 普通复盘与晋级分离，没有复用价值可无候选，不制造降本或因果证据。 |
| `adk-memory-curator` | 保留 | 只读候选整理、冲突与晋级审查明确，secret检索仅列文件名且说明覆盖限制。 |
| `adk-archive-governance` | 保留 | 已有归档的meta/topic/hash修复遵循目标检查入口，不擅自删除历史或提升全局规则。 |
| `adk-knowledge-archive` | 保留 | 新归档保留来源和适用边界，未知路径阻塞、不虚构验证或提升长期指导。 |
| `adk-engineering-growth-review` | 保留 | index-first和明确跨项目授权限制读取，趋势需跨时点证据，不凑训练建议。 |
| `adk-external-practice-absorption` | 保留 | 来源、独立owner决策、实施与验证角色分开；已批准续做不重启intake。 |
| `adk-data-fetch` | 保留 | 父项与两个可选子项独立安装，明确来源/权限与缺失拒绝，未假定父项隐式安装子项。 |
| `adk-email-imap-fetch` | 保留 | 当前方法已限定EXAMINE、UIDVALIDITY/UID与BODY.PEEK，部分结果和逐封错误不会伪作完整获取。 |
| `adk-fetch-url-content` | 保留 | 当前方法已限制origin/重定向/IP，提取保留链接语义并区分空壳、截断和完整结果。 |
| `adk-test-flakiness-triage` | 方法修复 | 真实原命令误算失败、吞退出码且输出合成凭据值；改为真实逐轮证据、原退出码及仅变量名。 |
| `adk-security-supply-chain` | 保留 | source-only/adoption/runtime分层，覆盖、误报和拒绝路径明确；静态零命中不被当作安全认证。 |
| `adk-prose-revision` | 保留 | report/revise按请求分流，保留技术字面量与事实，不据文风判断作者身份或强造改动。 |
| `adk-incident-rca-report` | 保留 | 已区分事实、已证因果和未决假设，5-Why按需且不虚构责任或恢复证据。 |
| `adk-skill-composition-governance` | 保留 | 沿用canonical matcher，source-contract与真实行为评测分开，不新增第二路由权威。 |

## 已证范围与保留边界

真实工具复现使用隔离 CMake/CTest、TShark 离线自造 PCAP、GCC/addr2line 与 Linux helper 的 host ELF，以及临时 Git、进程和 workflow 消费者夹具。测试明确区分执行失败、空集、运行时 skip、零匹配、缺失映射与完整结果；不把退出 0 一概解释为任务成功。

本轮没有真实模型 A/B、native Skill loading、设备/内核/HIL、实时网络抓包、邮箱或付费模型调用。模型成功率、Token、费用和端到端时延收益保持未测量；静态源体量及既有 profile 阈值单列，不能代替运行测量。E1 路由仍不可达，既有身份、安装选择与权限边界不改变。
