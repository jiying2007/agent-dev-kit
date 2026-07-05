# Agent and Skill Catalog

- generated_at: 2026-07-05T00:33:45Z
- source: manifest.yaml

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
| `hardware-debugger` | 硬件故障定位, oops 分析 | 长期架构设计, 发布放行 | driver-engineer, test-validation-engineer | adk-hardware-debugging, adk-embedded-remote-debug-log-triage, adk-systematic-debugging | 硬件调试结论必须包含现象、假设、实验和证据 |

## Skills

| Order | Stage | Category | Activation | Pattern | Name | Description | First Trigger | Path |
|---:|---:|---|---|---|---|---|---|---|
| 10 | 10 | `routing` | primary | governance | `adk-runtime-router` | adk-first 运行时技能路由入口，统一判定 primary/supporting/fallback 与跳过条件 | "技能路由" | `skills/adk-runtime-router/SKILL.md` |
| 10 | 20 | `routing` | primary | governance | `adk-context-engineering` | 上下文工程——优化 Agent 上下文设置 | "上下文不够" | `skills/adk-context-engineering/SKILL.md` |
| 10 | 30 | `routing` | primary | governance | `adk-token-context-governance` | 保真省 Token 的上下文读取治理，分层摘要、原文回退与高风险原文门禁 | "省 token" | `skills/adk-token-context-governance/SKILL.md` |
| 20 | 10 | `intake` | primary | playbook | `adk-requirements-triage` | 将需求转为可实现、可验证的工程条目 | "需求不清楚" | `skills/adk-requirements-triage/SKILL.md` |
| 20 | 20 | `intake` | primary | inversion | `adk-structured-requirements-questioning` | 结构化需求提问对齐，通过有序问题消除模糊需求 | "文档审查" | `skills/adk-structured-requirements-questioning/SKILL.md` |
| 20 | 30 | `intake` | primary | reviewer | `adk-repo-prompt-analysis` | 逆向分析开源项目中的 Prompt/系统指令设计，提取上下文工程模式 | 分析子仓 prompt | `skills/adk-repo-prompt-analysis/SKILL.md` |
| 20 | 40 | `intake` | primary | reviewer | `adk-skill-deep-analysis` | 从产品视角深度拆解 AI Skill 的设计意图、独特解法和可借鉴模式 | 深度拆解 skill | `skills/adk-skill-deep-analysis/SKILL.md` |
| 20 | 50 | `intake` | primary | pipeline | `adk-intake-workflow` | 子仓接入工作流——扫描、分析、决策与治理覆盖 | "接入新仓库" | `skills/adk-intake-workflow/SKILL.md` |
| 30 | 10 | `planning` | primary | playbook | `adk-lightweight-planning` | 轻量只读计划生成能力，用于用户明确要求先给计划但尚未要求执行或写文件的编码任务 | "给我一个计划" | `skills/adk-lightweight-planning/SKILL.md` |
| 30 | 20 | `planning` | primary | playbook | `adk-task-breakdown` | 将需求拆解为可并行执行的任务包 | "拆解任务" | `skills/adk-task-breakdown/SKILL.md` |
| 30 | 30 | `planning` | primary | governance | `adk-parallel-agent-governance` | 并行子代理治理，定义任务分片、scope_write、冲突矩阵、等待和整合验证 | "并行 agent" | `skills/adk-parallel-agent-governance/SKILL.md` |
| 30 | 40 | `planning` | primary | governance | `adk-worktree-governance` | git worktree 隔离开发治理，规范创建准入、目录、基线验证、同步、清理和禁止操作 | "worktree" | `skills/adk-worktree-governance/SKILL.md` |
| 30 | 50 | `planning` | primary | generator | `adk-context-compress-handoff` | 上下文压缩与会话接力，区分 stable/dynamic/evidence/excluded context，生成可恢复摘要、下一步和风险边界 | "上下文压缩" | `skills/adk-context-compress-handoff/SKILL.md` |
| 40 | 10 | `design` | primary | generator | `adk-interface-contract-design` | 定义模块/API/消息接口契约 | "设计接口" | `skills/adk-interface-contract-design/SKILL.md` |
| 40 | 20 | `design` | primary | generator | `adk-adr-writer` | 产出 Architecture Decision Record 并固化技术决策 | "写ADR" | `skills/adk-adr-writer/SKILL.md` |
| 40 | 30 | `design` | primary | reviewer | `adk-component-api-stability` | 组件 API 稳定性治理 | "API稳定性" | `skills/adk-component-api-stability/SKILL.md` |
| 40 | 40 | `design` | primary | generator | `adk-register-map-design` | 定义寄存器映射与位域文档 | "设计寄存器" | `skills/adk-register-map-design/SKILL.md` |
| 40 | 50 | `design` | primary | playbook | `adk-bsp-analysis` | BSP 代码分析、架构梳理、历史追溯 | bsp 分析 | `skills/adk-bsp-analysis/SKILL.md` |
| 50 | 10 | `implementation` | primary | playbook | `adk-driver-implementation` | 嵌入式驱动实现、联调验证与风险收口 | 驱动开发 | `skills/adk-driver-implementation/SKILL.md` |
| 50 | 20 | `implementation` | primary | playbook | `adk-driver-bringup-checklist` | 驱动 bring-up 标准检查清单 | "驱动开发" | `skills/adk-driver-bringup-checklist/SKILL.md` |
| 50 | 30 | `implementation` | primary | playbook | `adk-bsp-porting-playbook` | BSP 移植流程与风险控制 | "BSP移植" | `skills/adk-bsp-porting-playbook/SKILL.md` |
| 50 | 40 | `implementation` | primary | playbook | `adk-rtos-task-design` | RTOS 任务模型与优先级设计 | "RTOS任务" | `skills/adk-rtos-task-design/SKILL.md` |
| 50 | 50 | `implementation` | primary | playbook | `adk-interrupt-dma-patterns` | 中断与 DMA 协作模式设计 | "中断处理" | `skills/adk-interrupt-dma-patterns/SKILL.md` |
| 50 | 60 | `implementation` | primary | playbook | `adk-protocol-stack-integration` | 协议栈接入与状态机整合 | "协议栈" | `skills/adk-protocol-stack-integration/SKILL.md` |
| 50 | 70 | `implementation` | primary | tool-wrapper | `adk-cmake-cross-build` | CMake 交叉编译与多目标构建 | "CMake" | `skills/adk-cmake-cross-build/SKILL.md` |
| 50 | 80 | `implementation` | primary | reviewer | `adk-code-simplification` | 代码简化——在不改变行为的前提下提高清晰度 | "代码太复杂" | `skills/adk-code-simplification/SKILL.md` |
| 60 | 10 | `debugging` | primary | playbook | `adk-systematic-debugging` | 系统化调试流程，面向根因未明的问题定位与修复验证 | "调试" | `skills/adk-systematic-debugging/SKILL.md` |
| 60 | 20 | `debugging` | primary | tool-wrapper | `adk-embedded-debug-transport` | 嵌入式设备调试通道治理，覆盖 ADB/logcat、SSH、串口控制台、GDB remote、硬件调试探针和厂商 CLI 的连接边界、命令风险、证据采集和回滚锚点 | "调试通道" | `skills/adk-embedded-debug-transport/SKILL.md` |
| 60 | 30 | `debugging` | primary | playbook | `adk-embedded-remote-debug-log-triage` | 嵌入式设备端远程调试与日志取证，覆盖 SSH、ADB/logcat、串口、GDB remote、调试探针、boot/dmesg/应用/OTA/prog 日志、core dump 线索、知识库历史召回和下一步探针 | "远程调试" | `skills/adk-embedded-remote-debug-log-triage/SKILL.md` |
| 60 | 40 | `debugging` | primary | playbook | `adk-offline-core-dump-triage` | 嵌入式 Linux 离线 core dump 取证，先校验 core/binary/BuildID/符号/GDB 依赖，再给可信 backtrace、根因边界和下一步探针 | "core dump" | `skills/adk-offline-core-dump-triage/SKILL.md` |
| 60 | 50 | `debugging` | primary | playbook | `adk-hardware-debugging` | 硬件问题调试、oops 分析 | 硬件调试 | `skills/adk-hardware-debugging/SKILL.md` |
| 60 | 60 | `debugging` | primary | tool-wrapper | `adk-performance-profiling-embedded` | 嵌入式性能剖析与优化路径 | "性能分析" | `skills/adk-performance-profiling-embedded/SKILL.md` |
| 70 | 10 | `verification` | primary | playbook | `adk-test-strategy` | 嵌入式全栈测试策略与 TDD 分级，覆盖板级、启动链、BSP、OS/runtime、驱动、组件、设备应用、上位机工具、量产和现场维护的验证证据 | "测试策略" | `skills/adk-test-strategy/SKILL.md` |
| 70 | 20 | `verification` | primary | generator | `adk-unit-test-embedded` | 嵌入式单元测试策略与样例 | "单元测试" | `skills/adk-unit-test-embedded/SKILL.md` |
| 70 | 30 | `verification` | primary | playbook | `adk-integration-hil-sil` | HIL/SIL 集成验证编排 | "集成测试" | `skills/adk-integration-hil-sil/SKILL.md` |
| 70 | 40 | `verification` | primary | tool-wrapper | `adk-embedded-diagnostic-harness` | 嵌入式诊断 harness 治理，覆盖 prog_tool、diag 命令、strict/env 套件、返回码语义、HIL/SIL 证据和产测 CLI 验证 | "诊断 harness" | `skills/adk-embedded-diagnostic-harness/SKILL.md` |
| 70 | 50 | `verification` | primary | playbook | `adk-fault-injection-recovery` | 故障注入与恢复策略验证 | "故障注入" | `skills/adk-fault-injection-recovery/SKILL.md` |
| 70 | 60 | `verification` | primary | reviewer | `adk-artifact-gating` | 跨仓库 Artifact 门禁协议——统一标签、状态机与交接规范 | "artifact 门禁" | `skills/adk-artifact-gating/SKILL.md` |
| 70 | 70 | `verification` | primary | pipeline | `adk-pilot-framework` | 跨仓库 Pilot 试跑框架——场景定义、证据收集与门禁验收 | "试跑" | `skills/adk-pilot-framework/SKILL.md` |
| 70 | 80 | `verification` | primary | reviewer | `adk-verification-before-completion` | 完成前验证门禁，确保交付声明与证据一致 | "准备完成" | `skills/adk-verification-before-completion/SKILL.md` |
| 80 | 10 | `review_quality` | supporting | reviewer | `adk-chinese-commit-conventions` | 中文 Git 提交规范——适配国内开发团队 | "中文提交" | `skills/adk-chinese-commit-conventions/SKILL.md` |
| 80 | 20 | `review_quality` | supporting | reviewer | `adk-chinese-code-review` | 中文代码审查规范——适配国内团队沟通风格 | "代码审查" | `skills/adk-chinese-code-review/SKILL.md` |
| 80 | 30 | `review_quality` | primary | reviewer | `adk-code-review-loop` | 独立代码审查与反馈修复闭环，覆盖发现分级、真实性核验、修复验证和复审 | "独立代码审查" | `skills/adk-code-review-loop/SKILL.md` |
| 80 | 40 | `review_quality` | primary | reviewer | `adk-repo-drift-remediation` | 仓库漂移治理，面向全仓偏离、冗余、残留、边界不清、文档代码不一致和提交前质量收口 | "仓库漂移" | `skills/adk-repo-drift-remediation/SKILL.md` |
| 80 | 50 | `review_quality` | primary | reviewer | `adk-static-analysis-c-cpp` | C/C++ 静态分析与缺陷治理 | "静态分析" | `skills/adk-static-analysis-c-cpp/SKILL.md` |
| 80 | 60 | `review_quality` | primary | reviewer | `adk-commit-pr-quality-gate` | 提交与 PR 质量门禁检查 | "提交代码" | `skills/adk-commit-pr-quality-gate/SKILL.md` |
| 90 | 10 | `release_closure` | primary | generator | `adk-release-versioning` | 版本策略、变更说明与发布基线 | "版本发布" | `skills/adk-release-versioning/SKILL.md` |
| 90 | 20 | `release_closure` | primary | reviewer | `adk-production-field-readiness` | 嵌入式量产、产测、烧录、诊断、OTA、回滚与现场维护 readiness | "量产" | `skills/adk-production-field-readiness/SKILL.md` |
| 90 | 30 | `release_closure` | primary | pipeline | `adk-embedded-release-orchestration` | 嵌入式全栈发布编排，覆盖 SoC、MCU、bootloader、SD 升级、OTA、NAS/产线发布、版本标签、制品包和非覆盖发布门禁 | "嵌入式发布编排" | `skills/adk-embedded-release-orchestration/SKILL.md` |
| 90 | 40 | `release_closure` | primary | pipeline | `adk-embedded-storage-layout-migration` | 嵌入式存储布局和文件系统迁移治理，覆盖 UBI/UBIFS/SquashFS/ubiblock、业务分区保留、OTA 迁移、启动日志校验和回滚边界 | "UBIFS" | `skills/adk-embedded-storage-layout-migration/SKILL.md` |
| 90 | 60 | `release_closure` | primary | governance | `adk-branch-closeout` | 开发分支收尾治理，验证完成后选择本地合并、创建 PR、保留或丢弃并执行清理 | "分支收尾" | `skills/adk-branch-closeout/SKILL.md` |
| 90 | 70 | `release_closure` | primary | reviewer | `adk-after-action-review` | 任务复盘与经验记忆候选治理，提取 lessons、风险分级和写入路由 | "任务复盘" | `skills/adk-after-action-review/SKILL.md` |
| 100 | 10 | `governance` | primary | governance | `adk-memory-curator` | 记忆整理与候选治理，审计 memories、AGENTS、归档、session 总结和决策记录，生成可审查 memory candidate | "记忆整理" | `skills/adk-memory-curator/SKILL.md` |
| 100 | 20 | `governance` | primary | governance | `adk-archive-governance` | docs/archive 归档治理，覆盖 meta、topic registry、文件名、hash、superseded、敏感材料和归档门禁修复 | "归档治理" | `skills/adk-archive-governance/SKILL.md` |
| 100 | 30 | `governance` | primary | generator | `adk-knowledge-archive` | 知识归档与长期沉淀，将高价值总结、研究、排障、决策和会话材料写成脱敏、可检索、可治理的归档候选 | "知识归档" | `skills/adk-knowledge-archive/SKILL.md` |
| 100 | 50 | `governance` | primary | reviewer | `adk-engineering-growth-review` | 本地工程成长复盘与学习建议，宽读本地 Codex 历史、归档、日报和项目证据，识别长期趋势、重复问题和训练计划 | "开发者成长复盘" | `skills/adk-engineering-growth-review/SKILL.md` |

