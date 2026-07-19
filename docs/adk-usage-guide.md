# ADK 详细使用指南

本文面向 `agent-dev-kit` 使用者和维护者，说明如何选择 Profile、查找 Agent/Skill/Workflow、执行变更流程、安装或转换资产、修改资产并完成验证门禁。

ADK 的核心原则是：平台中立、资产有主责、流程有证据、变更可审查、发布可回滚。

## 1. ADK 是什么

`agent-dev-kit` 简称 ADK，是一套平台中立的 Agent/Skill/Profile/Workflow 资产包。它把工程流程、角色职责、技能方法、交付工作流和验证门禁固化为可维护的源文件，并通过显式声明的 `tool target` 导出到不同运行时；需要外部声明式链路承接的运行体系通过 `external_handoff_targets` 记录，不混入 direct export。

ADK 适合用于：

- 把模糊需求转成可验收的目标、任务和证据。
- 为一次开发、修复、重构、发布或事故响应选择合适的 Agent、Skill 和 Workflow。
- 维护跨项目复用的工程流程和质量门禁。
- 把 curated 资产导出到受支持的运行时目录或中间产物目录。
- 防止历史兼容残留、职责重叠、命名漂移和未经验证的资产进入 active source。

ADK 不负责：

- 替代具体项目的单元测试、集成测试、硬件验证或发布审批。
- 作为某个工具的用户运行目录。
- 默认写入 `~/.codex`、Claude、OpenCode 或其他真实运行环境。
- 在 core 中保留迁移期兼容别名、平台专属 handoff 或隐式默认 target。

## 2. 核心概念

| 概念 | 作用 | 单一事实源 |
|---|---|---|
| Agent | 定义角色主责、所有权、交接边界和质量门禁 | `manifest.json:agents`、`agents/<name>/AGENTS.md` |
| Skill | 定义可复用方法、触发条件、命令模式、证据模板和质量门禁 | `manifest.json:skills`、`skills/<name>/SKILL.md` |
| Optional Skill | 定义默认 profile 不自动启用、需要显式选择的能力 | `manifest.json:optional_skills`、`optional-skills/<name>/SKILL.md` |
| Profile | 定义某个使用场景解析后的 Agent/Skill 资产集合 | `manifest.json:profiles` |
| Workflow | 定义阶段顺序、产物契约、主责 Agent/Skill 和验证序列 | `manifest.json:workflows`、`workflows/<name>/WORKFLOW.md` |
| Change Set | 定义一次可审查变更的 proposal、design、tasks、verify、review 和归档记录 | `docs/changes/<change-id>/` |
| Reference Source | 定义外部资料、官方文档、参考实现和 provenance，不代表运行时启用 | `manifest.json:reference_sources`、`manifests/*` |
| Tool Target | 定义资产导出到某类运行时的格式和目录语义 | `manifest.json:tool_targets` |
| External Handoff Target | 定义由外部声明式链路承接的运行目标，不是 ADK direct export target | `manifest.json:external_handoff_targets` |

当前 target 模型：

- `tool_targets` 包含 `claude-code`、`hermes-agent`、`opencode`，它们是 ADK 可直接 install/export 的目标。
- `external_handoff_targets.codex` 表示 Codex 通过 `~/codex -> ~/.codex` source-to-live 链路承接 ADK 资产，不是 `export --target codex`。
- `reference_sources.openai-developers` 和 `reference_sources.codex-runtime-methods` 只提供引用、freshness、adoption 和边界治理；这些名称不授予 MCP、hook、plugin、hosted service、用户目录写入或 runtime enablement。

命名和边界规则见 `docs/asset-contract-standard.md`。日常使用时可以先记住四条硬规则：

- Agent 表示“谁负责”，不使用 `adk-` 前缀。
- Core Skill 表示“怎么做”，使用 `adk-` 前缀。
- Workflow 表示“按什么阶段推进”，不能替代 Agent 或 Skill。
- Profile 是闭包集合，包含某个 Agent 时，也必须解析到该 Agent 的 `default_skills`。

## 3. 命令执行方式

仓库脚本本身是普通 shell 入口。在普通 shell 中可以直接使用 `bash`：

```bash
bash scripts/devkit.sh validate --strict
bash tests/run_all.sh
```

在本机 Codex 托管会话中，所有 shell 命令必须通过 `rtk` 执行：

```bash
rtk bash scripts/devkit.sh validate --strict
rtk bash tests/run_all.sh
```

本文命令示例默认写成普通 shell 形式。若在本机 Codex 会话里执行，请在前面加 `rtk`。

### 3.1 本机命令、ADK 脚本和 CI 的边界

`rtk` 是本机 Codex 会话的操作者侧包装，不是 ADK 的运行依赖。ADK active scripts、测试脚本和 GitHub Actions 必须能在没有 `rtk` 的普通 runner 上执行。

| 场景 | 推荐写法 | 边界 |
|---|---|---|
| 普通 shell / GitHub Actions | `bash scripts/devkit.sh validate --strict` | ADK 本体必须可脱离本机代理包装运行 |
| 本机 Codex 会话 | `rtk bash scripts/devkit.sh validate --strict` | 只在操作者命令边界加 `rtk` |
| ADK active scripts | `bash`、`python3`、`rg` 等显式依赖 | 不直接调用 `rtk`、用户目录或平台专属 CLI |
| workflow / evidence 文本 | 可记录 `rtk bash ...` | 这是本机执行证据或命令契约，不等于脚本依赖 |

GitHub `validate-test` 失败时，优先用普通 runner 视角复现：

```bash
bash scripts/validate-assets.sh --strict
bash scripts/check-format.sh
bash tests/run_all.sh
```

若错误是 `command not found`，先查 active scripts 是否误引入本机专属命令，再用收窄后的 `PATH` 复现：

