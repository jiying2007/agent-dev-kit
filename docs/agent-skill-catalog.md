# Agent and Skill Catalog

- generated_at: 2026-06-01T12:19:14Z
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
| `adk-bsp-analyst` | BSP 代码分析、架构梳理、历史追溯 | `agents/adk-bsp-analyst/AGENTS.md` |
| `adk-driver-developer` | 嵌入式驱动实现、接口适配和 bring-up 修复 | `agents/adk-driver-developer/AGENTS.md` |
| `adk-hardware-debugger` | 硬件故障定位、oops 分析和板级调试证据整理 | `agents/adk-hardware-debugger/AGENTS.md` |
| `adk-planner` | 需求分析、任务拆解和工程方案设计 | `agents/adk-planner/AGENTS.md` |
| `adk-generator` | 按任务契约完成编码实现和单元测试补充 | `agents/adk-generator/AGENTS.md` |
| `adk-evaluator` | 代码评审、质量验证和放行风险判断 | `agents/adk-evaluator/AGENTS.md` |

## Agent Contract Matrix

| Agent | Owns | Does Not Own | Handoff To | Default Skills | Quality Gate |
|---|---|---|---|---|---|
| `requirements-analyst` | 需求边界, 验收标准 | 代码实现, 发布操作 | architecture-planner, test-validation-engineer, code-review-governor | adk-requirements-triage, adk-task-breakdown | 目标、非目标、影响面、验收标准和风险必须可验证 |
| `architecture-planner` | 架构边界, 接口决策 | 直接编码, 发布签核 | component-engineer, driver-engineer, code-review-governor | adk-interface-contract-design, adk-adr-writer | 设计必须包含接口、兼容性、迁移和回退边界 |
| `driver-engineer` | 驱动实现, bring-up 证据 | 产品需求裁剪, 发布放行 | test-validation-engineer, code-review-governor | adk-driver-bringup-checklist, adk-systematic-debugging | 驱动变更必须绑定硬件约束、验证证据和回归路径 |
| `component-engineer` | 组件接口, 模块实现 | 需求验收口径, 发布版本策略 | test-validation-engineer, code-review-governor | adk-interface-contract-design, adk-component-api-stability | 组件变更必须保留 API 稳定性和集成验证证据 |
| `application-engineer` | 应用逻辑, 工具行为 | 架构最终裁决, 发布放行 | test-validation-engineer, code-review-governor | adk-systematic-debugging, adk-unit-test-embedded | 应用行为变更必须包含用户路径、错误路径和回归证据 |
| `build-release-engineer` | 构建打包, 发布回滚 | 需求变更, 安全风险豁免 | security-compliance-reviewer, performance-reliability-engineer | adk-release-versioning, adk-commit-pr-quality-gate | 发布必须绑定版本、制品、校验、回滚和放行证据 |
| `test-validation-engineer` | 测试策略, 验证证据 | 功能实现, 风险豁免 | code-review-governor, build-release-engineer | adk-test-strategy, adk-verification-before-completion | 完成结论必须与验证命令、退出码和证据路径一致 |
| `performance-reliability-engineer` | 性能分析, 可靠性风险 | 功能需求裁决, 安全签核 | build-release-engineer, code-review-governor | adk-performance-profiling-embedded, adk-fault-injection-recovery | 性能和可靠性结论必须包含基线、负载条件和对比证据 |
| `security-compliance-reviewer` | 安全审查, 供应链风险 | 功能实现, 发布执行 | build-release-engineer, code-review-governor | adk-static-analysis-c-cpp, adk-commit-pr-quality-gate | 高风险项必须修复、降级或显式记录风险接受 |
| `code-review-governor` | 审查分级, 放行判断 | 直接修复代码, 发布执行 | requirements-analyst, test-validation-engineer | adk-code-review-loop, adk-commit-pr-quality-gate | blocker 必须修复或明确风险接受后才能放行 |
| `adk-bsp-analyst` | BSP 分析, 历史追溯 | 驱动实现, 发布放行 | adk-driver-developer, architecture-planner | adk-bsp-analyst, adk-bsp-porting-playbook | BSP 结论必须包含入口、依赖、风险和追溯证据 |
| `adk-driver-developer` | 嵌入式驱动实现, 接口适配 | BSP 架构裁决, 发布放行 | adk-evaluator, test-validation-engineer | adk-driver-developer, adk-driver-bringup-checklist | 驱动实现必须包含 bring-up、错误路径和验证证据 |
| `adk-hardware-debugger` | 硬件故障定位, oops 分析 | 长期架构设计, 发布放行 | adk-driver-developer, test-validation-engineer | adk-hardware-debugger, adk-systematic-debugging | 硬件调试结论必须包含现象、假设、实验和证据 |
| `adk-planner` | 计划拆解, 方案设计 | 代码实现, 质量放行 | adk-generator, adk-evaluator | adk-planner, adk-task-breakdown | 计划必须包含 scope、依赖、验证和阻塞条件 |
| `adk-generator` | 编码实现, 单元测试补充 | 需求重写, 审查放行 | adk-evaluator, test-validation-engineer | adk-generator, adk-unit-test-embedded | 实现必须匹配任务契约并通过定向验证 |
| `adk-evaluator` | 质量验证, 风险判断 | 编码修复, 需求变更 | adk-planner, code-review-governor | adk-evaluator, adk-code-review-loop | 评估结论必须列出 blocker、验证证据和剩余风险 |

