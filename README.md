# Global Dev Kit

面向软件研发的全局 Agent/Skill 资产包，默认聚焦嵌入式全栈（Linux Embedded + MCU Baremetal/RTOS），同时支持跨工具分发与流程化交付。

## 1. 核心能力

- 多工具安装：`codex` / `claude-code` / `hermes-agent` / `opencode`，支持 `--tool auto` 自动检测。
- Profile 分层：`core`（通用核心）+ `embedded-fullstack`（默认）+ `release-hardening` / `artifact-gated-lite`（可选叠加）。
- 可选技能库：`optional-skills/` 提供按需安装能力，不污染默认 profile。
- 资产转换：按目标工具导出目录结构与元数据（`scripts/convert_assets.sh`）。
- 资产目录索引：`catalog` 生成 Agent/Skill/Profile 可检索目录。
- 触发匹配：`match` 根据输入文本做 skill 触发判断（正/反触发）。
- 命令化工作流：`propose/apply/verify/review/archive`，沉淀提案、设计、负结果、验证、评审与归档工件。
- 阶段流转门禁：强制 `proposed -> applied -> verified -> review-passed -> archived`。
- 质量门禁：结构校验、格式一致性检查、内容反模板化检查、安装回归、转换回归、workflow smoke。
- 质量分级：`manifest.yaml` 内置 `quality_tiers`（`p0/p1/p2`），`--strict` 强制校验资产分级完整性与合法性。

## 2. 目录结构

- `agents/`：角色化 Agent 定义（每个角色一个目录）
- `skills/`：流程技能单元（frontmatter + workflow）
- `optional-skills/`：可选技能（仅按需安装/导出）
- `scripts/`：安装、转换、校验、工作流命令
- `tests/`：回归与 smoke 测试
- `docs/`：使用手册、命令说明、工作流说明、场景 runbook
- `.github/workflows/`：CI 与发布流水线
- `manifest.yaml`：单一资产注册源（tool_targets/profiles/quality_tiers/agents/skills/optional_skills）

## 3. 快速开始

```bash
cd global-dev-kit
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh validate --quick
bash scripts/devkit.sh install --tool auto --mode symlink --profile embedded-fullstack
```

常用命令：

```bash
# 列出支持工具与 profile
bash scripts/install_assets.sh --list-tools
bash scripts/install_assets.sh --list-profiles
bash scripts/install_assets.sh --list-optional-skills

# 安装 core + 发布强化 profile
bash scripts/devkit.sh install --tool codex --target ~/.codex --profile core --extra-profile release-hardening

# 安装 profile 并叠加可选技能
bash scripts/devkit.sh install --tool codex --profile core --with-optional-skill incident-rca-report

# 高风险变更：叠加轻量 artifact 门禁
bash scripts/devkit.sh install --tool codex --profile core --extra-profile artifact-gated-lite --with-optional-skill artifact-gated-lite

# 导出到 Claude Code 结构
bash scripts/devkit.sh convert --target claude-code --profile embedded-fullstack --out dist --clean

# 生成目录索引并按关键词检索
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type skill --keyword bring-up

# 输入文本触发匹配
bash scripts/devkit.sh match --skill requirements-triage --text "收到模糊需求或跨团队需求时"

# 工作流命令（动作式流程）
bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"
bash scripts/devkit.sh apply --change can-fd-bringup
bash scripts/devkit.sh verify --change can-fd-bringup
bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 1
bash scripts/devkit.sh archive --change can-fd-bringup
```

`propose` 强制模板检查项：
- 单问题陈述（避免一次改动捆绑多个无关问题）
- 上下文充分性检查（接口/风险/验证方式）
- Core/Optional 边界检查（通用能力 vs 场景化能力）
- 变更重复性检查（避免重复方案）
- Breaking Change 检查（迁移/回退）

## 4. Agents 一览（10）

| Agent | 职责 | 典型输出 |
|---|---|---|
| `requirements-analyst` | 需求澄清、边界冻结、验收标准固化 | 需求条目、验收标准、非目标清单 |
| `architecture-planner` | 架构与选型决策、模块边界定义 | 架构草图、决策记录、接口草案 |
| `driver-engineer` | 外设驱动实现与 bring-up | 初始化流程、寄存器访问策略、联调记录 |
| `component-engineer` | 组件抽象与中间件封装 | 组件 API、适配层、集成说明 |
| `application-engineer` | 业务状态机与系统编排实现 | 应用逻辑、错误恢复流程、任务协作设计 |
| `build-release-engineer` | 构建、制品、发布链路治理 | 构建脚本、版本清单、发布说明 |
| `test-validation-engineer` | 测试策略与验证闭环 | 测试矩阵、验证报告、缺陷清单 |
| `performance-reliability-engineer` | 性能剖析与可靠性强化 | 瓶颈定位、优化建议、稳定性报告 |
| `security-compliance-reviewer` | 安全基线与合规检查 | 风险清单、整改建议、合规结论 |
| `code-review-governor` | 代码评审与质量门禁裁决 | 评审意见、门禁结果、合并建议 |

## 5. Skills 一览（22）