```bash
rg -n '(^|[;&|({[:space:]])rtk[[:space:]]+' scripts tests .github
PATH=/usr/bin:/bin bash scripts/validate-assets.sh --strict
PATH=/usr/bin:/bin bash scripts/check-format.sh
PATH=/usr/bin:/bin bash tests/run_all.sh
```

允许 `rtk` 出现在本机操作说明、fixture、Evidence Index 或 workflow 命令契约中；不允许作为 GitHub runner 必需命令。

## 4. 推荐上手路径

第一次使用 ADK，按下面顺序走即可：

| 步骤 | 目的 | 命令 |
|---|---|---|
| 1 | 确认仓库健康 | `bash scripts/devkit.sh validate --strict`、`bash scripts/devkit.sh runtime-boundary` |
| 2 | 查看资产目录 | `bash scripts/devkit.sh catalog build` |
| 3 | 检查 Profile 闭包 | `bash scripts/check-profile-coherence.sh` |
| 4 | 搜索 Skill / Workflow | `bash scripts/devkit.sh catalog find --type skill --keyword 需求`、`bash scripts/devkit.sh catalog find --type workflow --keyword 发布` |
| 5 | 创建可审查变更 | `bash scripts/devkit.sh propose --change my-change --title "说明"` |
| 6 | 修改后验证 | `bash scripts/devkit.sh validate --strict`、`bash tests/run_all.sh` |

## 5. Profile 选择指南

Profile 决定一次使用或导出时启用哪些 Agent 和 Skill。

| Profile | 推荐场景 |
|---|---|
| `core` | 通用需求收敛、实现、验证、评审和完成前门禁 |
| `personal-core` | 个人项目工作，额外需要总结、归档和个人知识沉淀 |
| `team-core` | 团队交接、评审、跨团队协作和沟通治理 |
| `embedded-fullstack` | SoC、BSP、驱动、RTOS/Linux、设备应用、产测、诊断、发布和现场维护 |
| `release-hardening` | 发布前版本、回滚、安全、性能、可靠性和放行检查 |
| `openspec-driven` | 使用 spec/change/task 结构推进需求、设计和实现 |
| `large-refactor` | 大范围重构、接口稳定性、简化治理和回归门禁 |
| `incident-response` | 事故诊断、根因分析、恢复、复盘和安全响应 |
| `research-intake` | 外部实践候选的只读审查配置；必须显式叠加 `adk-external-practice-absorption` 才形成吸收 workflow 闭包 |

选择原则：

- 不确定时先选 `core`。
- 只有涉及设备链路、板级约束、BSP、驱动、产测或现场维护时才选 `embedded-fullstack`。
- 准备发布、回滚或版本放行时叠加 `release-hardening`。
- 需要团队交接或 review 责任明确时选 `team-core`。
- 外部资料先用 `research-intake` 做只读候选评估；进入吸收流程时必须显式传入 `--with-optional-skill adk-external-practice-absorption`，不能由 profile 隐式提升。

检查 Profile 闭包：

```bash
bash scripts/check-profile-coherence.sh
bash scripts/devkit.sh workflow-closure --profile research-intake --with-optional-skill adk-external-practice-absorption
```

该检查会阻止：

- 子 profile 重复声明父 profile 已继承资产。
- profile 包含 Agent 但缺少该 Agent 的 `default_skills`。
- workflow 引用的 Agent/Skill 不在目标 profile 闭包内。

## 6. Agent、Skill、Workflow 如何配合

一次任务通常按下面关系理解：

- Agent 决定主责和交付边界。
- Skill 决定可复用方法和触发条件。
- Workflow 决定阶段顺序和必备证据。
- Profile 决定当前运行或导出的可用资产集合。

典型分流：

| 用户意图 | Primary Skill | 常见 Workflow | 说明 |
|---|---|---|---|
| 需求不清、验收标准模糊 | `adk-requirements-triage` | `feature-delivery` | 可用 `adk-structured-requirements-questioning` 辅助提问 |
| 只要计划、不改文件 | `adk-lightweight-planning` | 无 | 只读计划；用户要求执行时退出该 skill |
| 需要拆解中大型任务 | `adk-task-breakdown` | `feature-delivery` | 依赖已明确的目标和验收边界 |
| 长任务需要计划、检查点和恢复 | `adk-planning-execution-loop` | `feature-delivery` | Optional skill；需要显式可用或安装 |
| Bug 根因不明 | `adk-systematic-debugging` | `bugfix-delivery` | 先定位根因，再修复 |
| 设备日志、core 或调试通道治理 | `adk-embedded-remote-debug-log-triage` / `adk-offline-core-dump-triage` / `adk-embedded-debug-transport` | `bugfix-delivery` | 仅嵌入式/事故响应相关 profile 使用 |
| 提交或 PR 前检查 | `adk-commit-pr-quality-gate` | `adk-delivery-gate` | 提交质量门禁不替代完成前验证 |
| 完成前确认验证证据 | `adk-verification-before-completion` | 任意交付 Workflow | 核对声明、证据和剩余风险 |
| 发布前强化 | `adk-release-versioning` | `release-hardening` | 绑定版本、制品、回滚和放行证据 |
| Skill / Workflow 分类、排序和归属治理 | `adk-skill-composition-governance` | `skill-curation-delivery` | Optional governance skill；场景入口以 routing matrix 为准 |

组合规则：

- 一个场景只应有一个 primary Skill。
- supporting Skill 只能补充检查，不抢入口。
- Agent 和 Skill 名称不能重复表达同一职责。
- Workflow 不能承载具体角色能力，角色能力应下沉到 Agent 或 Skill。
- 历史角色型资产硬切换后不保留 alias。

## 7. 查找和匹配资产

生成索引：

```bash
bash scripts/devkit.sh catalog build
```