## Optional Skills

| Order | Stage | Category | Activation | Pattern | Name | Description | First Trigger | Path |
|---:|---:|---|---|---|---|---|---|---|
| 30 | 60 | `planning` | primary | pipeline | `adk-planning-execution-loop` | 长任务计划审查、分阶段执行、恢复与收口闭环 | "执行计划" | `optional-skills/adk-planning-execution-loop/SKILL.md` |
| 50 | 90 | `implementation` | supporting | tool-wrapper | `adk-data-fetch` | 数据获取技能组合——包含邮件获取与网页正文提取 | "获取数据" | `optional-skills/adk-data-fetch/SKILL.md` |
| 50 | 91 | `implementation` | supporting | tool-wrapper | `adk-email-imap-fetch` | IMAP 邮件获取——从邮箱获取邮件列表和内容 | "获取邮件" | `optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md` |
| 50 | 92 | `implementation` | supporting | tool-wrapper | `adk-fetch-url-content` | URL 正文提取——从网页提取结构化内容 | "获取网页内容" | `optional-skills/adk-data-fetch/adk-fetch-url-content/SKILL.md` |
| 70 | 90 | `verification` | primary | playbook | `adk-test-flakiness-triage` | 定位测试波动根因并给出稳定化方案 | "测试波动" | `optional-skills/adk-test-flakiness-triage/SKILL.md` |
| 80 | 70 | `review_quality` | primary | reviewer | `adk-security-supply-chain` | 第三方技能、脚本与参考资产引入前的安全和供应链审查 | "供应链审查" | `optional-skills/adk-security-supply-chain/SKILL.md` |
| 90 | 50 | `release_closure` | supporting | generator | `adk-cross-team-handoff` | 跨团队交接时统一目标、边界和验收责任 | "团队交接" | `optional-skills/adk-cross-team-handoff/SKILL.md` |
| 90 | 80 | `release_closure` | fallback | generator | `adk-incident-rca-report` | 线上事故复盘与根因分析闭环 | "线上事故" | `optional-skills/adk-incident-rca-report/SKILL.md` |
| 100 | 40 | `governance` | primary | governance | `adk-skill-composition-governance` | 治理技能组合、触发优先级、fallback 与弃用关系 | "技能组合" | `optional-skills/adk-skill-composition-governance/SKILL.md` |