## Skills

| Name | Description | First Trigger | Path |
|---|---|---|---|
| `adk-requirements-triage` | 将需求转为可实现、可验证的工程条目 | "需求不清楚" | `skills/adk-requirements-triage/SKILL.md` |
| `adk-runtime-router` | adk-first 运行时技能路由入口，统一判定 primary/supporting/fallback 与跳过条件 | "技能路由" | `skills/adk-runtime-router/SKILL.md` |
| `adk-test-strategy` | 嵌入式全栈测试策略与 TDD 分级，覆盖板级、启动链、BSP、OS/runtime、驱动、组件、设备应用、上位机工具、量产和现场维护的验证证据 | "测试策略" | `skills/adk-test-strategy/SKILL.md` |
| `adk-code-review-loop` | 独立代码审查与反馈修复闭环，覆盖发现分级、真实性核验、修复验证和复审 | "独立代码审查" | `skills/adk-code-review-loop/SKILL.md` |
| `adk-parallel-agent-governance` | 并行子代理治理，定义任务分片、scope_write、冲突矩阵、等待和整合验证 | "并行 agent" | `skills/adk-parallel-agent-governance/SKILL.md` |
| `adk-worktree-governance` | git worktree 隔离开发治理，规范创建准入、目录、基线验证、同步、清理和禁止操作 | "worktree" | `skills/adk-worktree-governance/SKILL.md` |
| `adk-branch-closeout` | 开发分支收尾治理，验证完成后选择本地合并、创建 PR、保留或丢弃并执行清理 | "分支收尾" | `skills/adk-branch-closeout/SKILL.md` |
| `adk-adr-writer` | 产出 Architecture Decision Record 并固化技术决策 | "写ADR" | `skills/adk-adr-writer/SKILL.md` |
| `adk-task-breakdown` | 将需求拆解为可并行执行的任务包 | "拆解任务" | `skills/adk-task-breakdown/SKILL.md` |
| `adk-plan-lite` | 轻量只读计划生成能力，用于用户明确要求先给计划但尚未要求执行或写文件的编码任务 | "给我一个计划" | `skills/adk-plan-lite/SKILL.md` |
| `adk-context-compress-handoff` | 上下文压缩与会话接力，区分 stable/dynamic/evidence/excluded context，生成可恢复摘要、下一步和风险边界 | "上下文压缩" | `skills/adk-context-compress-handoff/SKILL.md` |
| `adk-interface-contract-design` | 定义模块/API/消息接口契约 | "设计接口" | `skills/adk-interface-contract-design/SKILL.md` |
| `adk-register-map-design` | 定义寄存器映射与位域文档 | "设计寄存器" | `skills/adk-register-map-design/SKILL.md` |
| `adk-driver-bringup-checklist` | 驱动 bring-up 标准检查清单 | "驱动开发" | `skills/adk-driver-bringup-checklist/SKILL.md` |
| `adk-bsp-porting-playbook` | BSP 移植流程与风险控制 | "BSP移植" | `skills/adk-bsp-porting-playbook/SKILL.md` |
| `adk-rtos-task-design` | RTOS 任务模型与优先级设计 | "RTOS任务" | `skills/adk-rtos-task-design/SKILL.md` |
| `adk-interrupt-dma-patterns` | 中断与 DMA 协作模式设计 | "中断处理" | `skills/adk-interrupt-dma-patterns/SKILL.md` |
| `adk-protocol-stack-integration` | 协议栈接入与状态机整合 | "协议栈" | `skills/adk-protocol-stack-integration/SKILL.md` |
| `adk-component-api-stability` | 组件 API 稳定性治理 | "API稳定性" | `skills/adk-component-api-stability/SKILL.md` |
| `adk-cmake-cross-build` | CMake 交叉编译与多目标构建 | "CMake" | `skills/adk-cmake-cross-build/SKILL.md` |
| `adk-toolchain-debug-openocd-gdb` | OpenOCD + GDB 联调流程 | "OpenOCD" | `skills/adk-toolchain-debug-openocd-gdb/SKILL.md` |
| `adk-static-analysis-c-cpp` | C/C++ 静态分析与缺陷治理 | "静态分析" | `skills/adk-static-analysis-c-cpp/SKILL.md` |
| `adk-systematic-debugging` | 系统化调试流程，面向根因未明的问题定位与修复验证 | "调试" | `skills/adk-systematic-debugging/SKILL.md` |
| `adk-unit-test-embedded` | 嵌入式单元测试策略与样例 | "单元测试" | `skills/adk-unit-test-embedded/SKILL.md` |
| `adk-verification-before-completion` | 完成前验证门禁，确保交付声明与证据一致 | "准备完成" | `skills/adk-verification-before-completion/SKILL.md` |
| `adk-after-action-review` | 任务复盘与经验记忆候选治理，提取 lessons、风险分级和写入路由 | "任务复盘" | `skills/adk-after-action-review/SKILL.md` |
| `adk-developer-growth-review` | 本地开发者成长复盘与学习建议，宽读本地 Codex 历史、归档、日报和项目证据，识别长期趋势、重复问题和训练计划 | "开发者成长复盘" | `skills/adk-developer-growth-review/SKILL.md` |
| `adk-memory-curator` | 记忆整理与候选治理，审计 memories、AGENTS、归档、session 总结和决策记录，生成可审查 memory candidate | "记忆整理" | `skills/adk-memory-curator/SKILL.md` |
| `adk-archive-governance` | docs/archive 归档治理，覆盖 meta、topic registry、文件名、hash、superseded、敏感材料和归档门禁修复 | "归档治理" | `skills/adk-archive-governance/SKILL.md` |
| `adk-knowledge-archive` | 知识归档与长期沉淀，将高价值总结、研究、排障、决策和会话材料写成脱敏、可检索、可治理的归档候选 | "知识归档" | `skills/adk-knowledge-archive/SKILL.md` |
| `adk-integration-hil-sil` | HIL/SIL 集成验证编排 | "集成测试" | `skills/adk-integration-hil-sil/SKILL.md` |
| `adk-fault-injection-recovery` | 故障注入与恢复策略验证 | "故障注入" | `skills/adk-fault-injection-recovery/SKILL.md` |
| `adk-performance-profiling-embedded` | 嵌入式性能剖析与优化路径 | "性能分析" | `skills/adk-performance-profiling-embedded/SKILL.md` |
| `adk-release-versioning` | 版本策略、变更说明与发布基线 | "版本发布" | `skills/adk-release-versioning/SKILL.md` |
| `adk-production-field-readiness` | 嵌入式量产、产测、烧录、诊断、OTA、回滚与现场维护 readiness | "量产" | `skills/adk-production-field-readiness/SKILL.md` |
| `adk-embedded-diagnostic-harness` | 嵌入式诊断 harness 治理，覆盖 prog_tool、diag 命令、strict/env 套件、返回码语义、HIL/SIL 证据和产测 CLI 验证 | "诊断 harness" | `skills/adk-embedded-diagnostic-harness/SKILL.md` |
| `adk-embedded-release-orchestration` | 嵌入式全栈发布编排，覆盖 SoC、MCU、bootloader、SD 升级、OTA、NAS/产线发布、版本标签、制品包和非覆盖发布门禁 | "嵌入式发布编排" | `skills/adk-embedded-release-orchestration/SKILL.md` |
| `adk-commit-pr-quality-gate` | 提交与 PR 质量门禁检查 | "提交代码" | `skills/adk-commit-pr-quality-gate/SKILL.md` |
| `adk-grill-with-docs` | 烤问式需求对齐——通过结构化提问消除模糊需求 | "文档审查" | `skills/adk-grill-with-docs/SKILL.md` |
| `adk-code-simplification` | 代码简化——在不改变行为的前提下提高清晰度 | "代码太复杂" | `skills/adk-code-simplification/SKILL.md` |
| `adk-context-engineering` | 上下文工程——优化 Agent 上下文设置 | "上下文不够" | `skills/adk-context-engineering/SKILL.md` |
| `adk-token-context-governance` | 保真省 Token 的上下文读取治理，分层摘要、原文回退与高风险原文门禁 | "省 token" | `skills/adk-token-context-governance/SKILL.md` |
| `adk-repo-drift-remediation` | 仓库漂移治理，面向全仓偏离、冗余、残留、边界不清、文档代码不一致和提交前质量收口 | "仓库漂移" | `skills/adk-repo-drift-remediation/SKILL.md` |
| `adk-chinese-commit-conventions` | 中文 Git 提交规范——适配国内开发团队 | "中文提交" | `skills/adk-chinese-commit-conventions/SKILL.md` |
| `adk-chinese-code-review` | 中文代码审查规范——适配国内团队沟通风格 | "代码审查" | `skills/adk-chinese-code-review/SKILL.md` |
| `adk-repo-prompt-analyzer` | 逆向分析开源项目中的 Prompt/系统指令设计，提取上下文工程模式 | 分析子仓 prompt | `skills/adk-repo-prompt-analyzer/SKILL.md` |
| `adk-skill-deep-analyzer` | 从产品视角深度拆解 AI Skill 的设计意图、独特解法和可借鉴模式 | 深度拆解 skill | `skills/adk-skill-deep-analyzer/SKILL.md` |
| `adk-artifact-gating` | 跨仓库 Artifact 门禁协议——统一标签、状态机与交接规范 | "artifact 门禁" | `skills/adk-artifact-gating/SKILL.md` |
| `adk-pilot-framework` | 跨仓库 Pilot 试跑框架——场景定义、证据收集与门禁验收 | "试跑" | `skills/adk-pilot-framework/SKILL.md` |
| `adk-intake-workflow` | 子仓接入工作流——扫描、分析、决策与治理覆盖 | "接入新仓库" | `skills/adk-intake-workflow/SKILL.md` |
| `adk-bsp-analyst` | BSP 代码分析、架构梳理、历史追溯 | bsp 分析 | `skills/adk-bsp-analyst/SKILL.md` |
| `adk-driver-developer` | 嵌入式驱动实现、联调验证与风险收口 | 驱动开发 | `skills/adk-driver-developer/SKILL.md` |
| `adk-hardware-debugger` | 硬件问题调试、oops 分析 | 硬件调试 | `skills/adk-hardware-debugger/SKILL.md` |
| `adk-planner` | 需求分析、任务拆解、方案设计 | 需求分析 | `skills/adk-planner/SKILL.md` |
| `adk-generator` | 编码实现、单元测试编写 | 编码实现 | `skills/adk-generator/SKILL.md` |
| `adk-evaluator` | 代码评审、质量验证 | 代码评审 | `skills/adk-evaluator/SKILL.md` |