生成结果包括：

- `docs/agent-skill-catalog.md`
- `docs/workflow-contract-matrix.md`
- `docs/reference/skill-routing-matrix.md`

按关键词查找：

```bash
bash scripts/devkit.sh catalog find --type agent --keyword review
bash scripts/devkit.sh catalog find --type skill --keyword 需求
bash scripts/devkit.sh catalog find --type optional-skill --keyword 事故
bash scripts/devkit.sh catalog find --type workflow --keyword 发布
```

检查某段用户输入是否命中 Skill：

```bash
bash scripts/devkit.sh match --skill adk-requirements-triage --text "需求不清楚，需要先梳理验收标准"
bash scripts/devkit.sh match --skill adk-systematic-debugging --text "问题根因不明确，需要定位后修复"
```

如果匹配不准，优先检查：

- `SKILL.md` frontmatter 的 `description` 是否准确。
- `triggers` 是否过宽或过窄。
- `non_triggers` 是否覆盖了不该命中的场景。
- `manifest.json` 里 Skill 所属 profile 是否正确。

## 8. 使用 Change Set 推进变更

可审查变更应使用 `docs/changes/<change-id>/`。这比只改文件更稳，因为它会留下目标、设计、任务、验证和评审证据。

生命周期：`propose -> apply -> verify -> review -> archive`，状态顺序是 `proposed -> applied -> verified -> review-passed -> archived`。

常用命令：`bash scripts/devkit.sh propose --change can-fd-bringup --title "新增 CAN-FD bring-up"`、`bash scripts/devkit.sh apply --change can-fd-bringup`、`bash scripts/devkit.sh verify --change can-fd-bringup`、`bash scripts/devkit.sh review --change can-fd-bringup --result pass --blockers 0 --majors 0 --minors 0`、`bash scripts/devkit.sh archive --change can-fd-bringup`。

最小工件要求：

| 文件 | 内容 |
|---|---|
| `proposal.md` | 问题、目标、非目标、充分性、风险和 breaking-change 决策 |
| `design.md` | 接口、兼容、迁移、回滚和边界 |
| `tasks.md` | 任务、owner、范围、验证命令和完成标准 |
| `checklist.md` | 阶段检查项 |
| `verify-report.md` | 命令、退出码、关键输出和结论 |
| `review-report.md` | blocker/major/minor、风险判断和放行结论 |
| `negative-results.md` | 失败尝试、拒绝路径和原因 |

追加命令级证据用 `bash scripts/devkit.sh evidence append --file <negative-results.md> --command "<cmd>" --exit-code <n> --summary "<summary>" --evidence-path <verify-report.md> --layer Workflow --artifact verify-report`。

使用纪律：

- `review` 只接受 `verified` 状态。
- `archive` 默认只接受 `review-passed` 状态。
- 未验证的探索结论可以记录，但不能当作放行证据。
- 失败路径要写入 `negative-results.md`，避免后续重复踩坑。

## 9. 安装与导出

ADK 支持两类交付动作：事务 `install` 和 deterministic `export`。

`install plan` 先计算 ownership、冲突、manifest/source/destination digest 和有效期；`install apply` 只接受完整、未篡改的 ready plan 并生成 receipt；`install rollback` 先预检全部目标，再按 receipt 原子恢复。重复安装的回滚会恢复上一份 receipt；托管资产漂移时不会发生部分删除。

```bash
bash scripts/devkit.sh install plan --tool claude-code --target /tmp/adk-target --mode copy --profile core --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json
bash scripts/devkit.sh install rollback --receipt /tmp/adk-target/.adk-install-receipt.json
```

常用参数：

| 参数 | 说明 |
|---|---|
| `--tool` | `claude-code`、`hermes-agent`、`opencode` |
| `--target` | 安装目标目录 |
| `--mode` | 仅支持 `copy`；`symlink` fail closed且不生成 plan |
| `--profile` | 主 profile |
| `--extra-profile` | 额外叠加 profile，可重复 |
| `--with-optional-skill` | 显式叠加 optional skill，可重复 |
| `--output` | plan JSON 输出路径 |
| `--ttl-minutes` | plan 有效期 |

`export` 用于导出目标工具格式的中间目录，例如 `bash scripts/devkit.sh export --target claude-code --profile embedded-fullstack --out dist --clean`。

安装和导出边界：

- `--target` 必须来自 `manifest.json:tool_targets`。
- Codex 当前不是 direct `tool_targets` 成员；Codex 支持由 `manifest.json:external_handoff_targets.codex` 描述，并通过外部 `~/codex -> ~/.codex` 链路完成 build/plan/apply/smoke。
- 不要把平台专属用户目录写成 ADK core 默认路径。
- 写入真实运行目录前必须有 dry-run、备份或回滚路径。
- `dist/` 是可丢弃产物，不是事实源。
- 事实源始终是 `manifest.json`、`agents/`、`skills/`、`optional-skills/`、`workflows/` 和 `docs/`；`manifest.yaml` 只是兼容镜像。

## 10. 修改 Agent、Skill、Workflow 的准则

修改前先判断资产类型：

| 需要改变什么 | 应修改 |
|---|---|
| 角色主责、handoff、决策权、质量门禁 | Agent |
| 方法步骤、触发条件、命令模式、证据模板 | Skill |
| 阶段顺序、必备工件、验收序列、发布路径 | Workflow |
| 某场景启用哪些资产 | Profile |
| 可选能力是否进入默认路径 | Optional Skill 或 profile membership |

修改 Agent 时检查：

- `agents/<name>/AGENTS.md` 是否清楚说明职责、边界和交付物。
- `manifest.json:agents` 是否同步更新。
- `default_skills` 是否足够覆盖该 Agent 的主责。
- 是否与已有 Agent 发生职责重叠。

修改 Skill 时检查：

