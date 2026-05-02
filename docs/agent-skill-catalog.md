# Agent and Skill Catalog

- generated_at: 2026-05-02T11:18:13Z
- source: manifest.yaml

## Agents

| Name | Role | Path |
|---|---|---|
| `requirements-analyst` | 需求澄清与验收标准固化 | `agents/requirements-analyst/AGENTS.md` |
| `architecture-planner` | 架构设计与技术选型 | `agents/architecture-planner/AGENTS.md` |
| `driver-engineer` | 驱动与外设集成实现 | `agents/driver-engineer/AGENTS.md` |
| `component-engineer` | 组件抽象与中间件实现 | `agents/component-engineer/AGENTS.md` |
| `application-engineer` | 应用层业务与系统编排实现 | `agents/application-engineer/AGENTS.md` |
| `build-release-engineer` | 构建、打包与发布流程 | `agents/build-release-engineer/AGENTS.md` |
| `test-validation-engineer` | 测试设计与验证闭环 | `agents/test-validation-engineer/AGENTS.md` |
| `performance-reliability-engineer` | 性能与可靠性优化 | `agents/performance-reliability-engineer/AGENTS.md` |
| `security-compliance-reviewer` | 安全与合规评审 | `agents/security-compliance-reviewer/AGENTS.md` |
| `code-review-governor` | 代码评审与质量门禁裁决 | `agents/code-review-governor/AGENTS.md` |

## Skills

| Name | Description | First Trigger | Path |
|---|---|---|---|
| `requirements-triage` | 将需求转为可实现、可验证的工程条目 | 收到模糊需求或跨团队需求时 | `skills/requirements-triage/SKILL.md` |
| `adr-writer` | 产出 Architecture Decision Record 并固化技术决策 | 涉及选型、架构调整、权衡讨论时 | `skills/adr-writer/SKILL.md` |
| `task-breakdown` | 将需求拆解为可并行执行的任务包 | 任务过大或多人协作时 | `skills/task-breakdown/SKILL.md` |
| `interface-contract-design` | 定义模块/API/消息接口契约 | 新增或变更跨模块接口时 | `skills/interface-contract-design/SKILL.md` |
| `register-map-design` | 定义寄存器映射与位域文档 | 驱动开发前期或芯片适配时 | `skills/register-map-design/SKILL.md` |
| `driver-bringup-checklist` | 驱动 bring-up 标准检查清单 | 新外设上板、驱动初次联调时 | `skills/driver-bringup-checklist/SKILL.md` |
| `bsp-porting-playbook` | BSP 移植流程与风险控制 | SoC/板卡迁移或内核升级时 | `skills/bsp-porting-playbook/SKILL.md` |
| `rtos-task-design` | RTOS 任务模型与优先级设计 | 新增实时任务或调度异常时 | `skills/rtos-task-design/SKILL.md` |
| `interrupt-dma-patterns` | 中断与 DMA 协作模式设计 | 高吞吐或低时延 I/O 场景 | `skills/interrupt-dma-patterns/SKILL.md` |
| `protocol-stack-integration` | 协议栈接入与状态机整合 | 串口/网络/现场总线协议接入时 | `skills/protocol-stack-integration/SKILL.md` |
| `component-api-stability` | 组件 API 稳定性治理 | 公共组件准备对外复用时 | `skills/component-api-stability/SKILL.md` |
| `cmake-cross-build` | CMake 交叉编译与多目标构建 | 新增目标板或 toolchain 时 | `skills/cmake-cross-build/SKILL.md` |
| `toolchain-debug-openocd-gdb` | OpenOCD + GDB 联调流程 | 硬件断点、烧录、在线调试时 | `skills/toolchain-debug-openocd-gdb/SKILL.md` |
| `static-analysis-c-cpp` | C/C++ 静态分析与缺陷治理 | 质量门禁或疑难 bug 排查时 | `skills/static-analysis-c-cpp/SKILL.md` |
| `systematic-debugging` | 系统化调试流程，面向根因未明的问题定位与修复验证 | 出现真实故障且根因不明确时 | `skills/systematic-debugging/SKILL.md` |
| `unit-test-embedded` | 嵌入式单元测试策略与样例 | 新增逻辑模块或回归缺陷时 | `skills/unit-test-embedded/SKILL.md` |
| `verification-before-completion` | 完成前验证门禁，确保交付声明与证据一致 | 准备声明完成并发起PR前 | `skills/verification-before-completion/SKILL.md` |
| `integration-hil-sil` | HIL/SIL 集成验证编排 | 跨模块联调或发布前验收时 | `skills/integration-hil-sil/SKILL.md` |
| `fault-injection-recovery` | 故障注入与恢复策略验证 | 需要验证韧性与恢复能力时 | `skills/fault-injection-recovery/SKILL.md` |
| `performance-profiling-embedded` | 嵌入式性能剖析与优化路径 | 出现时延抖动、CPU 占用过高时 | `skills/performance-profiling-embedded/SKILL.md` |
| `release-versioning` | 版本策略、变更说明与发布基线 | 里程碑发布、量产切版前 | `skills/release-versioning/SKILL.md` |
| `commit-pr-quality-gate` | 提交与 PR 质量门禁检查 | 准备 commit/PR 或代码评审前 | `skills/commit-pr-quality-gate/SKILL.md` |