## Optional Skills

| Name | Description | First Trigger | Path |
|---|---|---|---|
| `adk-incident-rca-report` | 线上事故复盘与根因分析闭环 | "线上事故" | `optional-skills/adk-incident-rca-report/SKILL.md` |
| `adk-cross-team-handoff` | 跨团队交接时统一目标、边界和验收责任 | "团队交接" | `optional-skills/adk-cross-team-handoff/SKILL.md` |
| `adk-data-fetch` | 数据获取技能组合——包含邮件获取与网页正文提取 | "获取数据" | `optional-skills/adk-data-fetch/SKILL.md` |
| `adk-email-imap-fetch` | IMAP 邮件获取——从邮箱获取邮件列表和内容 | "获取邮件" | `optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md` |
| `adk-fetch-url-content` | URL 正文提取——从网页提取结构化内容 | "获取网页内容" | `optional-skills/adk-data-fetch/adk-fetch-url-content/SKILL.md` |
| `adk-planning-execution-loop` | 长任务计划审查、分阶段执行、恢复与收口闭环 | "执行计划" | `optional-skills/adk-planning-execution-loop/SKILL.md` |
| `adk-security-supply-chain` | 第三方技能、脚本与参考资产引入前的安全和供应链审查 | "供应链审查" | `optional-skills/adk-security-supply-chain/SKILL.md` |
| `adk-skill-composition-governance` | 治理技能组合、触发优先级、fallback 与弃用关系 | "技能组合" | `optional-skills/adk-skill-composition-governance/SKILL.md` |
| `adk-test-flakiness-triage` | 定位测试波动根因并给出稳定化方案 | "测试波动" | `optional-skills/adk-test-flakiness-triage/SKILL.md` |