## Workflows

| Order | Type | Name | Description | Profiles | Primary Agent | Primary Skill | Path |
|---:|---|---|---|---|---|---|---|
| 10 | `feature-delivery` | `feature-delivery` | 新功能从需求收敛到验证评审的交付工作流 | core, embedded-fullstack | `requirements-analyst` | `adk-requirements-triage` | `workflows/feature-delivery/WORKFLOW.md` |
| 20 | `bugfix-delivery` | `bugfix-delivery` | 缺陷复现、根因定位、回归验证和审查闭环工作流 | embedded-fullstack | `application-engineer` | `adk-systematic-debugging` | `workflows/bugfix-delivery/WORKFLOW.md` |
| 60 | `release-hardening` | `release-hardening` | 发布前安全、性能、版本、回滚和放行证据收口工作流 | release-hardening | `build-release-engineer` | `adk-release-versioning` | `workflows/release-hardening/WORKFLOW.md` |
| 90 | `skill-curation-delivery` | `skill-curation-delivery` | 技能候选筛选、core/optional 归属和触发质量验证工作流 | core, team-core | `requirements-analyst` | `adk-requirements-triage` | `workflows/skill-curation-delivery/WORKFLOW.md` |
| 110 | `adk-governance` | `adk-delivery-gate` | agent-dev-kit 通用资产生产交付门禁 | core, embedded-fullstack | `code-review-governor` | `adk-verification-before-completion` | `workflows/adk-delivery-gate/WORKFLOW.md` |
| 110 | `adk-governance` | `runtime-routing` | 运行时技能路由、fallback 边界和 profile 闭包验证工作流 | core, embedded-fullstack | `architecture-planner` | `adk-runtime-router` | `workflows/runtime-routing/WORKFLOW.md` |