- `SKILL.md` frontmatter 至少包含 `name`、`description`、`version`、`last_updated`。
- `manifest.json:skills` 或 `optional_skills` 是否声明 `category`、`lifecycle_order`、`stage_order`、`activation_mode` 和 `pattern`。
- `description` 是否能支撑准确路由。
- `triggers` 和 `non_triggers` 是否清楚。
- 命令、证据、失败模式和质量门禁是否可执行。
- 是否应放在 `skills/` 还是 `optional-skills/`。
- 如果作为场景 primary，`activation_mode` 必须为 `primary`；optional primary 必须在 routing matrix 或 intent 中声明 `availability: optional-skill-required`。

修改 Workflow 时检查：

- primary Agent、primary Skill 和 supporting Skills 是否都在目标 profile 闭包中。
- `workflow_type`、`lifecycle_order`、`entry_conditions` 和 `exit_evidence` 是否同步更新。
- 每个阶段是否有明确输入、输出和完成标准。
- 是否定义了验证命令和 review 产物。
- 是否与 `docs/workflow-contract-matrix.md` 一致。
- 是否与 `docs/reference/skill-routing-matrix.md` 的场景入口一致。

修改 Profile 时检查：

- 子 profile 只声明相对父 profile 的增量。
- 不重复声明已继承资产。
- 每个 resolved Agent 的 `default_skills` 都被 resolved profile 包含。
- 不把专用领域能力误放进 `core`。

修改后运行 `bash scripts/devkit.sh validate --strict`、`bash scripts/check-profile-coherence.sh`、`bash scripts/devkit.sh asset-taxonomy`、`bash scripts/devkit.sh catalog build`、`bash tests/test_catalog.sh`、`bash tests/test_workflow_contract.sh`。涉及 manifest、脚本、profile、workflow 或跨资产重命名时，运行 `bash tests/run_all.sh`。

## 11. 常用验证门禁

| 命令 | 作用 |
|---|---|
| `bash scripts/devkit.sh validate --strict` | 严格校验 manifest、frontmatter、profile 引用、workflow 和资产质量 |
| `bash scripts/devkit.sh validate --quick` | 快速结构检查，适合编辑中间态 |
| `bash scripts/check-profile-coherence.sh` | 检查 profile 继承、重复声明和 default_skills 闭包 |
| `bash scripts/devkit.sh runtime-boundary` | 检查 core 是否保持平台中立，防止平台专属残留 |
| `bash scripts/devkit.sh asset-taxonomy` | 检查 skill/workflow 分类、manifest 物理顺序、profile 生命周期顺序和场景路由矩阵 |
| `bash scripts/devkit.sh official-docs-governance --summary-json` | 检查官方资料 freshness 和提升门禁 |
| `bash scripts/devkit.sh workflow-closure --profile core` | 检查 workflow 引用是否在 profile 闭包内 |
| `bash scripts/devkit.sh workflow-closure --profile research-intake --with-optional-skill adk-external-practice-absorption` | 检查外部实践 workflow 只能由显式 optional skill 完成闭包 |
| `bash scripts/devkit.sh file-modes` | 检查 tracked 文件权限 |
| `bash scripts/devkit.sh catalog build` | 重新生成资产目录、workflow matrix 和 skill routing matrix |
| `bash scripts/devkit.sh test` | 执行全量回归入口 |
| `bash tests/run_all.sh` | 执行测试套件 |

推荐分级：

| 变更范围 | 最小验证 |
|---|---|
| 纯文档说明 | `validate --strict` |
| Agent/Skill/Profile/Manifest | `validate --strict`、`check-profile-coherence.sh`、`asset-taxonomy`、相关 catalog/workflow 测试 |
| Workflow 或 Change Set | `validate --strict`、`asset-taxonomy`、`tests/test_workflow_contract.sh` |
| 安装、转换、运行时边界 | `runtime-boundary`、相关脚本 smoke、`tests/run_all.sh` |
| 发布、推送、交付给运行态 | `tests/run_all.sh`、ready/rollback 证据 |

## 12. 提交前检查

提交前建议执行 `bash scripts/devkit.sh validate --strict`、`bash scripts/check-profile-coherence.sh`、`bash scripts/devkit.sh runtime-boundary`、`bash tests/run_all.sh`、`git diff --cached --check`。在本机 Codex 会话中写成 `rtk bash ...` 和 `rtk git diff --cached --check`。

提交信息格式：

```text
<type>(scope): <中文动词短句>
```

示例：

```text
feat(profile): 收敛资产命名和 profile 闭包
docs(usage): 增加 ADK 中文使用指南
fix(catalog): 修复 workflow matrix 生成格式
```

推送前确认：

- 工作区状态符合预期。
- 所有新增、删除、重命名都已 staged。
- 硬切换时已扫描旧 ID，无残留引用。
- 全量回归通过。
- 如果会同时推送历史未推送提交，需要在交付说明中明确。

## 13. 常见场景

| 场景 | 推荐路径 |
|---|---|
| 小型文档治理 | 选择 `core` 或 `team-core`，用 `adk-requirements-triage` 明确目标和非目标，走 `feature-delivery`，创建 `docs/changes/<change-id>/`，修改后运行 `validate --strict` 并写入 verify/review 证据 |
| 受控 bugfix | 用 `adk-systematic-debugging` 先确认根因，走 `bugfix-delivery`，修复后运行定向测试，再用 `adk-verification-before-completion` 收口 |
| Skill 候选归属 | 使用 `research-intake` 或 `core`，用 `adk-skill-composition-governance` 判断归属，先查现有资产，再决定 `use-as-is`、`adapt-existing`、`build-fresh` 或 `reference-only` |
| 发布前强化 | 叠加 `release-hardening`，检查版本、回滚、安全、性能、可靠性和证据，运行全量回归并记录 release decision |

