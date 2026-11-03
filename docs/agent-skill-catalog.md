# Agent and Skill Catalog

- source: manifest.json

## Agents

| Name | Description | Path |
|---|---|---|
| `requirements-analyst` | 需求澄清、验收标准和范围边界分析 | `agents/requirements-analyst/AGENTS.md` |
| `architecture-planner` | 架构方案、模块边界和技术决策规划 | `agents/architecture-planner/AGENTS.md` |
| `driver-engineer` | 驱动实现、bring-up 和底层联调 | `agents/driver-engineer/AGENTS.md` |
| `component-engineer` | 组件接口、模块实现和集成边界治理 | `agents/component-engineer/AGENTS.md` |
| `application-engineer` | 设备侧应用、上位机工具和业务逻辑实现 | `agents/application-engineer/AGENTS.md` |
| `build-release-engineer` | 构建、打包、版本发布和回滚链路 | `agents/build-release-engineer/AGENTS.md` |
| `test-validation-engineer` | 测试策略、验证证据和完成前门禁 | `agents/test-validation-engineer/AGENTS.md` |
| `performance-reliability-engineer` | 性能剖析、稳定性和可靠性风险治理 | `agents/performance-reliability-engineer/AGENTS.md` |
| `security-compliance-reviewer` | 安全、合规、凭据和供应链风险审查 | `agents/security-compliance-reviewer/AGENTS.md` |
| `code-review-governor` | 代码审查、反馈闭环和质量放行治理 | `agents/code-review-governor/AGENTS.md` |
| `bsp-analyst` | BSP 代码分析、架构梳理、历史追溯 | `agents/bsp-analyst/AGENTS.md` |
| `external-practice-curator` | 多来源外部实践的来源、重复、合规、安全和资产形态只读审查 | `agents/external-practice-curator/AGENTS.md` |
| `hardware-debugger` | 硬件故障定位、oops 分析和板级调试证据整理 | `agents/hardware-debugger/AGENTS.md` |

## Agent Contract Matrix

| Agent | Owns | Does Not Own | Handoff To | Default Skills | Quality Gate |
|---|---|---|---|---|---|
| `requirements-analyst` | 需求边界, 验收标准 | 代码实现, 发布操作 | architecture-planner, test-validation-engineer, code-review-governor | adk-requirements-triage, adk-task-breakdown | 目标、非目标、影响面、验收标准和风险必须可验证 |
| `architecture-planner` | 架构边界, 接口决策 | 直接编码, 发布签核 | component-engineer, driver-engineer, code-review-governor | adk-interface-contract-design, adk-adr-writer | 设计必须包含接口、兼容性、迁移和回退边界 |
| `driver-engineer` | 驱动实现, bring-up 证据 | 产品需求裁剪, 发布放行 | test-validation-engineer, code-review-governor | adk-driver-implementation, adk-driver-bringup-checklist, adk-systematic-debugging | 驱动变更必须绑定硬件约束、验证证据和回归路径 |
| `component-engineer` | 组件接口, 模块实现 | 需求验收口径, 发布版本策略 | test-validation-engineer, code-review-governor | adk-interface-contract-design, adk-component-api-stability | 组件变更必须保留 API 稳定性和集成验证证据 |
| `application-engineer` | 应用逻辑, 工具行为 | 架构最终裁决, 发布放行 | test-validation-engineer, code-review-governor | adk-systematic-debugging, adk-unit-test-embedded | 应用行为变更必须包含用户路径、错误路径和回归证据 |
| `build-release-engineer` | 构建打包, 发布回滚 | 需求变更, 安全风险豁免 | security-compliance-reviewer, performance-reliability-engineer | adk-release-versioning, adk-commit-pr-quality-gate | 发布必须绑定版本、制品、校验、回滚和放行证据 |
| `test-validation-engineer` | 测试策略, 验证证据 | 功能实现, 风险豁免 | code-review-governor, build-release-engineer | adk-test-strategy, adk-verification-before-completion | 完成结论必须与验证命令、退出码和证据路径一致 |
| `performance-reliability-engineer` | 性能分析, 可靠性风险 | 功能需求裁决, 安全签核 | build-release-engineer, code-review-governor | adk-performance-profiling-embedded, adk-fault-injection-recovery | 性能和可靠性结论必须包含基线、负载条件和对比证据 |
| `security-compliance-reviewer` | 安全审查, 供应链风险 | 功能实现, 发布执行 | build-release-engineer, code-review-governor | adk-static-analysis-c-cpp, adk-commit-pr-quality-gate | 高风险项必须修复、降级或显式记录风险接受 |
| `code-review-governor` | 审查分级, 放行判断 | 直接修复代码, 发布执行 | requirements-analyst, test-validation-engineer | adk-code-review-loop, adk-commit-pr-quality-gate | blocker 必须修复或明确风险接受后才能放行 |
| `bsp-analyst` | BSP 分析, 历史追溯 | 驱动实现, 发布放行 | driver-engineer, architecture-planner | adk-bsp-analysis, adk-bsp-porting-playbook | BSP 结论必须包含入口、依赖、风险和追溯证据 |
| `external-practice-curator` | 外部实践候选审查, 吸收决策材料 | 候选批准, 代码实现, 安装与发布 | requirements-analyst, architecture-planner, security-compliance-reviewer, test-validation-engineer, code-review-governor | adk-requirements-triage, adk-repo-prompt-analysis | 来源、负结果、不可迁移缺点和独立 owner handoff 必须完整，curator 不得自批 |
| `hardware-debugger` | 硬件故障定位, oops 分析 | 长期架构设计, 发布放行 | driver-engineer, test-validation-engineer | adk-hardware-debugging, adk-embedded-remote-debug-log-triage, adk-systematic-debugging | 硬件调试结论必须包含现象、假设、实验和证据 |

