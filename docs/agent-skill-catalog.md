# Agent and Skill Catalog

- generated_at: 2026-05-23T08:47:33Z
- source: manifest.yaml

## Agents

| Name | Role | Path |
|---|---|---|
| `requirements-analyst` |  | `agents/requirements-analyst/AGENTS.md` |
| `architecture-planner` |  | `agents/architecture-planner/AGENTS.md` |
| `driver-engineer` |  | `agents/driver-engineer/AGENTS.md` |
| `component-engineer` |  | `agents/component-engineer/AGENTS.md` |
| `application-engineer` |  | `agents/application-engineer/AGENTS.md` |
| `build-release-engineer` |  | `agents/build-release-engineer/AGENTS.md` |
| `test-validation-engineer` |  | `agents/test-validation-engineer/AGENTS.md` |
| `performance-reliability-engineer` |  | `agents/performance-reliability-engineer/AGENTS.md` |
| `security-compliance-reviewer` |  | `agents/security-compliance-reviewer/AGENTS.md` |
| `code-review-governor` |  | `agents/code-review-governor/AGENTS.md` |
| `adk-bsp-analyst` |  | `agents/adk-bsp-analyst/AGENTS.md` |
| `adk-driver-developer` |  | `agents/adk-driver-developer/AGENTS.md` |
| `adk-hardware-debugger` |  | `agents/adk-hardware-debugger/AGENTS.md` |
| `adk-planner` |  | `agents/adk-planner/AGENTS.md` |
| `adk-generator` |  | `agents/adk-generator/AGENTS.md` |
| `adk-evaluator` |  | `agents/adk-evaluator/AGENTS.md` |

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
| `adk-integration-hil-sil` | HIL/SIL 集成验证编排 | "集成测试" | `skills/adk-integration-hil-sil/SKILL.md` |
| `adk-fault-injection-recovery` | 故障注入与恢复策略验证 | "故障注入" | `skills/adk-fault-injection-recovery/SKILL.md` |
| `adk-performance-profiling-embedded` | 嵌入式性能剖析与优化路径 | "性能分析" | `skills/adk-performance-profiling-embedded/SKILL.md` |
| `adk-release-versioning` | 版本策略、变更说明与发布基线 | "版本发布" | `skills/adk-release-versioning/SKILL.md` |
| `adk-production-field-readiness` | 嵌入式量产、产测、烧录、诊断、OTA、回滚与现场维护 readiness | "量产" | `skills/adk-production-field-readiness/SKILL.md` |
| `adk-commit-pr-quality-gate` | 提交与 PR 质量门禁检查 | "提交代码" | `skills/adk-commit-pr-quality-gate/SKILL.md` |
| `adk-grill-with-docs` | 烤问式需求对齐——通过结构化提问消除模糊需求 | "文档审查" | `skills/adk-grill-with-docs/SKILL.md` |
| `adk-code-simplification` | 代码简化——在不改变行为的前提下提高清晰度 | "代码太复杂" | `skills/adk-code-simplification/SKILL.md` |
| `adk-context-engineering` | 上下文工程——优化 Agent 上下文设置 | "上下文不够" | `skills/adk-context-engineering/SKILL.md` |
| `adk-token-context-governance` | 保真省 Token 的上下文读取治理，分层摘要、原文回退与高风险原文门禁 | "省 token" | `skills/adk-token-context-governance/SKILL.md` |
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

## Profiles

| Name | Description | Optional | Extends |
|---|---|---|---|
| `core` | 嵌入式全栈开发核心配置（需求、架构、实现、验证与评审） | false | - |
| `release-hardening` | 发布加固配置（安全审查、性能优化、合规检查） | false | - |
| `personal-core` | 个人 ~/codex 声明式交付配置（核心功能 + 发布检查） | false | core |
| `embedded-fullstack` | 嵌入式全栈开发配置（芯片/板级、启动链、BSP、驱动、组件、应用、工具、验证、量产和现场维护） | false | core |
| `team-core` | 团队协作配置（交接/验证/评审） | false | core |
| `openspec-driven` | Spec 驱动开发配置（需求/设计/任务链路） | false | core |
| `large-refactor` | 大型重构配置（API 稳定性 + 代码简化） | false | embedded-fullstack |
| `incident-response` | 线上事故响应配置（根因/复盘/恢复） | false | - |
| `research-intake` | 参考仓吸收配置（候选筛选与审查） | false | - |