## 14. 故障排查

| 现象 | 常见原因 | 处理方式 |
|---|---|---|
| `profile coherence` 失败 | 子 profile 重复声明继承资产，或缺少 Agent default Skills | 删除继承重复项，或补齐 resolved profile 所需 Skill |
| catalog 生成后有 diff | `manifest.json` 已变更但目录文档未更新 | 运行 `bash scripts/devkit.sh catalog build` 并审查 diff |
| `workflow contract` 失败 | Workflow 引用的 Agent/Skill 不在 profile 闭包内 | 更新 profile membership 或修正 Workflow contract |
| `runtime-boundary` 失败 | active source 出现平台专属路径、handoff 或运行时写入残留，或 direct/external target 边界混用 | 移到 reference metadata、archive、`external_handoff_targets`，或显式声明 direct tool target 并补转换语义 |
| `file_modes` 失败 | Git index 中的 executable bit 不符合规则 | 检查是否误加执行位，必要时运行 `file-modes --fix` |
| Skill 匹配过宽 | `description` 或 `triggers` 太泛 | 收紧描述，增加 `non_triggers` |
| Skill 匹配不到 | 触发词缺失或 profile 未包含该 Skill | 补触发条件，或调整 profile |
| install/export 结果不对 | target 未声明、profile 选择错误或输出目录未清理 | 检查 `manifest.json:tool_targets`，加 `--clean` 重新导出 |

## 15. 日常最小清单

普通编辑：`bash scripts/devkit.sh validate --strict`、`bash tests/test_catalog.sh`、`bash tests/test_workflow_contract.sh`。

资产或 manifest 变更：`bash scripts/check-profile-coherence.sh`、`bash scripts/devkit.sh asset-taxonomy`、`bash scripts/devkit.sh catalog build`、`bash tests/run_all.sh`。

发布或推送前：`bash tests/run_all.sh`；本机 Codex 运行态收口再执行 `rtk bash ~/codex/scripts/final-ready.sh`。

## 16. 维护原则

- 先复用现有 Agent/Skill/Workflow，再考虑新增。
- 新增资产必须有清楚边界、触发条件、失败模式和验证门禁。
- 历史资产硬切换时删除旧目录和旧 ID 引用，不保留兼容 alias。
- 文档、manifest、catalog、workflow matrix 和 skill routing matrix 必须同步。
- 没有验证证据，不声明完成、可提交、可合并或可发布。
- ADK core 保持平台中立；运行时差异通过 direct `tool_targets`、profile 和 `external_handoff_targets` 表达。OpenAI/Codex 资料可作为 `reference_sources`，但不能成为 core runtime 前提。

## 17. Agent 详细介绍

本节说明当前 ADK 维护的全部 Agent。Agent 表示“谁负责”，重点是主责、非主责、交接对象、默认技能和质量门禁。

| Agent | 定位 | 主责 | 不负责 | 默认 Skill | 质量门禁 |
|---|---|---|---|---|---|
| `requirements-analyst` | 需求澄清、验收标准和范围边界分析 | 需求边界、验收标准 | 代码实现、发布操作 | `adk-requirements-triage`、`adk-task-breakdown` | 目标、非目标、影响面、验收标准和风险必须可验证 |
| `architecture-planner` | 架构方案、模块边界和技术决策规划 | 架构边界、接口决策 | 直接编码、发布签核 | `adk-interface-contract-design`、`adk-adr-writer` | 设计必须包含接口、兼容性、迁移和回退边界 |
| `driver-engineer` | 驱动实现、bring-up 和底层联调 | 驱动实现、bring-up 证据 | 产品需求裁剪、发布放行 | `adk-driver-implementation`、`adk-driver-bringup-checklist`、`adk-systematic-debugging` | 驱动变更必须绑定硬件约束、验证证据和回归路径 |
| `component-engineer` | 组件接口、模块实现和集成边界治理 | 组件接口、模块实现 | 需求验收口径、发布版本策略 | `adk-interface-contract-design`、`adk-component-api-stability` | 组件变更必须保留 API 稳定性和集成验证证据 |
| `application-engineer` | 设备侧应用、上位机工具和业务逻辑实现 | 应用逻辑、工具行为 | 架构最终裁决、发布放行 | `adk-systematic-debugging`、`adk-unit-test-embedded` | 应用行为变更必须包含用户路径、错误路径和回归证据 |
| `build-release-engineer` | 构建、打包、版本发布和回滚链路 | 构建打包、发布回滚 | 需求变更、安全风险豁免 | `adk-release-versioning`、`adk-commit-pr-quality-gate` | 发布必须绑定版本、制品、校验、回滚和放行证据 |
| `test-validation-engineer` | 测试策略、验证证据和完成前门禁 | 测试策略、验证证据 | 功能实现、风险豁免 | `adk-test-strategy`、`adk-verification-before-completion` | 完成结论必须与验证命令、退出码和证据路径一致 |
| `performance-reliability-engineer` | 性能剖析、稳定性和可靠性风险治理 | 性能分析、可靠性风险 | 功能需求裁决、安全签核 | `adk-performance-profiling-embedded`、`adk-fault-injection-recovery` | 性能和可靠性结论必须包含基线、负载条件和对比证据 |
| `security-compliance-reviewer` | 安全、合规、凭据和供应链风险审查 | 安全审查、供应链风险 | 功能实现、发布执行 | `adk-static-analysis-c-cpp`、`adk-commit-pr-quality-gate` | 高风险项必须修复、降级或显式记录风险接受 |
| `external-practice-curator` | GitHub、GitLab、Gitee、官方实践、微信公众号和人工候选的只读来源/重复/合规审查 | 审查材料、负结果、独立 owner handoff | 自批候选、实现代码、安装与发布 | `adk-requirements-triage`、`adk-repo-prompt-analysis` | curator 不能同时充当采纳决策 owner，所有输出保持 report-only |
| `code-review-governor` | 代码审查、反馈闭环和质量放行治理 | 审查分级、放行判断 | 直接修复代码、发布执行 | `adk-code-review-loop`、`adk-commit-pr-quality-gate` | blocker 必须修复或明确风险接受后才能放行 |
| `bsp-analyst` | BSP 代码分析、架构梳理、历史追溯 | BSP 分析、历史追溯 | 驱动实现、发布放行 | `adk-bsp-analysis`、`adk-bsp-porting-playbook` | BSP 结论必须包含入口、依赖、风险和追溯证据 |
| `hardware-debugger` | 硬件故障定位、oops 分析和板级调试证据整理 | 硬件故障定位、oops 分析 | 长期架构设计、发布放行 | `adk-hardware-debugging`、`adk-systematic-debugging` | 硬件调试结论必须包含现象、假设、实验和证据 |

