# 65 项 Skill 审查与落地

基线：`907080d5a0f6e49daa93e217f60383b23ed89d37` / 11.3.4。最终运行源码：`016d673331ef458ac94f72d08ec67537a000cc4b` / 11.3.5。

独立领域审查者读取了全部 **65 个 SKILL.md 与 53 个直接引用文件，共 118 个路径**。原始逐项身份和 SHA-256 见 [portfolio-audit.json](evidence/portfolio-audit.json)。该审查初判为 15 项 fix、50 项 retain；root 另依据独立问题来源改进结构化提问，最终实际修改 **16 个 Skill**。retain 表示本轮没有选出需要改动的具体缺口，不表示穷尽所有缺陷或取得模型效果认证。README、LICENSE、UI metadata 不计入上述完整阅读范围。

## 实际改进

- 同组提升复用主 Skill 的 non-trigger 和否定意图；显式名称拒绝涵盖 plain、backtick、$、@ 及有限组合，使用精确名称边界。正常提升及不同名称保持可选，拒绝不能变成授权。
- BSP 示例传递已确认架构、工具链、板级配置、image/可选 DT 和 jobs 预算，防止覆盖已有输出；接口示例验证明确兼容策略下的最低 2.1 与 ASYNC_CANCEL 能力，拒绝无条件降级。
- 结构化提问保留稳定 ID、问题原意和答案来源；部分回答不会填满未决项，上游修订使依赖决定失效。实际隔离对话观察保留原版本边界，未登记为模型 A/B。
- 分支收尾复用同目标/动作/范围且未撤销的可回读明确授权，保留现有检查和未覆盖动作边界。
- 13 个原本带 rtk 的入口/引用改为原工具命令，相关父 Skill 同步版本；ADK/llm_agent 命令注明核验源码根。真实导出的 Review 示例在只有 git、没有 rtk 或 ADK 的 PATH 执行成功。
- 任务比较绑定完整开始/结束时间与每个 task 的验收项组成；一次比较只加载验证合同一次，下一次重新验证文件和 schema。名字组成一致不证明 grader 语义一致。

## 源码体积

既有八个 Profile ratchet 全部通过，未调高任何上限。下表来自同一现有工具分别读取完整基线 Git tree 和候选 tree 的实际结果；字节不是 provider Token，按需 reference 不假定初始已加载。

| Profile | 入口文件字节 | 相对基线 | 全部潜在源码字节 | 相对基线 |
|---|---:|---:|---:|---:|
| core | 99537 | -1560 | 173362 | -487 |
| release-hardening | 84084 | -1556 | 156934 | -483 |
| personal-core | 114469 | -1399 | 192031 | -326 |
| embedded-fullstack | 212577 | -1073 | 316440 | 0 |
| team-core | 125003 | -1407 | 211197 | -334 |
| large-refactor | 215602 | -1073 | 323322 | 0 |
| incident-response | 30800 | -4 | 46556 | -4 |
| research-intake | 66708 | -1386 | 117692 | -432 |

## 全量覆盖映射

原审查判定与最终编辑决定分列，保留两者不同来源，不将后续修改反写成早期结论。条目完整原始读入路径、各文件基线摘要和具体 finding 见原始 JSON。