## Skills

| Order | Stage | Category | Activation | Pattern | Name | Description | First Trigger | Path |
|---:|---:|---|---|---|---|---|---|---|
| 10 | 10 | `routing` | primary | governance | `adk-runtime-router` | 用于任务开始前在可信 Skills 清单中选定唯一 primary、supporting 和回退路径；不用于已有明确任务包时重复路由或隐式授予执行权限。 | 技能路由 | `skills/adk-runtime-router/SKILL.md` |
| 10 | 20 | `routing` | primary | governance | `adk-context-engineering` | 用于上下文膨胀、跨会话恢复或并行 Agent 隔离时规划稳定规则、按需引用及证据指针；不用于直接替代任务计划、代码实现或 Token 配额门禁。 | 上下文工程 | `skills/adk-context-engineering/SKILL.md` |
| 10 | 30 | `routing` | primary | governance | `adk-token-context-governance` | 用于日志与上下文过长时设置 Token 预算、分层读取和原文回退门禁；不用于压缩掉高风险证据或放宽验证要求。 | 省 token | `skills/adk-token-context-governance/SKILL.md` |
| 20 | 10 | `intake` | primary | playbook | `adk-requirements-triage` | 用于需求不清时澄清目标、范围边界和可验证验收标准；已明确的开发任务无需重复访谈，也不用于代替实际实现。 | 需求不清楚 | `skills/adk-requirements-triage/SKILL.md` |
| 20 | 20 | `intake` | primary | inversion | `adk-structured-requirements-questioning` | 用于需求目标、术语和验收边界仍模糊时开展有序澄清；不用于明确的小范围实现、文档润色或重复询问已知条件。 | 帮我理清需求 | `skills/adk-structured-requirements-questioning/SKILL.md` |
| 20 | 30 | `intake` | primary | reviewer | `adk-repo-prompt-analysis` | 用于逆向审查参考仓 Agent Prompt 的约束、结构与上下文工程方法；不用于直接复制不可信指令或运行外部仓脚本。 | 分析子仓 prompt | `skills/adk-repo-prompt-analysis/SKILL.md` |
| 20 | 40 | `intake` | primary | reviewer | `adk-skill-deep-analysis` | 用于外部或本地 Skill 的设计意图、差异价值与可迁移方法评估；不用于未经来源审查直接安装或自动批准候选 Skill。 | 深度拆解 skill | `skills/adk-skill-deep-analysis/SKILL.md` |
| 30 | 10 | `planning` | primary | playbook | `adk-lightweight-planning` | 用于用户明确要求先给计划、尚不修改文件的只读编码方案；不用于已批准的长任务执行或自动开启外部写入。 | 给我一个计划 | `skills/adk-lightweight-planning/SKILL.md` |
| 30 | 15 | `planning` | primary | generator | `adk-goal-authoring` | 用于长期目标过大、Goal 不收敛时生成可验证的目标合同、有限批次和恢复入口；不用于已有计划的日常执行或自行设置宿主预算与权限。 | 生成Goal | `skills/adk-goal-authoring/SKILL.md` |
| 30 | 20 | `planning` | primary | playbook | `adk-task-breakdown` | 用于复杂需求拆解任务包、依赖关系及并行边界；单点小修无需拆包，也不用于替代已批准计划的持续执行。 | 拆解任务 | `skills/adk-task-breakdown/SKILL.md` |
| 30 | 25 | `planning` | primary | pipeline | `adk-planning-execution-loop` | 用于已批准的多阶段长任务计划执行、恢复检查点、有限重试与收口验证；不用于仅索要只读计划，也不自行扩大宿主预算或权限。 | 执行计划 | `skills/adk-planning-execution-loop/SKILL.md` |
| 30 | 30 | `planning` | primary | governance | `adk-parallel-agent-governance` | 用于多个 Agent 并行时划分 scope、共享契约、冲突矩阵和最终集成验证；不用于单点小改或擅自委派有额外权限的任务。 | 并行 agent | `skills/adk-parallel-agent-governance/SKILL.md` |
| 30 | 40 | `planning` | primary | governance | `adk-worktree-governance` | 用于 git worktree 并行开发前的隔离、基线锁定、同步与安全清理；不用于擅自删除脏工作树或替代多 Agent 任务拆分。 | worktree | `skills/adk-worktree-governance/SKILL.md` |
| 30 | 50 | `planning` | primary | generator | `adk-context-compress-handoff` | 用于长任务上下文压缩、跨会话恢复及交接时保存目标、证据指针和下一动作；不用于替代原始高风险证据或任务执行。 | 上下文压缩 | `skills/adk-context-compress-handoff/SKILL.md` |
| 40 | 10 | `design` | primary | generator | `adk-interface-contract-design` | 用于模块 API、协议消息及生命周期状态转换的接口契约设计与迁移评审；不用于需求未收敛时直接写实现或放行设备动作。 | 设计接口 | `skills/adk-interface-contract-design/SKILL.md` |
| 40 | 20 | `design` | primary | generator | `adk-adr-writer` | 用于架构方案已有明确权衡、需要记录决定与替代方案时生成 ADR；不用于在需求不明时直接替代需求澄清或执行代码修改。 | 写ADR | `skills/adk-adr-writer/SKILL.md` |
| 40 | 30 | `design` | primary | reviewer | `adk-component-api-stability` | 用于组件 API 演进时检查调用方、兼容边界、迁移与回滚证据；不用于未经设计直接大范围改签名或纯格式修改。 | API稳定性 | `skills/adk-component-api-stability/SKILL.md` |
| 40 | 40 | `design` | primary | generator | `adk-register-map-design` | 用于芯片寄存器映射、位域权限和驱动接口文档设计；不用于直接对真实寄存器写入或代替外设时序调试。 | 设计寄存器 | `skills/adk-register-map-design/SKILL.md` |
| 40 | 50 | `design` | primary | playbook | `adk-bsp-analysis` | 分析现有嵌入式 BSP 源码、启动/探测路径、clock/reset/pinctrl/IRQ/DMA 依赖、硬件参考和 patch 历史，形成证据化架构理解与迁移风险。用于 BSP 代码梳理、厂商实现追踪、SoC/board 差异和历史 workaround 分析；不用于直接实现新驱动或 live 板级故障隔离。 | BSP 分析 | `skills/adk-bsp-analysis/SKILL.md` |
| 50 | 10 | `implementation` | primary | playbook | `adk-driver-implementation` | 用于 Linux、RTOS 或裸机驱动代码实现、资源生命周期与定向回归；不用于仅做首板调试清单或未经授权的真实设备刷写。 | 驱动开发 | `skills/adk-driver-implementation/SKILL.md` |
| 50 | 20 | `implementation` | primary | playbook | `adk-driver-bringup-checklist` | 用于首板 bring-up 联调时核对驱动时钟、复位、probe、中断和外设依赖；不用于直接编写驱动代码或未经授权执行设备寄存器写操作。 | 驱动调试 | `skills/adk-driver-bringup-checklist/SKILL.md` |
| 50 | 30 | `implementation` | primary | playbook | `adk-bsp-porting-playbook` | 用于 BSP 移植涉及启动链、驱动依赖、构建环境和迁移风险时规划与验证；不用于未授权的设备刷写或纯源码阅读。 | BSP移植 | `skills/adk-bsp-porting-playbook/SKILL.md` |
| 50 | 40 | `implementation` | primary | playbook | `adk-rtos-task-design` | 用于 RTOS 任务优先级、时序约束、同步资源与调度风险设计；不用于纯裸机单循环程序或未经测量声称实时性达标。 | RTOS任务 | `skills/adk-rtos-task-design/SKILL.md` |
| 50 | 50 | `implementation` | primary | playbook | `adk-interrupt-dma-patterns` | 用于中断、DMA、缓存一致性、共享缓冲所有权的实现模式与实时性检查；不用于无中断参与的普通应用逻辑或免证据修改寄存器。 | 中断处理 | `skills/adk-interrupt-dma-patterns/SKILL.md` |
| 50 | 60 | `implementation` | primary | playbook | `adk-protocol-stack-integration` | 用于通信协议栈适配、连接状态机和跨层错误处理的集成设计与回归；不用于纯寄存器布局设计或仅修复孤立格式问题。 | 协议栈 | `skills/adk-protocol-stack-integration/SKILL.md` |
| 50 | 70 | `implementation` | primary | tool-wrapper | `adk-cmake-cross-build` | 用于嵌入式 CMake 工程的交叉编译、工具链配置与多目标构建排障；不用于无 CMake 的构建系统或直接设备部署。 | CMake | `skills/adk-cmake-cross-build/SKILL.md` |
| 50 | 80 | `implementation` | primary | reviewer | `adk-code-simplification` | 用于代码结构冗长且行为已被测试约束时做等价代码简化；不用于未建立行为基线的功能修改、性能调优或根因不明的错误。 | 代码太复杂 | `skills/adk-code-simplification/SKILL.md` |
| 60 | 10 | `debugging` | primary | playbook | `adk-systematic-debugging` | 用于根因不明的问题复现、单变量假设验证和确定性回归；不用于跳过取证直接猜测修复或替代性能基准实验。 | 调试 | `skills/adk-systematic-debugging/SKILL.md` |
| 60 | 20 | `debugging` | primary | tool-wrapper | `adk-embedded-debug-transport` | 用于管理串口、SSH、ADB、远程 GDB 等调试通道的连接与权限证据；不用于隐式远程部署、修改设备配置或替代故障根因分析。 | 调试通道 | `skills/adk-embedded-debug-transport/SKILL.md` |
| 60 | 30 | `debugging` | primary | playbook | `adk-embedded-remote-debug-log-triage` | 用于远程设备 SSH、ADB、串口与启动日志取证和分层连通性定位；不用于未授权远程写入、替代离线 core dump 解析或新驱动实现。 | 远程调试 | `skills/adk-embedded-remote-debug-log-triage/SKILL.md` |
| 60 | 40 | `debugging` | primary | playbook | `adk-offline-core-dump-triage` | 用于离线分析嵌入式 Linux core dump，并对 binary、BuildID、符号与 GDB 匹配留证；不用于无符号时编造可信 backtrace 或操作在线设备。 | core dump | `skills/adk-offline-core-dump-triage/SKILL.md` |
| 60 | 50 | `debugging` | primary | playbook | `adk-hardware-debugging` | 用于板级电源、时钟、复位和硬件异常的假设验证与证据定位；不用于把 Linux oops 直接归咎硬件或未经许可执行带风险的硬件操作。 | 硬件调试 | `skills/adk-hardware-debugging/SKILL.md` |
| 60 | 60 | `debugging` | primary | tool-wrapper | `adk-performance-profiling-embedded` | 用于有明确指标时对嵌入式真实负载做性能分析和可比较的 A/B 验证；无指标不启用，也不用于仅凭推测宣布性能改善。 | 性能分析 | `skills/adk-performance-profiling-embedded/SKILL.md` |
| 70 | 10 | `verification` | primary | playbook | `adk-test-strategy` | 用于定义跨模块测试策略、风险分级、行为覆盖和可复跑验证矩阵；不用于只生成嵌入式局部替身代码或代替真实执行结果。 | 测试策略 | `skills/adk-test-strategy/SKILL.md` |
| 70 | 20 | `verification` | primary | generator | `adk-unit-test-embedded` | 用于 MCU/RTOS 的单元测试断言、替身与外设边界模拟；非跨模块测试策略，也不用于直接证明真实 HIL 性能。 | 单元测试 | `skills/adk-unit-test-embedded/SKILL.md` |
| 70 | 30 | `verification` | primary | playbook | `adk-integration-hil-sil` | 用于软件在环与硬件在环的集成测试、场景配置与结果证据编排；不用于仅做单元测试或绕过真实设备操作授权。 | 集成测试 | `skills/adk-integration-hil-sil/SKILL.md` |
| 70 | 40 | `verification` | primary | tool-wrapper | `adk-embedded-diagnostic-harness` | 用于诊断 CLI、prog_tool、strict 套件及 HIL/SIL 证据的返回码和行为验证；不用于无许可的现场产测写入或直接放行量产。 | 诊断 harness | `skills/adk-embedded-diagnostic-harness/SKILL.md` |
| 70 | 50 | `verification` | primary | playbook | `adk-fault-injection-recovery` | 用于已授权的故障注入、失败路径与恢复能力验证，并记录可重放的回滚证据；不用于未经隔离的生产设备破坏性实验。 | 故障注入 | `skills/adk-fault-injection-recovery/SKILL.md` |
| 70 | 60 | `verification` | primary | reviewer | `adk-artifact-gating` | 用于跨仓交付物需要标签、状态与验收交接协议时定义 Artifact 门禁；不用于单仓常规测试、直接上传制品或发布批准。 | artifact 门禁 | `skills/adk-artifact-gating/SKILL.md` |
| 70 | 70 | `verification` | primary | pipeline | `adk-pilot-framework` | 用于跨仓新能力的有界 Pilot 试跑、证据采集、失败门禁和回退判定；不用于替代正式产品资格认证或自动将试验结果发布。 | 试跑 | `skills/adk-pilot-framework/SKILL.md` |
| 70 | 80 | `verification` | primary | reviewer | `adk-verification-before-completion` | 用于交付完成前核对测试、审查、权限、证据与回滚的真实状态；不用于把实现者自述、静态检查或过期收据当作完成证明。 | 准备完成 | `skills/adk-verification-before-completion/SKILL.md` |
| 80 | 10 | `review_quality` | supporting | reviewer | `adk-chinese-commit-conventions` | 用于中文 Git 提交标题、scope 和变更摘要的规范化；不用于自动创建提交、调整权限或替代提交前质量门禁。 | 中文提交 | `skills/adk-chinese-commit-conventions/SKILL.md` |
| 80 | 20 | `review_quality` | supporting | reviewer | `adk-chinese-code-review` | 用于团队需要中文代码审查意见的格式、严重性和反馈沟通约定；不用于代替实际独立代码审查、修复验证或审批。 | 代码审查 | `skills/adk-chinese-code-review/SKILL.md` |
| 80 | 30 | `review_quality` | primary | reviewer | `adk-code-review-loop` | 用于独立代码审查、问题复核与反馈闭环；不用于自动批准或代替提交前门禁。 | 独立代码审查 | `skills/adk-code-review-loop/SKILL.md` |
| 80 | 40 | `review_quality` | primary | reviewer | `adk-repo-drift-remediation` | 用于全仓漂移、兼容残留、冗余目录和文档代码不一致的取证与修复计划；不用于跳过基线验证或清除用户未授权的改动。 | 仓库漂移 | `skills/adk-repo-drift-remediation/SKILL.md` |
| 80 | 50 | `review_quality` | primary | reviewer | `adk-static-analysis-c-cpp` | 用于 C/C++ 静态分析告警分级、根因追踪与误报确认，并补最小复现；不用于把单次扫描当作完整功能或动态安全验收。 | 静态分析 | `skills/adk-static-analysis-c-cpp/SKILL.md` |
| 80 | 60 | `review_quality` | primary | reviewer | `adk-commit-pr-quality-gate` | 用于提交 PR 前核对测试证据、差异范围与质量门禁；不能替代独立代码审查，也不用于未授权的合并或发布。 | 提交代码 | `skills/adk-commit-pr-quality-gate/SKILL.md` |
| 90 | 10 | `release_closure` | primary | generator | `adk-release-versioning` | 用于规划版本号、Changelog 和发布基线并检查历史版本一致性；不执行真实发布，也不用于替代固件包验证或设备更新。 | 版本发布 | `skills/adk-release-versioning/SKILL.md` |
| 90 | 20 | `release_closure` | primary | reviewer | `adk-production-field-readiness` | 用于嵌入式产测、OTA、诊断及现场维护的量产准备状态和证据审查；不用于仅凭桌面测试宣称量产就绪或直接刷写设备。 | 量产 | `skills/adk-production-field-readiness/SKILL.md` |
| 90 | 30 | `release_closure` | primary | pipeline | `adk-embedded-release-orchestration` | 用于嵌入式固件 OTA 制品的发布准备、签名证据和回滚编排；不用于未经单独授权的真实 publish、设备 flash 或发布批准。 | 嵌入式发布编排 | `skills/adk-embedded-release-orchestration/SKILL.md` |
| 90 | 40 | `release_closure` | primary | pipeline | `adk-embedded-storage-layout-migration` | 用于 MTD、UBI、分区及文件系统布局迁移的 host 端检查、演练和回退设计；不用于未授权的设备存储写入或纯日志检索。 | UBIFS | `skills/adk-embedded-storage-layout-migration/SKILL.md` |
| 90 | 50 | `release_closure` | supporting | generator | `adk-cross-team-handoff` | 用于产品、研发、测试等多团队交接时明确责任、接口和验收证据；不用于替代需求变更批准或直接操作外部系统。 | 团队交接 | `skills/adk-cross-team-handoff/SKILL.md` |
| 90 | 60 | `release_closure` | primary | governance | `adk-branch-closeout` | 用于代码与验证完成后的分支收口、PR 选择和保留或清理决策；不用于未验证时直接合并、删除用户工作树或替代评审。 | 分支收尾 | `skills/adk-branch-closeout/SKILL.md` |
| 90 | 70 | `release_closure` | primary | reviewer | `adk-after-action-review` | 用于任务交付后复盘问题、修复成本与可复用经验并形成候选记录；不用于替代交付前验证或直接发布未经审核的长期记忆。 | 任务复盘 | `skills/adk-after-action-review/SKILL.md` |
| 100 | 10 | `governance` | primary | governance | `adk-memory-curator` | 用于已授权的历史记录、项目知识和决策证据整理，生成可审查的 memory candidate；不用于静默写入长期记忆或传播无关敏感上下文。 | 记忆整理 | `skills/adk-memory-curator/SKILL.md` |
| 100 | 20 | `governance` | primary | governance | `adk-archive-governance` | 用于检查和修复现有归档的元数据、topic、hash 与安全问题；不负责新建知识笔记或代替知识候选的正式审核。 | 归档治理 | `skills/adk-archive-governance/SKILL.md` |
| 100 | 30 | `governance` | primary | generator | `adk-knowledge-archive` | 用于新建脱敏的研究、排障与决策归档候选并登记证据指针；不处理已有归档的元数据修复，也不替代发布审核。 | 知识归档 | `skills/adk-knowledge-archive/SKILL.md` |
| 100 | 50 | `governance` | primary | reviewer | `adk-engineering-growth-review` | 用于基于已授权的工程历史和交付证据做长期开发习惯复盘、学习建议与趋势分析；不用于推断私人属性或无证据评判个人表现。 | 开发者成长复盘 | `skills/adk-engineering-growth-review/SKILL.md` |