Agent 使用要点：

- 需求、架构、实现、验证、审查和发布必须由不同职责明确接力，不能让单个 Agent 同时裁决所有风险。
- 嵌入式专用 Agent 只在 `embedded-fullstack` 等相关 profile 中启用，不应回流到通用 `core` 前提。
- 修改 Agent 后必须同步检查 `manifest.json:agents`、profile 闭包和 `docs/agent-skill-catalog.md`。

## 18. Skill 详细介绍

本节覆盖主要 live Skill。完整、按 taxonomy 排序的实时列表以 `docs/agent-skill-catalog.md` 为准；场景 primary/supporting/fallback 入口以 `docs/reference/skill-routing-matrix.md` 为准。

| Skill | 适用场景 | 主要产物 / 门禁 | 使用边界 |
|---|---|---|---|
| `adk-runtime-router` | 任务开始前需要判断 primary/supporting/fallback skill，或需要验证 adk-first 路由 | 路由决策、跳过条件、fallback 边界 | 只做路由裁决，不替代具体 Skill 执行 |
| `adk-context-engineering` | 需要优化 Agent 上下文、加载层或提示结构 | 上下文分层方案、加载策略 | 不替代具体业务 Skill |
| `adk-token-context-governance` | 日志、diff、上下文过大，需要保真省 token | 读取分层、摘要边界、原文回退门禁 | 不能牺牲高风险原文证据 |
| `adk-requirements-triage` | 需求不清、范围不明、验收标准缺失、新功能入口 | 目标、非目标、影响面、验收标准、风险 | 不直接实现代码；实现前必须形成可验证条目 |
| `adk-structured-requirements-questioning` | 用结构化提问消除需求或文档模糊点 | 问题清单、澄清结论 | 与 triage 区分：它更偏提问对齐 |
| `adk-repo-prompt-analysis` | 逆向分析参考仓 Prompt/系统指令 | prompt 结构、上下文工程模式、采纳建议 | 只做分析和候选，不直接提升 active rule |
| `adk-skill-deep-analysis` | 从产品视角深度拆解 AI Skill | 八阶段拆解、独特解法、吸收边界 | 不做无审查的直接迁移 |
| `adk-external-practice-absorption` | 多来源外部 Agent、Skill、Workflow 和工程实践吸收 | 来源/重复/许可证/安全审查、独立决策、change、验证、pilot、发布复审和退役证据 | optional skill；不得自动安装、复制、自批或绕过独立 owner decision |
| `adk-lightweight-planning` | 用户明确只要计划、尚未要求写文件或执行 | 轻量计划、行动项、开放问题 | 只读计划，不进入实现流程 |
| `adk-task-breakdown` | 需求已经可描述，但任务过大或需要并行拆分 | 任务包、owner、读写范围、验证命令 | 依赖需求边界；不用于绕过需求澄清 |
| `adk-parallel-agent-governance` | 并行子代理任务分片和整合治理 | scope_read/write、must_not_touch、整合验证 | 不用于边界不清或强耦合任务 |
| `adk-worktree-governance` | git worktree 隔离开发、多分支并行治理 | worktree plan、冲突矩阵、清理规则 | 共享 schema、根配置、lockfile 默认串行 |
| `adk-context-compress-handoff` | 上下文压力高、需要会话接力或恢复提示 | stable/dynamic/evidence/excluded context、resume prompt | 不写长期记忆；长期提升另走 memory/archive 治理 |
| `adk-interface-contract-design` | 模块、API、消息、组件边界需要定义契约 | 接口契约、兼容性、迁移和回退边界 | 依赖需求边界；不负责具体实现 |
| `adk-adr-writer` | 需要固化架构或技术选型决策 | ADR、决策背景、取舍、后果 | 不用于记录临时过程噪音 |
| `adk-component-api-stability` | 组件 API 变更、兼容性治理、集成边界保护 | API 稳定性评估、迁移说明、兼容证据 | 破坏性变更必须显式记录 |
| `adk-register-map-design` | 需要定义寄存器映射、位域、SVD 或硬件接口 | register map、位域规则、验证证据 | 嵌入式硬件语义场景使用 |
| `adk-bsp-analysis` | BSP 代码分析、入口梳理、历史追溯 | BSP 入口、依赖、风险、追溯证据 | 只分析和定位，不承担驱动实现 |
| `adk-driver-implementation` | 嵌入式驱动实现、联调、寄存器/中断/DMA 风险收口 | 驱动实现计划、联调证据、风险清单 | 不裁剪产品需求，不做发布放行 |
| `adk-driver-bringup-checklist` | 驱动 bring-up 前后需要标准检查 | bring-up checklist、硬件约束、回归路径 | 不能替代真实板级或仿真验证 |
| `adk-bsp-porting-playbook` | BSP 移植、板级适配、启动链或设备树迁移 | 移植步骤、依赖矩阵、失败回退 | 需绑定目标板和启动链证据 |
| `adk-rtos-task-design` | RTOS 任务模型、优先级、资源竞争设计 | 任务模型、优先级、同步和死锁预防 | 不用于普通线程模型泛泛讨论 |
| `adk-interrupt-dma-patterns` | 中断、DMA、cache coherency、ring buffer 等协作设计 | ISR/DMA 协作模式、证据模板 | 必须绑定平台约束和验证路径 |
| `adk-protocol-stack-integration` | 协议栈接入、状态机和分层测试 | 协议层次、状态机、集成测试策略 | 不把协议业务逻辑和底层驱动混写 |
| `adk-cmake-cross-build` | CMake 交叉编译、多目标构建和工具链配置 | toolchain file、构建矩阵、产物路径 | 不解决业务代码正确性 |
| `adk-code-simplification` | 在不改变行为的前提下简化代码 | 简化方案、行为保持证据 | 不做功能变更或大范围重构逃逸 |
| `adk-systematic-debugging` | 根因不明的问题、测试失败、异常行为定位 | 现象、假设、实验、根因、修复验证 | 禁止盲改、盲重试和无证据归因 |
| `adk-embedded-debug-transport` | ADB/logcat、SSH、串口、GDB remote、调试探针和厂商 CLI 等设备调试通道治理 | 调试通道矩阵、命令风险、连接证据、回滚锚点 | 不绑定具体工具；写操作、刷写、擦除和重启必须审批 |
| `adk-embedded-remote-debug-log-triage` | 嵌入式串口、boot、dmesg、ADB/logcat、OTA、prog 和现场日志分析 | 日志异常、假设矩阵、下一步探针、知识库历史召回 | 不替代真实复现；日志证据不足时必须列缺口 |
| `adk-offline-core-dump-triage` | 嵌入式 Linux core dump、BuildID、符号和 backtrace 离线分析 | core/binary/symbol 校验、可信 backtrace、根因边界 | 在线调试通道联调不走该 skill |
| `adk-hardware-debugging` | 硬件问题调试、oops 分析 | 现象、假设、实验和证据 | 不替代长期架构设计或发布放行 |
| `adk-performance-profiling-embedded` | 嵌入式性能剖析、瓶颈定位和优化 | 基线、负载条件、对比数据 | 没有基线和测量条件不得下结论 |
| `adk-test-strategy` | 需要测试矩阵、TDD 分级、验证策略 | 测试层级、矩阵、证据要求 | 不直接实现测试，先定义策略 |
| `adk-unit-test-embedded` | 嵌入式单元测试、host test、mock、边界用例 | 单测策略、样例、覆盖证据 | 不替代 HIL/SIL 或真实设备验证 |
| `adk-integration-hil-sil` | HIL/SIL 集成验证编排 | 集成环境、执行记录、设备/仿真证据 | 需要明确硬件、仿真或替代验证边界 |
| `adk-embedded-diagnostic-harness` | prog_tool、diag、strict/env、HIL/SIL 诊断 harness | 诊断 CLI 契约、返回码、证据矩阵 | 不把临时调试脚本伪装成产测工具 |
| `adk-fault-injection-recovery` | 故障注入、恢复策略、回滚和韧性验证 | 故障矩阵、恢复证据、失败处理 | 不用于未定义恢复目标的泛泛测试 |
| `adk-artifact-gating` | 跨仓 Artifact 标签、状态机和交接协议 | artifact 标签、状态、交接记录 | 不替代具体 workflow 验证 |
| `adk-pilot-framework` | 跨仓 Pilot 试跑场景、证据和门禁 | pilot scenario、运行记录、回灌建议 | 试跑通过前不升级默认规则 |
| `adk-verification-before-completion` | 完成前确认声明、命令和证据一致 | 验证清单、命令退出码、证据路径 | 不负责提交质量全审；提交前用 commit gate |
| `adk-chinese-commit-conventions` | 中文 Git 提交规范 | type/scope/summary 检查 | 不替代实际 diff 审查 |
| `adk-chinese-code-review` | 中文代码审查沟通和分级规范 | 中文 review 发现和结论 | 审查语气规范不能降低技术严格度 |
| `adk-code-review-loop` | 独立代码审查、发现分级、修复闭环 | blocker/major/minor、复审结论 | 不直接修复代码；审查与实现职责分离 |
| `adk-repo-drift-remediation` | 全仓偏离、冗余、残留、边界不清治理 | 漂移清单、修复计划、验证证据 | 用于治理，不用于随意格式化全仓 |
| `adk-static-analysis-c-cpp` | C/C++ 静态分析、规则集和缺陷治理 | 静态分析结果、分级、修复或接受记录 | 不能替代编译、单测和运行验证 |
| `adk-commit-pr-quality-gate` | commit/PR 前质量门禁 | staged diff、验证结果、提交风险 | 不替代完成前验证；两者关注点不同 |
| `adk-release-versioning` | 版本策略、变更说明、发布基线 | version decision、changelog、release gate | 发布必须绑定回滚和验证证据 |
| `adk-production-field-readiness` | 量产、产测、烧录、OTA、回滚和现场维护 readiness | readiness matrix、产测/现场证据 | 不具备现场恢复路径时不能放行 |
| `adk-embedded-release-orchestration` | 嵌入式全栈发布编排、制品包、OTA/NAS/产线发布 | 发布编排、制品校验、非覆盖门禁 | command risk 高于普通开发，需回滚路径 |
| `adk-embedded-storage-layout-migration` | 嵌入式存储布局、文件系统和 OTA 迁移治理 | 分区/卷迁移方案、启动日志校验、回滚边界 | 涉及数据保留和非覆盖升级时必须显式验收 |
| `adk-branch-closeout` | 分支收尾、本地合并、PR、保留或丢弃决策 | 分支状态、验证、清理计划 | 不自动执行破坏性清理 |
| `adk-after-action-review` | 任务复盘、lessons、memory candidate 和 codify decision | AAR、风险分级、可提升/不提升结论 | 不静默写入长期 memory |
| `adk-memory-curator` | memory/memories/AGENTS/归档候选治理 | memory candidate、审计报告 | 不直接覆盖 `~/.codex/memories` |
| `adk-archive-governance` | `docs/archive` 元数据、命名、hash、superseded 治理 | 归档检查和修复报告 | 只在归档治理异常时使用 |
| `adk-knowledge-archive` | 把高价值总结、研究、排障和决策沉淀为归档候选 | 脱敏、可检索、可治理归档候选 | 不把一次性过程噪音写入长期归档 |
| `adk-engineering-growth-review` | 基于本地历史和归档做开发者成长复盘 | 趋势、重复问题、训练计划 | 需要限定数据源和隐私边界 |