| Skill | 实读路径数 | 原审查判定 | 最终编辑 | 原审查理由 |
|---|---:|---|---|---|
| adk-data-fetch | 1 | retain | 保留 | 父 Skill 只选择已安装子 Skill，不隐式安装或扩展访问权限。 |
| adk-email-imap-fetch | 1 | retain | 保留 | 授权邮箱只读范围、凭据与输出最小化明确，不扩成发信或归档写操作。 |
| adk-fetch-url-content | 1 | retain | 保留 | 指定公开 URL 提取、访问限制和内网/登录边界明确，不把抓取工具当搜索器。 |
| adk-external-practice-absorption | 1 | fix | 已修改 | 来源到评估/pilot/退役闭环有效，公开工具示例隐式依赖 rtk。 |
| adk-incident-rca-report | 1 | retain | 保留 | 事故稳定后证据时间线、恢复与防复发路径明确，不伪造取证材料。 |
| adk-prose-revision | 2 | retain | 保留 | 表达最小修订与事实核验/作者鉴别分离，review cases 没有明显范围冲突。 |
| adk-security-supply-chain | 2 | retain | 保留 | 来源、权限及静态扫描覆盖限制明确，不把扫描通过当安全认证。 |
| adk-skill-composition-governance | 3 | retain | 保留 | 组合/路由/生命周期与行为评测引用保留，不新增第二路由权威。 |
| adk-test-flakiness-triage | 2 | retain | 保留 | 真实样本退出码、环境脱敏和重跑预算已有可执行验证，本轮保留。 |
| adk-adr-writer | 1 | retain | 保留 | 已有取舍、替代方案及决策后果路径；未发现本轮可复现功能缺口。 |
| adk-after-action-review | 4 | retain | 保留 | 复盘与交付前验证、知识候选发布分离，三个引用保留原始证据和审核边界。 |
| adk-archive-governance | 1 | fix | 已修改 | 元数据修复路径保留，但公开命令隐式依赖 rtk，导出后可直接 exit 127。 |
| adk-artifact-gating | 2 | retain | 保留 | 制品标签、状态、跨仓交接与发布资格区分清楚，入口和引用一致。 |
| adk-branch-closeout | 2 | fix | 已修改 | 引用禁止从任何 previous conversation 识别批准，与可追溯既有明确授权冲突，导致同范围重复询问。 |
| adk-bsp-analysis | 2 | retain | 保留 | 源码、硬件资料、历史 workaround 与证据化风险闭环完整，保留现有按需引用。 |
| adk-bsp-porting-playbook | 1 | fix | 已修改 | Linux 示例固定 arm64/aarch64、通用 defconfig 与 nproc 并行度，忽略已确认目标与资源预算。 |
| adk-cmake-cross-build | 1 | retain | 保留 | 已有真实工具链、配置隔离和 CPU/RAM 并行预算，不重复添加通用检查段落。 |
| adk-code-review-loop | 5 | fix | 已修改 | 独立审查、反馈复核和证据生命周期有效；两个引用命令隐式依赖 rtk。 |
| adk-code-simplification | 3 | retain | 保留 | 等价性基线、可观察行为和深模块引用已覆盖方法差异，本轮保留。 |
| adk-commit-pr-quality-gate | 2 | retain | 保留 | 提交前证据、独立 review 与受保护合并边界明确，本轮保留。 |
| adk-component-api-stability | 1 | retain | 保留 | 调用方清单、兼容矩阵与迁移回退路径有效，不扩成新的接口框架。 |
| adk-context-compress-handoff | 1 | retain | 保留 | 交接保留来源、未完成事项与下一动作，不将摘要作为高风险原始证据。 |
| adk-context-engineering | 1 | retain | 保留 | 稳定规则、按需引用与并行隔离明确，没有发现需新增上下文层的证据。 |
| adk-cross-team-handoff | 1 | retain | 保留 | 责任、接口、验收映射与外部动作边界明确，本轮保留。 |
| adk-driver-bringup-checklist | 1 | retain | 保留 | 时钟/复位/probe/中断的依赖排查与设备写入许可分离，本轮保留。 |
| adk-driver-implementation | 1 | retain | 保留 | 目标运行时、资源生命周期和定向回归覆盖具体驱动实现风险，本轮保留。 |
| adk-embedded-debug-transport | 1 | retain | 保留 | 调试连接证据与远程部署权限分开，不把连接成功当目标资格。 |
| adk-embedded-diagnostic-harness | 1 | fix | 已修改 | 退出码与证据语义有效，但示例隐式依赖 rtk，需可移植原工具命令。 |
| adk-embedded-release-orchestration | 2 | fix | 已修改 | 多 MCU OTA 恢复和制品准备门禁保留；公开示例隐式依赖 rtk。 |
| adk-embedded-remote-debug-log-triage | 2 | retain | 保留 | 先确认真实目标/连接/取证层次，ADB 引用对写入和 HIL 证据有单独边界。 |
| adk-embedded-storage-layout-migration | 1 | fix | 已修改 | 存储演练与真实写权限分离，但 host 示例隐式依赖 rtk。 |
| adk-engineering-growth-review | 2 | retain | 保留 | 授权历史、工程证据与个人属性推断有明确边界，不把单次观察外推成趋势。 |
| adk-fault-injection-recovery | 1 | retain | 保留 | 有界故障注入、隔离、恢复与重放证据明确，本轮保留。 |
| adk-goal-authoring | 2 | fix | 已修改 | Goal 原验收和闭合批次已有约束；内部管理示例隐式依赖 rtk。 |
| adk-hardware-debugging | 2 | retain | 保留 | 硬件假设、Linux 与 MCU 分支及 fault/reset/wakeup 证据明确，本轮保留。 |
| adk-integration-hil-sil | 1 | retain | 保留 | 真实 HIL/SIL 入口、设备授权与结果层次已有修复，不重复上轮内容。 |
| adk-interface-contract-design | 6 | fix | 已修改 | 示例只比较 major，未声明消费者最低 minor 能力；协商失败无条件降级缺少可用交集证据。 |
| adk-interrupt-dma-patterns | 3 | retain | 保留 | 缓存一致性、所有权、ISR/任务边界与诊断引用已经覆盖关键实现语义。 |
| adk-knowledge-archive | 1 | retain | 保留 | 新候选归档与既有元数据修复分工清楚，脱敏和原始证据指针保留。 |
| adk-lightweight-planning | 1 | retain | 保留 | 只读方案与已批准执行互斥清楚，无需重新开启审批或创建执行资产。 |
| adk-memory-curator | 1 | fix | 已修改 | 候选记忆与正式发布边界有效，现有命令示例隐式依赖 rtk。 |
| adk-offline-core-dump-triage | 1 | retain | 保留 | binary/BuildID/符号身份及离线证据限定明确，不虚构可置信堆栈。 |
| adk-parallel-agent-governance | 3 | retain | 保留 | 任务写集、共享契约和最终集成责任明确，两个引用保留可审核委派信息。 |
| adk-performance-profiling-embedded | 2 | retain | 保留 | 上轮已补 call-chain 栈上界方法与测量证据，本轮不重复修改。 |
| adk-pilot-framework | 2 | retain | 保留 | 有界试跑与正式产品认证分开，保留失败与回退判定。 |
| adk-planning-execution-loop | 2 | fix | 已修改 | 已批准计划的恢复与持续执行路径有效；源码管理示例隐式依赖 rtk。 |
| adk-production-field-readiness | 2 | retain | 保留 | 产测/OTA/现场维护与 pilot 证据层级明确，不从桌面测试推导量产就绪。 |
| adk-protocol-stack-integration | 1 | retain | 保留 | 跨层状态、错误、恢复与协议集成回归覆盖现有范围，本轮保留。 |
| adk-register-map-design | 1 | retain | 保留 | 位域访问权限、硬件来源与真实设备写入分离，本轮未选取需泛化规则修改的证据。 |
| adk-release-versioning | 2 | retain | 保留 | 历史枚举示例已有真实命令回归，不按提交类型过滤丢失变更，本轮保留。 |
| adk-repo-drift-remediation | 1 | fix | 已修改 | 基线与漂移取证路径有效，但命令隐式依赖 rtk 且源仓内部脚本需限定上下文。 |
| adk-repo-prompt-analysis | 1 | retain | 保留 | 不可信参考仓提示作为分析数据，保留来源而不执行外部脚本。 |
| adk-requirements-triage | 3 | retain | 保留 | 已有明确任务不重开访谈，嵌入式与探索性 brief 按需分支有效。 |
| adk-rtos-task-design | 1 | retain | 保留 | 任务时序、优先级、同步与实时性测量要求明确，本轮保留。 |
| adk-runtime-router | 2 | retain | 保留 | 入口策略保留；父任务独立发现并处理 matcher 同组提升实现缺口，本审查不重复裁决。 |
| adk-skill-deep-analysis | 2 | retain | 保留 | 只读发现、来源验证和有界可迁移价值分析有效，不把目录收录当质量证明。 |
| adk-static-analysis-c-cpp | 1 | retain | 保留 | 上轮已补静态到动态反例闭环，本轮不重复 sanitizer 方法。 |
| adk-structured-requirements-questioning | 2 | retain | 已修改 | 父任务单独处理部分回答/问题身份/上游修订缺口，本领域审查保留并转交该写集。 |
| adk-systematic-debugging | 4 | fix | 已修改 | 上轮 sanitizer/单变量反馈方法保留；入口命令隐式依赖 rtk。 |
| adk-task-breakdown | 3 | retain | 保留 | 上轮 expand/migrate/contract 和纵切拆分已覆盖，本轮保留有效方法。 |
| adk-test-strategy | 2 | retain | 保留 | 上轮独立期望值与检查器校准已覆盖，不将结构校验当真实效果认证。 |
| adk-token-context-governance | 1 | retain | 保留 | 原始证据回退与 Token 预算门禁明确，本轮未发现需放宽门禁的依据。 |
| adk-unit-test-embedded | 3 | retain | 保留 | 上轮性质/状态序列与独立断言方法已补齐，不能用 host 结果替代 HIL 资格。 |
| adk-verification-before-completion | 2 | fix | 已修改 | 完成证据的身份与时效约束有效；详细引用中源码测试命令隐式依赖 rtk。 |
| adk-worktree-governance | 3 | retain | 保留 | 隔离基线、provenance 与脏工作树保护及两处引用一致，本轮保留。 |

## 边界

本轮没有新建 Skill、第二套路由或运行时，没有复制第三方安装器。外部具体文件版本与拒绝理由见 [source-review.md](source-review.md)。真实 kernel 交叉编译、板级启动、模型效果、provider Token/费用、native host 初始加载均未测量。有限身份/否定匹配也不构成完整自然语言或授权理解。最终全量、独立审查与平台发布的实际状态分别见验证与平台记录。