## Workflow Matrix

| Order | Type | Workflow | Profiles | Command Risk | Primary Agent | Primary Skill | Supporting Skills | Entry Conditions | Exit Evidence | Verification |
|---:|---|---|---|---|---|---|---|---|---|---|
| 10 | `feature-delivery` | `feature-delivery` | core, embedded-fullstack | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-interface-contract-design, adk-unit-test-embedded, adk-verification-before-completion, adk-code-review-loop | 用户目标包含新功能、增强或可验收行为变化, 需求可以通过目标、非目标和验收标准表达 | 需求和任务拆解闭环, 实现范围与验收标准一致, 目标测试和完成前验证通过 | rtk bash tests/test_validate.sh, rtk bash tests/test_workflow_closure.sh |
| 20 | `bugfix-delivery` | `bugfix-delivery` | embedded-fullstack | low | `application-engineer` | `adk-systematic-debugging` | adk-task-breakdown, adk-verification-before-completion, adk-code-review-loop | 观察行为与预期行为不一致, 需要先复现、定位根因，再实施修复 | 根因陈述, 修复摘要, 复现路径或负结果说明, 定向回归验证 | rtk bash tests/test_workflow.sh, rtk bash tests/test_integration.sh |
| 60 | `release-hardening` | `release-hardening` | release-hardening | medium | `build-release-engineer` | `adk-release-versioning` | adk-test-strategy, adk-code-review-loop, adk-branch-closeout, adk-verification-before-completion, adk-commit-pr-quality-gate | 变更准备进入发布、打包、交付或现场放行阶段, 需要版本、回滚、安全、性能或放行证据 | 版本与制品信息, 回滚路径, 发布前验证结果, commit/PR 或放行门禁结论 | rtk bash tests/test_validate.sh, rtk bash tests/test_profile_coherence.sh |
| 90 | `skill-curation-delivery` | `skill-curation-delivery` | core, team-core | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-commit-pr-quality-gate, adk-verification-before-completion | 新增、导入、拆分、替换或弃用 skill 候选, 需要判断 core/optional 归属和触发质量 | 归属决策, 正例、反例和 fallback 样例, catalog、SOP 和触发矩阵验证 | rtk bash tests/test_catalog.sh, rtk bash tests/test_skill_sop_quality.sh |
| 110 | `adk-governance` | `adk-delivery-gate` | core, embedded-fullstack | low | `code-review-governor` | `adk-verification-before-completion` | adk-runtime-router, adk-requirements-triage, adk-task-breakdown, adk-test-strategy, adk-code-review-loop, adk-after-action-review, adk-token-context-governance, adk-commit-pr-quality-gate | ADK active 资产、manifest、profile、workflow 或门禁发生变更, 需要把变更声明和验证证据绑定到完成前门禁 | strict validate 通过, workflow closure 或 profile coherence 通过, run_all 或等效定向回归证据 | rtk bash tests/run_all.sh --fail-fast |
| 110 | `adk-governance` | `runtime-routing` | core, embedded-fullstack | low | `architecture-planner` | `adk-runtime-router` | adk-verification-before-completion, adk-repo-drift-remediation | 新增、替换、弃用或重排 skill/profile/workflow 路由, 需要确认 primary/supporting/fallback 和 profile 闭包 | routing matrix 与 manifest 一致, trigger 冲突检查通过, profile coherence 和 workflow closure 通过 | rtk bash tests/test_skill_trigger_matrix.sh, rtk bash tests/test_workflow_closure.sh |