## 19. Optional Skill 详细介绍

Optional Skill 默认不进入 core profile，需要显式选择或由特定 profile/任务触发。

| Optional Skill | 适用场景 | 主要产物 / 门禁 | 使用边界 |
|---|---|---|---|
| `adk-planning-execution-loop` | 长任务、跨阶段执行、恢复和收口 | 阶段计划、checkpoint、恢复提示 | 小任务不要默认启用 |
| `adk-data-fetch` | 需要组合邮件和网页正文获取能力 | 数据源、获取方式、证据路径 | 只做受控数据获取，不绕过权限或登录 |
| `adk-email-imap-fetch` | 通过 IMAP 获取邮件列表或内容 | 邮件查询条件、结果摘要、证据 | 必须有凭据边界和最小读取范围 |
| `adk-fetch-url-content` | 从 URL 提取网页正文或结构化内容 | URL、正文摘要、提取证据 | 不做大规模抓取或绕过反爬 |
| `adk-test-flakiness-triage` | 测试波动、不稳定 CI、偶发失败定位 | flaky 分类、重试策略、隔离和根因记录 | 不能把不稳定测试简单标记为可忽略 |
| `adk-security-supply-chain` | 第三方 skill、脚本、插件、MCP 或参考资产引入前审查 | 来源、权限、deny-path、回滚、风险结论 | 未完成审查不得启用外部写操作 |
| `adk-cross-team-handoff` | 跨团队交接、责任边界和验收对齐 | 目标、范围、owner、验收责任 | 不替代项目管理审批 |
| `adk-incident-rca-report` | 线上事故、故障复盘、根因分析闭环 | 时间线、5-Why、RCA、纠正预防措施 | 无事实证据不得归因 |
| `adk-skill-composition-governance` | Skill 组合、触发优先级、fallback、弃用关系治理 | primary/supporting/fallback 决策、生命周期判断 | 不解决具体业务任务，只治理组合关系 |