## Optional Skills

| Name | Description | First Trigger | Path |
|---|---|---|---|
| `test-flakiness-triage` | 定位测试波动根因并给出稳定化方案 | 回归测试同代码多次执行结果不一致 | `optional-skills/test-flakiness-triage/SKILL.md` |
| `cross-team-handoff` | 跨团队交接时统一目标、边界和验收责任 | 模块即将交接给其他团队维护 | `optional-skills/cross-team-handoff/SKILL.md` |
| `incident-rca-report` | 线上事故复盘与根因分析闭环 | 出现线上故障且需要复盘闭环 | `optional-skills/incident-rca-report/SKILL.md` |
| `artifact-gated-lite` | 高风险变更时使用轻量 artifact 标签与门禁模板固定交付证据 | 涉及公共接口、schema、发布链路等高风险变更 | `optional-skills/artifact-gated-lite/SKILL.md` |
| `planning-execution-loop` | 长任务计划审查、分阶段执行、恢复与收口闭环 | 有书面计划需要持续执行时 | `optional-skills/planning-execution-loop/SKILL.md` |
| `skill-composition-governance` | 治理技能组合、触发优先级、fallback 与弃用关系 | 新增或调整多个 skill 的组合关系时 | `optional-skills/skill-composition-governance/SKILL.md` |
| `security-supply-chain` | 第三方技能、脚本与参考资产引入前的安全和供应链审查 | 引入第三方 skill、agent、脚本或参考资产前 | `optional-skills/security-supply-chain/SKILL.md` |

## Profiles

| Name | Description | Optional | Extends |
|---|---|---|---|
| `core` | 通用研发核心配置（跨模块需求、实现、验证与评审） | false | - |
| `personal-core` | 个人 ~/.codex 生产默认配置（精简核心 + 完成前门禁） | false | core |
| `embedded-fullstack` | C/C++ 嵌入式全栈默认配置（驱动、组件、应用） | false | core |
| `release-hardening` | 发布前强化配置（安全、可靠性、发布治理） | true | - |
| `artifact-gated-lite` | 高风险变更的轻量产物门禁配置（强调可追溯交付证据） | true | core |
| `team-core` | 团队交付配置（责任矩阵、交接、验证与评审） | true | core |
| `openspec-driven` | Spec 驱动变更配置（requirements/design/tasks 与 gdk workflow 对齐） | true | core |
| `large-refactor` | 大型重构配置（边界冻结、API 稳定性、基线对比与回归） | true | core |
| `incident-response` | 事故响应配置（根因定位、复盘、恢复与验证） | true | core |
| `research-intake` | 参考仓吸收配置（候选筛选、组合治理与供应链审查） | true | - |