## Optional Skills

| Order | Stage | Category | Activation | Pattern | Name | Description | First Trigger | Path |
|---:|---:|---|---|---|---|---|---|---|
| 20 | 50 | `intake` | primary | pipeline | `adk-external-practice-absorption` | 统一评估 GitHub、GitLab、Gitee、OpenAI/Codex 官方、Anthropic/Claude 官方、微信公众号和人工证据中的外部 Agent、Skill、Workflow 与工程实践，并把批准项闭环到 ADK change、验证、pilot、发布复审和退役。用于“吸收外部实践”“评估参考实现”“从官方或社区沉淀 Agent/Skill/Workflow”“Gitee/GitLab/GitHub 实践研究”等请求；不用于普通功能开发、单纯浏览网页或未经 owner 决策的自动安装/复制。 | 吸收外部实践 | `optional-skills/adk-external-practice-absorption/SKILL.md` |
| 50 | 90 | `implementation` | supporting | tool-wrapper | `adk-data-fetch` | 用于按 URL 或 IMAP 类型选择**已显式安装**的数据获取子 Skill 并检查访问权限；不自动安装子 Skill，不用于数据库操作或未授权的邮件读取。 | 获取数据 | `optional-skills/adk-data-fetch/SKILL.md` |
| 50 | 91 | `implementation` | supporting | tool-wrapper | `adk-email-imap-fetch` | 用于已授权邮箱的只读 IMAP 邮件列表及正文提取，并限制凭据与输出范围；不用于邮件发送、归档写入或扫描无关邮箱。 | 获取邮件 | `optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md` |
| 50 | 92 | `implementation` | supporting | tool-wrapper | `adk-fetch-url-content` | 用于对明确的公开 HTTP(S) URL 做正文提取与结构化 Markdown 转换；不用于网页搜索、绕过登录、内网探测或抓取受限资源。 | 获取网页内容 | `optional-skills/adk-data-fetch/adk-fetch-url-content/SKILL.md` |
| 70 | 90 | `verification` | primary | playbook | `adk-test-flakiness-triage` | 用于非确定性测试故障的复现、波动归因和消除不稳定方案验证；不用于把失败盲目重跑到绿或降低测试门禁。 | 测试波动 | `optional-skills/adk-test-flakiness-triage/SKILL.md` |
| 80 | 70 | `review_quality` | primary | reviewer | `adk-security-supply-chain` | 用于第三方 Skill、脚本、依赖和参考资产引入前的来源、权限与供应链审查；不用于自动安装不可信包或把静态扫描当安全认证。 | 供应链审查 | `optional-skills/adk-security-supply-chain/SKILL.md` |
| 90 | 80 | `release_closure` | fallback | generator | `adk-incident-rca-report` | 用于生产事故稳定后整理时间线、根因、恢复和防复发证据；不用于事故正在处置时替代现场响应或虚构不存在的取证材料。 | 线上事故 | `optional-skills/adk-incident-rca-report/SKILL.md` |
| 100 | 40 | `governance` | primary | governance | `adk-skill-composition-governance` | 用于多个 Skill 的触发冲突、组合边界、fallback 和退役策略审查；不用于新增并行路由权威或直接提升工具写权限。 | 技能组合 | `optional-skills/adk-skill-composition-governance/SKILL.md` |