## 20. Workflow 详细介绍

Workflow 表示“按什么阶段推进”，用于规定阶段顺序、主责、支持技能、命令风险和验证证据。

| Workflow | 适用场景 | Profile | 主责 | 阶段和证据重点 | 验证入口 |
|---|---|---|---|---|---|
| `feature-delivery` | 新功能从需求收敛到实现、验证和评审 | `core`、`embedded-fullstack` | `requirements-analyst` + `adk-requirements-triage` | proposal、设计、任务、实现范围、单测/回归、review 结论 | `rtk bash tests/test_validate.sh`、`rtk bash tests/test_workflow_closure.sh` |
| `bugfix-delivery` | 缺陷复现、根因定位、修复、回归和审查 | `embedded-fullstack` | `application-engineer` + `adk-systematic-debugging` | 复现证据、根因假设、实验记录、修复 diff、回归证据 | `rtk bash tests/test_workflow.sh`、`rtk bash tests/test_integration.sh` |
| `release-hardening` | 发布前安全、性能、版本、回滚和放行证据收口 | `release-hardening` | `build-release-engineer` + `adk-release-versioning` | 版本、制品、静态分析、性能可靠性、回滚、branch/PR 门禁 | `rtk bash tests/test_validate.sh`、`rtk bash tests/test_profile_coherence.sh` |
| `skill-curation-delivery` | Skill 候选筛选、core/optional 归属和触发质量验证 | `core`、`team-core` | `requirements-analyst` + `adk-requirements-triage` | 现有资产检索、归属判断、触发质量、提交门禁、完成前验证 | `rtk bash tests/test_catalog.sh`、`rtk bash tests/test_skill_sop_quality.sh` |
| `adk-delivery-gate` | ADK 资产生产、规范化、发布前交付门禁 | `core`、`embedded-fullstack` | `code-review-governor` + `adk-verification-before-completion` | 路由、需求、任务、测试策略、审查、复盘和 token/context 证据齐备后放行 | `rtk bash tests/run_all.sh --fail-fast` |
| `runtime-routing` | 运行时技能路由、fallback 边界和 profile 闭包验证 | `core`、`embedded-fullstack` | `architecture-planner` + `adk-runtime-router` | primary/supporting/fallback 判定、profile 闭包、漂移治理 | `rtk bash tests/test_skill_trigger_matrix.sh`、`rtk bash tests/test_workflow_closure.sh` |

Workflow 选择规则：

- 新增能力优先 `feature-delivery`。
- 缺陷修复优先 `bugfix-delivery`，且必须先证明根因。
- 发布、版本、回滚或制品链路优先 `release-hardening`。
- ADK 资产自身治理优先 `adk-delivery-gate`。
- Skill 新增、迁移、拆分、弃用和归属判断优先 `skill-curation-delivery`。
- 路由、fallback、profile 闭包和运行时边界问题优先 `runtime-routing`。
