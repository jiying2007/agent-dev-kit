# ADK 详细使用指南

本文面向 `agent-dev-kit` 使用者和维护者，说明如何选择 Profile、查找 Agent/Skill/Workflow、执行变更流程、安装或导出资产，以及如何完成验证与发布前收口。

ADK 的核心原则是：**平台中立、单一事实源、资产有主责、流程有证据、变更可审查、发布可回滚。**

> 资产明细不在本文复制维护。Agent/Skill/Workflow 的当前完整列表以 `manifest.json` 为结构化事实源，以 `docs/agent-skill-catalog.md`、`docs/workflow-contract-matrix.md` 和 `docs/reference/skill-routing-matrix.md` 为生成的人类可读视图。

## 1. 定位与边界

`agent-dev-kit` 是平台中立的 Agent/Skill/Profile/Workflow 资产编译与交付控制面。它负责：

- 维护 Agent、Skill、Profile、Workflow 与治理合同；
- 把工程方法压实成可执行、可验证、可回滚的资产；
- 通过显式 `tool_targets` 为受支持运行时生成或安装资产；
- 维护 reference source、freshness、routing、release 与 evidence 契约；
- 为真实 runtime/field campaign 提供平台中立证据结构。

它不负责：

- 实现 LLM 推理循环或 session scheduler；
- 替代具体项目的测试、发布审批或生产运行时；
- 默认写入任何用户运行目录；
- 在 core 中保留迁移期兼容别名、平行 Manifest 或平台专属默认 target。

## 2. 单一事实源

当前结构化 Manifest 的唯一事实源是：

- `manifest.json`
- `manifests/manifest.schema.json`（schema 4.0）

对应的人类可读资产分别位于：

| 类型 | 当前入口 |
|---|---|
| Agent | `agents/<name>/AGENTS.md` |
| Core Skill | `skills/<name>/SKILL.md` |
| Optional Skill | `optional-skills/<name>/SKILL.md` |
| Workflow | `manifest.json:workflows` 与 `workflows/<name>/WORKFLOW.md` |
| Profile | `manifest.json:profiles` |
| Tool Target | `manifest.json:tool_targets` |
| External Handoff | `manifest.json:external_handoff_targets` |
| Governance Contracts | `manifests/*.json` |
| Change Evidence | `docs/changes/<change-id>/` |

不维护第二份结构化 Manifest 镜像。Catalog、matrix 和其它派生文档必须从 canonical source 单向生成，不能反向成为平行 SSOT。

## 3. 命令执行方式

统一入口：

```bash
bash scripts/devkit.sh <command> [options]
```

常用健康检查：

```bash
bash scripts/devkit.sh validate --strict
bash scripts/check-runtime-boundary.sh
bash scripts/devkit.sh target check --all --level static --summary-json
bash scripts/devkit.sh security check --summary-json
bash tests/run_all.sh
```

解释器支持基线为 Python 3.11+。未设置 `ADK_PYTHON_BIN` 时，launcher 按 `python3.12 -> python3.11 -> python3` 选择；发布/认证验证应使用受支持解释器，并可设置 `ADK_REQUIRE_SUPPORTED_PYTHON=1` fail closed。

本机代理包装（例如操作者自己的命令前缀）不是 ADK 运行依赖。active scripts、测试与 GitHub Actions 必须能在普通 runner 上执行。

## 4. Profile 选择

| Profile | 推荐场景 |
|---|---|
| `core` | 通用需求、实现、验证、评审 |
| `personal-core` | 个人通用开发与归档 |
| `team-core` | 团队协作、交接与 review |
| `embedded-fullstack` | SoC/BSP/驱动/RTOS/Linux/产测/现场维护 |
| `release-hardening` | 发布、安全、性能、可靠性与回滚强化 |
| `openspec-driven` | Spec/change/task 驱动交付 |
| `large-refactor` | 大型重构与接口稳定性治理 |
| `incident-response` | 故障响应、RCA 与恢复 |
| `research-intake` | 外部参考候选的只读评估 |

选择规则：