## Workflows

| Order | Type | Name | Description | Profiles | Primary Agent | Primary Skill | Path |
|---:|---|---|---|---|---|---|---|
| 10 | `feature-delivery` | `feature-delivery` | 新功能从需求收敛到验证评审的交付工作流 | core, embedded-fullstack | `requirements-analyst` | `adk-requirements-triage` | `workflows/feature-delivery/WORKFLOW.md` |
| 20 | `bugfix-delivery` | `bugfix-delivery` | 缺陷复现、根因定位、回归验证和审查闭环工作流 | embedded-fullstack | `application-engineer` | `adk-systematic-debugging` | `workflows/bugfix-delivery/WORKFLOW.md` |
| 60 | `release-hardening` | `release-hardening` | 发布前安全、性能、版本、回滚和放行证据收口工作流 | release-hardening | `build-release-engineer` | `adk-release-versioning` | `workflows/release-hardening/WORKFLOW.md` |
| 80 | `research-intake` | `external-practice-absorption` | 多来源外部实践从 report-only candidate 到独立决策、ADK change、验证、pilot、发布复审和退役的治理工作流 | research-intake | `external-practice-curator` | `adk-external-practice-absorption` | `workflows/external-practice-absorption/WORKFLOW.md` |
| 90 | `skill-curation-delivery` | `skill-curation-delivery` | 技能候选筛选、core/optional 归属和触发质量验证工作流 | core, team-core | `requirements-analyst` | `adk-requirements-triage` | `workflows/skill-curation-delivery/WORKFLOW.md` |
| 110 | `adk-governance` | `adk-delivery-gate` | agent-dev-kit 通用资产生产交付门禁 | core, embedded-fullstack | `code-review-governor` | `adk-verification-before-completion` | `workflows/adk-delivery-gate/WORKFLOW.md` |
| 110 | `adk-governance` | `runtime-routing` | 运行时技能路由、fallback 边界和 profile 闭包验证工作流 | core, embedded-fullstack | `architecture-planner` | `adk-runtime-router` | `workflows/runtime-routing/WORKFLOW.md` |