## Workflows

| Name | Description | Profiles | Primary Agent | Primary Skill | Path |
|---|---|---|---|---|---|
| `adk-delivery-gate` | agent-dev-kit 通用资产生产交付门禁 | core, embedded-fullstack | `code-review-governor` | `adk-verification-before-completion` | `workflows/adk-delivery-gate/WORKFLOW.md` |
| `feature-delivery` | 新功能从需求收敛到验证评审的交付工作流 | core, embedded-fullstack | `requirements-analyst` | `adk-requirements-triage` | `workflows/feature-delivery/WORKFLOW.md` |
| `bugfix-delivery` | 缺陷复现、根因定位、回归验证和审查闭环工作流 | embedded-fullstack | `application-engineer` | `adk-systematic-debugging` | `workflows/bugfix-delivery/WORKFLOW.md` |
| `release-hardening` | 发布前安全、性能、版本、回滚和放行证据收口工作流 | release-hardening | `build-release-engineer` | `adk-release-versioning` | `workflows/release-hardening/WORKFLOW.md` |
| `runtime-routing` | 运行时技能路由、fallback 边界和 profile 闭包验证工作流 | core, embedded-fullstack | `architecture-planner` | `adk-runtime-router` | `workflows/runtime-routing/WORKFLOW.md` |
| `skill-curation-delivery` | 技能候选筛选、core/optional 归属和触发质量验证工作流 | core, team-core | `requirements-analyst` | `adk-requirements-triage` | `workflows/skill-curation-delivery/WORKFLOW.md` |