- 不确定时从 `core` 开始；
- 领域能力只在相关 profile 启用，不回流为 core 前提；
- optional skill 必须显式可用，不能被 profile 隐式提升为默认能力；
- profile 解析必须包含 Agent 的 `default_skills` 闭包。

检查 Profile 与 Workflow 闭包：

```bash
bash scripts/check-profile-coherence.sh
bash scripts/check-workflow-closure.sh --profile core
```

## 5. Agent、Skill、Workflow、Profile 的关系

- **Agent**：谁负责，定义 ownership、handoff、质量门禁；
- **Skill**：怎么做，定义方法、触发、证据与失败模式；
- **Workflow**：按什么阶段推进，定义阶段、产物与验证序列；
- **Profile**：当前场景允许使用哪些资产的闭包集合。

一个场景应有一个 primary Skill；supporting/fallback Skill 只能补充，不抢入口。完整场景路由以 `docs/reference/skill-routing-matrix.md` 为准。

生成与检索当前资产视图：

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh catalog find --type agent --keyword review
bash scripts/devkit.sh catalog find --type skill --keyword 需求
bash scripts/devkit.sh catalog find --type workflow --keyword 发布
```

## 6. Routing 使用

当前 routing 事实源在 `manifest.json:routing` 与 `skill_routing_matrix`。路由使用现有 routing IR，不维护第二套路由表。

检查路由相关合同：

```bash
bash tests/test_routing.sh
bash tests/test_routing_ir_contract.py
bash tests/test_skill_trigger_matrix.sh
```

调整路由时优先修改 canonical routing 数据，再重新生成相应人类可读矩阵，并用 positive/negative 场景验证 primary、supporting、fallback、abstain 与 permission 边界。

## 7. Change Set 工作流

可审查变更使用：

```text
docs/changes/<change-id>/
```

至少记录：requirements/proposal、design、tasks、验证证据、review 结论与 negative results。仓库兼容的 lifecycle 命令仍通过统一入口执行：

```bash
bash scripts/devkit.sh propose --change my-change --title "说明"
bash scripts/devkit.sh apply --change my-change
bash scripts/devkit.sh verify --change my-change
bash scripts/devkit.sh review --change my-change --result pass --blockers 0 --majors 0 --minors 0
bash scripts/devkit.sh archive --change my-change
```

未验证的探索结论不能升级为放行证据；失败路径应留下可复核 negative result，避免后续重复试错。

## 8. Install 与 Export

事务安装：

```bash
bash scripts/devkit.sh install plan --tool claude-code --target /tmp/adk-target --mode copy --profile core --output /tmp/adk-plan.json
bash scripts/devkit.sh install apply --plan /tmp/adk-plan.json
bash scripts/devkit.sh install rollback --receipt /tmp/adk-target/.adk-install-receipt.json
```

确定性导出：

```bash
bash scripts/devkit.sh export --target claude-code --profile core --out dist --clean
```

边界：

- `--target` 必须来自 `manifest.json:tool_targets`；
- target adapter 必须显式声明 native path、asset kind、permission 与拒绝条件；
- `dist/` 是可丢弃产物，不是事实源；
- 写真实运行目录前必须具备 dry-run/plan、receipt 与 rollback 边界；
- external handoff target 不等于 direct export target。

当前 direct targets 的支持级别、asset kind 与 contract 以 Manifest 和 `target check` 输出为准，不在本文手工复制状态表。

## 9. Target 验证

静态 contract：

```bash
bash scripts/devkit.sh target check --all --level static --summary-json
```

真实 runtime smoke：

```bash
bash scripts/devkit.sh target smoke --target <target> --stage discovery --profile core --asset-kind skill --runtime-command <read-only-smoke-command>
```

没有 caller-supplied runtime command 时必须返回 `not-run`，不能把 static/fixture 结果冒充 native runtime certification。

## 10. 资产修改准则

### 修改 Agent

检查 ownership、handoff、`default_skills`、profile 闭包与职责重叠。

### 修改 Skill

检查 frontmatter、taxonomy、`activation_mode`、triggers/non-triggers、证据、失败模式与 command risk。

### 修改 Workflow

检查 primary Agent/Skill、supporting Skills、entry/exit evidence、阶段验证与目标 profile 闭包。

### 修改 Profile

保持增量继承，避免重复资产；确保 resolved Agent 的默认 Skill 全部可解析。

### 修改 Manifest

只编辑 canonical JSON；修改后至少运行 strict validate、profile/workflow/routing 相关定向测试，并在需要时重新生成 catalog/matrix。

## 11. 验证分级

| 变更范围 | 最小验证 |
|---|---|
| 纯文档 | `bash scripts/devkit.sh validate --strict` + 相关文档测试 |
| Agent/Skill/Profile/Manifest | strict validate + 定向合同 + `bash tests/run_all.sh --fail-fast` |
| Workflow/Change Set | strict validate + workflow contract/closure |
| install/export/release | product maturity v5 + Software M5 readiness + full regression |
| security/dependency | `bash scripts/devkit.sh security check` + Ruff + dependency audit |
| release candidate | full regression + release check + rollback/rehearsal evidence |

当前完整回归入口：

```bash
bash tests/run_all.sh
```

没有 fresh evidence，不声明完成、可合并、可发布或 M5 certified。

## 12. Security

ADK 自身阻断式安全检查：

```bash
bash scripts/devkit.sh security check --summary-json
```

CI 同时执行固定版本 Python 静态分析和依赖审计。外部安全工具是 CI 能力，不进入 ADK core runtime；不可用时应明确 blocked/unavailable，不能把未执行记为通过。

凭证、token、私钥、用户目录敏感状态不得进入 Agent/Skill/Manifest/日志或 release evidence。

## 13. Evaluation 与真实效果

确定性评测：

```bash
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh eval effect --contract manifests/effect_eval_contract.json --summary-json
```

真实 runtime/campaign 必须显式执行，默认 planning/report-only。Software M5 的正式合同、repository evidence、field pilot 要求以当前 `manifests/*` 和 maturity policy 为准；fixture pass、owner attestation 或静态 target pass 都不能替代 runtime-measured/field evidence。

## 14. Release

发布前：

```bash
bash scripts/devkit.sh release check --summary-json
bash scripts/devkit.sh release build --version 6.0.0 --out dist --summary-json
bash scripts/devkit.sh release runtime-build --profile team-core --out dist --summary-json
```

正式 release identity 必须绑定 exact commit/tree、Manifest/schema 与制品 digest；未绑定 snapshot 不能升级为 release evidence。发布/回滚/重演练必须保留可验证的 artifact 与 rollback anchor。

## 15. 故障排查

| 现象 | 优先检查 |
|---|---|
| strict validate 失败 | schema、runtime boundary、资产引用、生成视图漂移 |
| profile coherence 失败 | 继承重复、Agent default Skill 缺失、workflow 闭包 |
| target check 失败 | target contract、asset kind、native path、permission |
| docs gate 失败 | active 文档是否引用退役或不存在的脚本/测试入口 |
| catalog 有 diff | canonical source 已变化但生成视图未刷新 |
| full regression 波动 | 先区分 deterministic failure 与环境/依赖问题，不用盲目重试掩盖 |

## 16. 维护原则

1. 先复用现有 Agent/Skill/Workflow，再新增。
2. 一项事实只保留一个 canonical source；其它视图生成或引用它。
3. 历史迁移、废弃路径和 negative evidence 留在 change/archive，不回流到 active usage。
4. 不为了兼容保留 alias、双读、双写或平行 SSOT。
5. 不把平台专属路径提升为 core 默认行为。
6. 门禁必须同时有正向和负向语义，且不能把“未运行”记为“通过”。
7. 真实效果优先于资产数量、报告数量或脚本数量。

更详细的当前资产与路由关系请使用生成视图，而不是扩充本文：

- `docs/agent-skill-catalog.md`
- `docs/workflow-contract-matrix.md`
- `docs/reference/skill-routing-matrix.md`
- `docs/commands.md`