## Workflow Matrix

| Order | Type | Workflow | Profiles | Command Risk | Primary Agent | Primary Skill | Supporting Skills | Entry Conditions | Exit Evidence | Verification |
|---:|---|---|---|---|---|---|---|---|---|---|
| 10 | `feature-delivery` | `feature-delivery` | core, embedded-fullstack | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-interface-contract-design, adk-test-strategy, adk-verification-before-completion, adk-code-review-loop | 用户目标包含新功能、增强或可验收行为变化, 需求可以通过目标、非目标和验收标准表达 | 需求和任务拆解闭环, 实现范围与验收标准一致, 目标测试和完成前验证通过 | rtk bash tests/test_validate.sh, rtk bash tests/test_workflow_closure.sh |
| 20 | `bugfix-delivery` | `bugfix-delivery` | embedded-fullstack | low | `application-engineer` | `adk-systematic-debugging` | adk-task-breakdown, adk-verification-before-completion, adk-code-review-loop | 观察行为与预期行为不一致, 需要先复现、定位根因，再实施修复 | 根因陈述, 修复摘要, 复现路径或负结果说明, 定向回归验证 | rtk bash tests/test_workflow.sh, rtk bash tests/test_integration.sh |
| 60 | `release-hardening` | `release-hardening` | release-hardening | medium | `build-release-engineer` | `adk-release-versioning` | adk-test-strategy, adk-code-review-loop, adk-branch-closeout, adk-verification-before-completion, adk-commit-pr-quality-gate | 变更准备进入发布、打包、交付或现场放行阶段, 需要版本、回滚、安全、性能或放行证据 | 版本与制品信息, 回滚路径, 发布前验证结果, commit/PR 或放行门禁结论 | rtk bash tests/test_validate.sh, rtk bash tests/test_profile_coherence.sh |
| 80 | `research-intake` | `external-practice-absorption` | research-intake | low | `external-practice-curator` | `adk-external-practice-absorption` | adk-requirements-triage, adk-repo-prompt-analysis, adk-skill-deep-analysis, adk-task-breakdown, adk-verification-before-completion, adk-code-review-loop | 存在外部实践 candidate、来源 URL 或受治理 metadata evidence, 目标是评估、吸收、合并、增强、观察或拒绝外部实践 | 来源、重复、许可证/版权、安全和架构审查, 独立 owner decision 或 needs-more-evidence 结论, 批准项的 change、验证、pilot、发布复审与退役证据 | rtk bash tests/test_optional_skills.sh, rtk bash tests/test_workflow_closure.sh, rtk bash tests/test_skill_trigger_matrix.sh |
| 90 | `skill-curation-delivery` | `skill-curation-delivery` | core, team-core | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-commit-pr-quality-gate, adk-verification-before-completion | 新增、导入、拆分、替换或弃用 skill 候选, 需要判断 core/optional 归属和触发质量 | 归属决策, 正例、反例和 fallback 样例, catalog、SOP 和触发矩阵验证 | rtk bash tests/test_catalog.sh, rtk bash tests/test_skill_sop_quality.sh |
| 110 | `adk-governance` | `adk-delivery-gate` | core, embedded-fullstack | low | `code-review-governor` | `adk-verification-before-completion` | adk-runtime-router, adk-requirements-triage, adk-task-breakdown, adk-test-strategy, adk-code-review-loop, adk-after-action-review, adk-token-context-governance, adk-commit-pr-quality-gate | ADK active 资产、manifest、profile、workflow 或门禁发生变更, 需要把变更声明和验证证据绑定到完成前门禁 | strict validate 通过, workflow closure 或 profile coherence 通过, run_all 或等效定向回归证据 | rtk bash tests/run_all.sh --fail-fast |
| 110 | `adk-governance` | `runtime-routing` | core, embedded-fullstack | low | `architecture-planner` | `adk-runtime-router` | adk-verification-before-completion, adk-repo-drift-remediation | 新增、替换、弃用或重排 skill/profile/workflow 路由, 需要确认 primary/supporting/fallback 和 profile 闭包 | routing matrix 与 manifest 一致, trigger 冲突检查通过, profile coherence 和 workflow closure 通过 | rtk bash tests/test_skill_trigger_matrix.sh, rtk bash tests/test_workflow_closure.sh |