## Workflow Matrix

| Workflow | Profiles | Command Risk | Primary Agent | Primary Skill | Supporting Skills | Verification |
|---|---|---|---|---|---|---|
| `adk-delivery-gate` | core, embedded-fullstack | low | `code-review-governor` | `adk-verification-before-completion` | adk-runtime-router, adk-requirements-triage, adk-task-breakdown, adk-test-strategy, adk-code-review-loop, adk-after-action-review, adk-token-context-governance, adk-commit-pr-quality-gate | rtk bash tests/run_all.sh --fail-fast |
| `feature-delivery` | core, embedded-fullstack | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-interface-contract-design, adk-unit-test-embedded, adk-verification-before-completion, adk-code-review-loop | rtk bash tests/test_validate.sh, rtk bash tests/test_workflow_closure.sh |
| `bugfix-delivery` | embedded-fullstack | low | `application-engineer` | `adk-systematic-debugging` | adk-task-breakdown, adk-verification-before-completion, adk-code-review-loop | rtk bash tests/test_workflow.sh, rtk bash tests/test_integration.sh |
| `release-hardening` | release-hardening | medium | `build-release-engineer` | `adk-release-versioning` | adk-test-strategy, adk-code-review-loop, adk-branch-closeout, adk-verification-before-completion, adk-commit-pr-quality-gate | rtk bash tests/test_validate.sh, rtk bash tests/test_profile_coherence.sh |
| `runtime-routing` | core, embedded-fullstack | low | `architecture-planner` | `adk-runtime-router` | adk-verification-before-completion, adk-repo-drift-remediation | rtk bash tests/test_skill_trigger_matrix.sh, rtk bash tests/test_workflow_closure.sh |
| `skill-curation-delivery` | core, team-core | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-commit-pr-quality-gate, adk-verification-before-completion | rtk bash tests/test_catalog.sh, rtk bash tests/test_skill_sop_quality.sh |

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