## Skill Routing Matrix

| Scenario | Description | Availability | Profiles | Workflow | Primary | Supporting | Fallback | Mutually Exclusive | Positive Example | Negative Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `runtime_routing` | 任务开始前选择 profile、primary skill 和 supporting skill | profile-resolved | core, embedded-fullstack | `runtime-routing` | `adk-runtime-router` | - | adk-requirements-triage | - | 判断这个任务应该使用哪个技能 | 只要计划，不要修改文件 |
| `unclear_requirement` | 需求、边界、验收或优先级不清，需要先收敛 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-requirements-triage` | adk-structured-requirements-questioning | - | adk-lightweight-planning, adk-planning-execution-loop | 需求不清楚，先梳理目标和验收标准 | 按已有计划直接执行 |
| `planning_only` | 用户明确要求只读计划，不创建、不修改、不删除文件 | profile-resolved | core | `-` | `adk-lightweight-planning` | - | adk-requirements-triage | adk-planning-execution-loop | 先给计划，不要改文件 | 按计划执行并修改代码 |
| `task_breakdown` | 需求已明确但任务过大，需要拆成可执行任务包 | profile-resolved | core, embedded-fullstack | `feature-delivery` | `adk-task-breakdown` | adk-requirements-triage | adk-lightweight-planning | - | 任务太大，拆解成任务包 | 根因不明，先定位问题 |
| `long_execution` | 长任务需要计划审查、检查点、恢复和完成前闭环 | optional-skill-required | core, embedded-fullstack | `feature-delivery` | `adk-planning-execution-loop` | adk-task-breakdown, adk-verification-before-completion | adk-lightweight-planning | adk-lightweight-planning | 分阶段执行并持续验证 | 只要计划，不要执行 |
| `unknown_root_cause_bug` | 行为异常但根因未明，需要系统化定位再修复 | profile-resolved | core, embedded-fullstack | `bugfix-delivery` | `adk-systematic-debugging` | adk-test-strategy, adk-verification-before-completion | - | adk-lightweight-planning | 问题根因不明确，需要定位后修复 | 新功能需求需要先拆解 |
| `embedded_log_analysis` | 嵌入式串口、boot、dmesg、ADB/logcat、OTA 或现场日志分析 | profile-resolved | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-embedded-remote-debug-log-triage` | adk-systematic-debugging, adk-embedded-debug-transport, adk-offline-core-dump-triage | adk-systematic-debugging | - | 分析这段串口日志和 dmesg | 定义一个新接口契约 |
| `embedded_core_dump` | 嵌入式 Linux core dump、BuildID、符号和 backtrace 离线分析 | profile-resolved | embedded-fullstack, incident-response | `bugfix-delivery` | `adk-offline-core-dump-triage` | adk-systematic-debugging, adk-embedded-remote-debug-log-triage | adk-systematic-debugging | - | 分析这个 core dump 和符号匹配 | 只需要查询 skill 分类 |
| `embedded_debug_transport` | ADB、SSH、串口、GDB remote、调试探针或厂商 CLI 的连接边界治理 | profile-resolved | embedded-fullstack | `bugfix-delivery` | `adk-embedded-debug-transport` | adk-systematic-debugging | adk-embedded-remote-debug-log-triage | - | ADB SSH 串口 GDB remote 调试通道 | 只读生成一个实现计划 |
| `completion_gate` | 完成前核对声明、验证证据、风险和回退边界 | profile-resolved | core, embedded-fullstack | `adk-delivery-gate` | `adk-verification-before-completion` | adk-test-strategy | - | - | 准备完成，做完成前检查 | 需求边界还没明确 |
| `commit_pr_gate` | 提交或 PR 前质量门禁、格式、评审和证据检查 | profile-resolved | core, release-hardening | `adk-delivery-gate` | `adk-commit-pr-quality-gate` | adk-verification-before-completion, adk-code-review-loop | - | - | 准备 commit，跑提交门禁 | 只分析日志，不提交 |
| `release_versioning` | 发布、版本、制品、回滚和放行证据收口 | profile-resolved | release-hardening, embedded-fullstack | `release-hardening` | `adk-release-versioning` | adk-commit-pr-quality-gate, adk-verification-before-completion | adk-branch-closeout | - | 准备发布并生成版本说明 | 代码根因还没定位 |
| `skill_governance` | skill 组合、触发优先级、fallback、弃用和 profile 归属治理 | optional-skill-required | core, team-core | `skill-curation-delivery` | `adk-skill-composition-governance` | adk-repo-drift-remediation, adk-verification-before-completion | adk-requirements-triage | - | skill、workflow 分类和排序需要治理 | 设备日志里有内核 oops |

## Profiles

| Name | Description | Optional | Extends |
|---|---|---|---|
| `core` | 通用 ADK 核心配置（需求、架构、实现、验证与评审） | false | - |
| `release-hardening` | 发布加固配置（安全审查、性能优化、合规检查） | false | - |
| `personal-core` | 个人通用 ADK 资产配置（核心功能 + 发布检查） | false | core |
| `embedded-fullstack` | 嵌入式全栈开发配置（芯片/板级、启动链、BSP、驱动、组件、应用、工具、验证、量产和现场维护） | false | core |
| `team-core` | 团队协作配置（交接/验证/评审） | false | core |
| `openspec-driven` | Spec 驱动开发配置（需求/设计/任务链路） | false | core |
| `large-refactor` | 大型重构配置（API 稳定性 + 代码简化） | false | embedded-fullstack |
| `incident-response` | 线上事故响应配置（根因/复盘/恢复） | false | - |
| `research-intake` | 参考仓吸收配置（候选筛选与审查） | false | - |