## Skill Routing Matrix

| Scenario | Description | Availability | Profiles | Workflow | Primary | Supporting | Fallback | Mutually Exclusive | Positive Example | Negative Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `runtime_routing` | 任务开始前选择 profile、primary skill 和 supporting skill | profile-resolved | core, embedded-fullstack | `runtime-routing` | `adk-runtime-router` | - | adk-requirements-triage | - | 判断这个任务应该使用哪个技能 | 只要计划，不要修改文件 |
| `unclear_requirement` | 需求、边界、验收或优先级不清，需要先收敛 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-requirements-triage` | - | - | adk-lightweight-planning, adk-planning-execution-loop | 需求不清楚，先梳理目标和验收标准 | 按已有计划直接执行 |
| `planning_only` | 用户明确要求只读计划，不创建、不修改、不删除文件 | profile-resolved | core | `-` | `adk-lightweight-planning` | - | adk-requirements-triage | adk-planning-execution-loop | 先给计划，不要改文件 | 按计划执行并修改代码 |
| `task_breakdown` | 需求已明确但任务过大，需要拆成可执行任务包 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-task-breakdown` | adk-requirements-triage | adk-lightweight-planning | - | 任务太大，拆解成任务包 | 根因不明，先定位问题 |
| `long_execution` | 长任务需要计划审查、检查点、恢复和完成前闭环 | explicit-profile-required | team-core | `feature-delivery` | `adk-planning-execution-loop` | adk-verification-before-completion | adk-lightweight-planning | adk-lightweight-planning | 分阶段执行并持续验证 | 只要计划，不要执行 |
| `unknown_root_cause_bug` | 行为异常但根因未明，需要系统化定位再修复 | profile-resolved | core, embedded-fullstack | `bugfix-delivery` | `adk-systematic-debugging` | - | - | adk-lightweight-planning | 问题根因不明确，需要定位后修复 | 新功能需求需要先拆解 |
| `embedded_log_analysis` | 嵌入式串口、boot、dmesg、ADB/logcat、OTA 或现场日志分析 | profile-resolved | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-embedded-remote-debug-log-triage` | adk-systematic-debugging, adk-offline-core-dump-triage, adk-embedded-diagnostic-harness, adk-token-context-governance | adk-systematic-debugging | - | 分析这段串口日志和 dmesg | 定义一个新接口契约 |
| `embedded_core_dump` | 嵌入式 Linux core dump、BuildID、符号和 backtrace 离线分析 | explicit-profile-required | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-offline-core-dump-triage` | adk-systematic-debugging | adk-systematic-debugging | - | 分析这个 core dump 和符号匹配 | 只需要查询 skill 分类 |
| `embedded_debug_transport` | ADB、SSH、串口、GDB remote、调试探针或厂商 CLI 的连接边界治理 | profile-resolved | embedded-fullstack | `bugfix-delivery` | `adk-embedded-debug-transport` | adk-systematic-debugging | adk-embedded-remote-debug-log-triage | - | ADB SSH 串口 GDB remote 调试通道 | 只读生成一个实现计划 |
| `completion_gate` | 完成前核对声明、验证证据、风险和回退边界 | profile-resolved | core, embedded-fullstack | `adk-delivery-gate` | `adk-verification-before-completion` | - | - | - | 准备完成，做完成前检查 | 需求边界还没明确 |
| `commit_pr_gate` | 提交或 PR 前质量门禁、格式、评审和证据检查 | profile-resolved | core, release-hardening | `adk-delivery-gate` | `adk-commit-pr-quality-gate` | adk-verification-before-completion | - | - | 准备 commit，跑提交门禁 | 只分析日志，不提交 |
| `release_versioning` | 发布、版本、制品、回滚和放行证据收口 | profile-resolved | release-hardening, embedded-fullstack | `release-hardening` | `adk-release-versioning` | adk-commit-pr-quality-gate | adk-branch-closeout | - | 准备发布并生成版本说明 | 代码根因还没定位 |
| `external_practice_absorption` | 多来源外部实践的来源审查、独立决策、ADK change、验证、pilot、发布复审和退役治理 | optional-skill-required | research-intake | `external-practice-absorption` | `adk-external-practice-absorption` | adk-requirements-triage, adk-repo-prompt-analysis, adk-verification-before-completion | adk-requirements-triage | - | 吸收 Gitee GitHub GitLab 的 Agent 工程实践 | 直接实现已经批准的普通功能 |
| `skill_governance` | skill 组合、触发优先级、fallback、弃用和 profile 归属治理 | optional-skill-required | core, team-core | `skill-curation-delivery` | `adk-skill-composition-governance` | adk-repo-drift-remediation, adk-verification-before-completion | adk-requirements-triage | - | skill、workflow 分类和排序需要治理 | 设备日志里有内核 oops |

## Profiles

| Name | Description | Optional | Extends |
|---|---|---|---|
| `core` | 通用 ADK 核心配置（需求、架构、实现、验证与评审） | false | - |
| `release-hardening` | 发布加固配置（安全审查、性能优化、合规检查） | false | - |
| `personal-core` | 个人通用 ADK 资产配置（核心功能 + 发布检查） | false | core |
| `embedded-fullstack` | 嵌入式全栈开发配置（芯片/板级、启动链、BSP、驱动、组件、应用、工具、验证、量产和现场维护） | false | core |
| `team-core` | 团队协作配置（交接/验证/评审） | false | core |
| `large-refactor` | 大型重构配置（API 稳定性 + 代码简化） | false | embedded-fullstack |
| `incident-response` | 线上事故响应配置（根因/复盘/恢复） | false | - |
| `research-intake` | 多来源外部实践吸收配置（只读候选审查与独立决策 handoff） | false | - |