| Skill | 用途 | 典型触发 |
|---|---|---|
| `requirements-triage` | 需求结构化与验收定义 | 需求模糊、跨团队协作 |
| `adr-writer` | 技术决策沉淀 | 选型分歧、架构调整 |
| `task-breakdown` | 任务拆分与并行规划 | 任务过大、多人协作 |
| `interface-contract-design` | 跨模块接口契约设计 | 公共接口新增/变更 |
| `register-map-design` | 寄存器映射与位域设计 | 驱动前期建模 |
| `driver-bringup-checklist` | 驱动上板调试 checklist | 新外设第一次联调 |
| `bsp-porting-playbook` | BSP 移植流程与风险控制 | 板卡迁移、内核升级 |
| `rtos-task-design` | RTOS 任务与调度模型设计 | 实时任务新增/异常 |
| `interrupt-dma-patterns` | ISR 与 DMA 协同模式 | 高吞吐、低时延 I/O |
| `protocol-stack-integration` | 协议栈接入与状态机整合 | 串口/网络协议接入 |
| `component-api-stability` | API 稳定性与兼容治理 | 组件发布前审查 |
| `cmake-cross-build` | CMake 交叉构建治理 | 新 toolchain/目标板接入 |
| `toolchain-debug-openocd-gdb` | OpenOCD/GDB 联调流程 | 在线调试、断点排障 |
| `static-analysis-c-cpp` | C/C++ 静态分析缺陷治理 | 质量门禁、疑难问题排查 |
| `systematic-debugging` | 系统化调试与根因收敛 | 根因未明、回归失败难定位 |
| `unit-test-embedded` | 嵌入式单元测试设计 | 新模块开发、回归修复 |
| `verification-before-completion` | 完成前验证门禁 | 准备声明完成、提交或发起 PR |
| `integration-hil-sil` | HIL/SIL 集成验证 | 发布前联调、系统级验收 |
| `fault-injection-recovery` | 故障注入与恢复验证 | 韧性与容错能力验证 |
| `performance-profiling-embedded` | 性能剖析与优化 | CPU 占用高、时延抖动 |
| `release-versioning` | 发布版本与变更治理 | 里程碑切版、量产发布 |
| `commit-pr-quality-gate` | commit/PR 合规门禁 | 提交前、合并前检查 |

## 6. Optional Skills（4）

| Skill | 用途 | 典型触发 |
|---|---|---|
| `test-flakiness-triage` | 测试波动定位与稳定化 | 同代码多次回归结果不一致 |
| `cross-team-handoff` | 跨团队交接清单与责任闭环 | 模块交接、Owner 变更 |
| `incident-rca-report` | 故障复盘与 RCA 报告沉淀 | 线上事故复盘闭环 |
| `artifact-gated-lite` | 高风险变更的轻量 artifact 标签与门禁模板 | 涉及共享契约/发布链路且需可追溯交付 |

## 7. 场景工作流推荐

- 需求到交付：`requirements-analyst -> architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`
- 新外设 bring-up：`requirements-analyst -> driver-engineer -> component-engineer -> test-validation-engineer`
- BSP 迁移：`architecture-planner -> driver-engineer -> build-release-engineer -> test-validation-engineer`
- 发布收口：`test-validation-engineer -> security-compliance-reviewer -> build-release-engineer -> code-review-governor`
- 高风险变更门禁：`architecture-planner -> application-engineer -> test-validation-engineer -> code-review-governor`

建议配套技能：
- 需求阶段：`requirements-triage` + `task-breakdown`
- 设计阶段：`adr-writer` + `interface-contract-design`
- 调试阶段：`systematic-debugging` + `test-flakiness-triage`（可选）
- 验证阶段：`unit-test-embedded` + `integration-hil-sil` + `verification-before-completion` + `commit-pr-quality-gate`
- 高风险变更：`artifact-gated-lite`（可选）+ `verification-before-completion` + `commit-pr-quality-gate`

场景手册入口：
- `docs/runbooks/feature-delivery.md`
- `docs/runbooks/driver-bringup.md`
- `docs/runbooks/release-hardening.md`
- `docs/runbooks/artifact-gated-delivery.md`

## 8. 测试与发布

```bash
# 全量回归（validate/content-quality/install/convert/workflow/catalog/trigger-matrix）
bash scripts/devkit.sh test

# 格式一致性
bash scripts/check_format.sh
```

CI：`.github/workflows/ci.yml`（校验 + 格式 + 回归）

Release：`.github/workflows/release.yml`（验证后构建多工具 dist bundle）

## 9. 兼容说明

- 旧命令 `scripts/sync_codex_assets.sh` 仍可用（内部已转发到新安装器）。
- 新增 profile 采用“继承 + 叠加”模型，支持按场景组合安装。
- 新增 optional skill 采用“按需注入”模型，不影响默认 profile 解析。
- `manifest.yaml` 是唯一事实源，变更 Agent/Skill 后请先执行 `validate --strict`。
- Agent 资产新增“场景输入样例 + 输出样例（pass/needs-fix）”门禁，未满足会在 `tests/test_asset_content_quality.sh` 失败。

## 10. 独立性说明

- 本仓库无 git submodule、无外部仓库脚本依赖。
- 所有命令仅基于当前仓库文件与本地 shell 工具执行。
- 若后续新增能力，需同时补充本地测试，保证离线可用、可验证。

更多细节见：
- `docs/usage.md`
- `docs/commands.md`
- `docs/workflows.md`
- `docs/runbooks/`
- `docs/reference-adoption.md`
