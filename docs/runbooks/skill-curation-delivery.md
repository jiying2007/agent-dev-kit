# Skill Curation Delivery Runbook

## 适用场景

- 需要从候选技能池中筛选、吸收并落地到当前工程能力目录。
- 需要明确技能是 `global-ready` 还是 `project-bound`，避免错误并入 core。

## 推荐 Agent 链

`requirements-analyst -> architecture-planner -> code-review-governor`

## 推荐 Skill 组合

- `adk-requirements-triage`
- `adk-task-breakdown`
- `adk-commit-pr-quality-gate`
- `adk-verification-before-completion`

## 命令模板

```bash
bash scripts/devkit.sh catalog build
bash scripts/devkit.sh match --skill adk-requirements-triage --text "<候选技能描述>"
bash scripts/devkit.sh validate --strict
bash scripts/devkit.sh review --change <change-id> --result pass --blockers 0 --majors 0 --minors 0
```

## 执行纪律

- 每个候选技能必须给出归属结论：`core` / `optional` / `reject`。
- 必须声明安装范围：`global-ready` 或 `project-bound`。
- 必须记录依赖边界：是否依赖项目内脚本、数据目录或私有上下文。
- 候选必须证明有稳定骨架和重复价值；一次性任务、变化过大的流程或纯领域案例默认不沉淀为 Skill。
- 候选技能文档推荐使用结构化章节：`what-to-do` 与 `supporting-info`，降低路由歧义与冗余解释成本。
- 来源文章、教程或第三方 Skill 只能提供方法候选；不得把原文、营销 claims、项目名热度或未审查代码复制进 core。
- 团队内部 Skill 仓库、市场或私有 registry 只能作为分发候选；进入 adk 前仍需逐项完成 owner、license、版本锚点、安全扫描、人工审批和回滚路径审查。
- 从真实使用中演化 Skill 时，必须同时保留成功样例的不变量和失败样例的修复目标；不得只根据单次失败把局部补丁写进长期 Skill。
- 平台特定 Skill frontmatter、hook、slash command、allowed-tools、fork/context、动态命令注入或 marketplace 字段只能作为兼容线索；进入 adk 时必须映射到本仓的 `SKILL.md` frontmatter、manifest、profile 和验证脚本，不保留不可验证的平台私有语义。
- 研发场景热门 Skill 榜单只能用于发现候选能力，不得因“热门/推荐/高 star”直接新增 core Skill；必须先证明与现有 adk Skill 不重复，并通过 reuse threshold。
- `reuse-before-rebuild` 是新增 Skill 前的硬门禁：先记录 `existing_asset_search` 和 candidate assets；能 `use-as-is` 或 `adapt-existing` 时不得 `build-fresh`。
- Skill 正文优先沉淀稳定指令；配套脚本不是默认选项。只有任务需要确定性执行、依赖边界可声明、可 dry-run 或测试，且不引入未审查外部 API、凭据或平台私有语义时，才允许进入 `scripts/` 或等价可执行资产。

## Skill 结构契约（推荐）

- `what-to-do`：只写行动步骤、输入输出和完成判据。
- `supporting-info`：集中放约束、背景、反例与兼容说明。
- 两类信息分区后，优先让路由和执行读取 `what-to-do`，减少上下文开销。
- `SKILL.md` 是岗位 SOP 入口，不是百科全书；长背景、案例、领域规则和失败样例进入 `references/`，并保留原始证据路径。
- Skill 应保持原子化：一个 Skill 负责一类稳定任务；跨 Skill 编排交给 Agent、Workflow 或 composition governance，不在 Skill 正文里隐式调用另一个 Skill。

## 模式选择

常见结构模式按目标选择：知识规范用 `Tool Wrapper`，固定产物用 `Generator`，质量评估用 `Reviewer`，上下文不足先问清楚用 `Inversion`，多阶段交付用 `Pipeline`。混合模式必须说明 primary pattern 和硬门禁，不能只靠“不要跳步”这类自然语言约束。

涉及评分、计数、格式化、schema 校验、批量状态判定或质量分级的 Skill，必须声明 `deterministic_source_of_truth`。脚本、模板、schema 或检查清单输出是唯一依据；Agent 不得重算、调分、补项或软化失败结论。

生成型或资产型 Skill 必须把模型输出视为未可信候选，而不是最终产物。合格的资产流水线至少声明 job manifest、provenance/hash、结构校验、语义 QA、局部 repair 和最终打包/发布责任人。子代理可以生成候选、记录 QA note 或定位失败范围，但 truth commit、manifest/package 写入和最终 provenance 归档必须由父控制面或确定性脚本集中完成。

自动结构校验通过不等于语义通过。图像、文档、配置包、发布包和其他固定格式产物必须同时有机器可检查的格式门禁和人工/规则化语义验收；修复失败时只重跑最小失败范围，并保留已通过产物与对应证据。

## 演化与分发门禁

Skill 更新不是文案改写，必须走候选验证：

1. 证据分组：按 Skill、任务类型和失败模式归类会话、工单或测试证据。
2. 不变量提取：先标出已成功路径中不能破坏的步骤、输入输出和 done criteria。
3. 候选更新：只修改能解释重复失败的最小规则、模板或脚本边界。
4. 对照验证：用同一批代表性任务比较当前版本与候选版本，至少覆盖一条成功保持样例和一条失败修复样例。
5. 单调发布：候选未证明更稳时只归档为 `candidate`，不得进入 `core`、`profile` 或私有 registry 默认频道。
6. 分发审计：私有 registry、namespace、token 登录和管理员审核只解决分发问题，不替代 adk 的供应链与运行态门禁。

## Skill Factory 边界

从重复工作流自动生成 Skill 的能力只能作为候选发现机制，不能直接写入 core 或默认 profile。

合格流程必须是：

1. `observe`：只记录重复动作、工具组合、失败修复和用户明确提到的固定流程，不采集密钥、隐私原文或一次性草稿。
2. `propose`：给出候选 Skill 名称、适用场景、捕获步骤、反模式、依赖边界和风险等级。
3. `confirm`：用户或维护者确认是否生成 `SKILL.md`、脚手架或仅归档。
4. `generate`：生成内容进入草稿或候选目录，不直接注册到生产 manifest。
5. `validate`：通过重复价值、触发边界、冲突检查、供应链检查和至少一条代表性任务验证后才允许晋级。

自动沉淀的 Skill 必须保留反例和失败修复目标。只根据“经常做过”生成的流程，若没有稳定 done criteria、验证命令和回退方式，结论固定为 `reference-only` 或 `candidate`。

## Skill 覆盖审计

外部文章中的 Skill 分类、榜单或团队实践只能用于覆盖缺口审计：

- 库/API 参考、产品验证、数据分析、业务自动化、脚手架、代码质量、CI/CD、故障 runbook 和基础设施运维可作为候选类别。
- 类别缺口不等于必须新增 Skill；优先检查是否已由现有 ADK Skill、runbook、workflow 或模板覆盖。
- 使用量、触发率和失败率可作为迭代证据，但不能替代质量门禁。
- hook、slash command、动态配置和插件脚手架属于运行态能力，默认走 plugin/MCP/供应链边界，不写进普通 Skill。
- “最值得装”“爆款”“神技”这类榜单只进入候选发现；缺少 owner、license、版本锚点、权限边界和验证样例时，结论固定为 `reference-only`。
- 垂直业务自动化 Skill 只有在能拆清接口适配层、核心逻辑层、数据/外部依赖层，并声明 I/O schema、验证规则、错误等级、缓存/去重/断点续传策略、密钥来源和人工审批点后，才可进入候选实现。

## 观察仓库抽样吸收

对仍在快速更新的外部 skill/agent 仓库，默认使用 sampled watch，而不是恢复全量子仓或安装运行态。每次抽样必须把外部能力先归入以下 lane，再决定是否改 ADK 资产：

| Lane | 典型来源 | 可吸收内容 | 默认落点 | 禁止事项 |
|---|---|---|---|---|
| requirements-and-domain-modeling | `mattpocock/skills` 等需求/建模类 skill | 术语表、实体/状态、非目标、验收样例和实现前拷问契约 | `adk-requirements-triage` 或需求模板 | 不复制外部 skill 文本，不把单次 PRD 写成 core 规则 |
| review-contract | `mattpocock/skills`、`superpowers` 等 review 能力 | spec verdict、quality verdict、cannot-verify-from-diff、out-of-scope suggestion 处理 | `adk-code-review-loop` | 不把 reviewer 意见当自动修复命令 |
| lifecycle-gate | `addyosmani/agent-skills` 等生命周期/质量门禁 | eval、security、release、incremental implementation 或 hardening gate 的新增差异 | workflow/runbook/manifest | 不重复已有 ADK 生命周期流程 |
| catalog-discovery | awesome/marketplace/skill-pool 仓库 | 候选发现、分类、license/owner 线索 | discovery report / adoption matrix | 不安装 CLI，不全量导入 skill pool |
| runtime-security-review | ECC、Composio、hooks/MCP/tooling 仓库 | install surface、hooks、MCP、credentials、data retention、deny-path、rollback 风险 | `external_agent_pattern_contracts.json` / security review report | 不启用外部 runtime，不写全局目录，不接入凭证 |

抽样吸收步骤：

1. 先查 `subrepos/adoption-matrix.md` 和 `manifests/subrepo_lifecycle.json`，确认该来源是否已吸收、移除、watch 或 archive-only。
2. 用 `reuse-before-rebuild` 判断是否能增强现有 skill/runbook/manifest；能合并时不得新增 skill。
3. 对每个候选机制记录 `source repo`、`sampled capability`、`local existing asset`、`decision`、`target asset`、`forbidden action` 和 `verification`。
4. 只有发现 ADK 未覆盖的新契约，才允许修改 ADK 资产；否则写入 `no-new-absorption` 或 `archive-only`。
5. 含 hooks、MCP、browser、hosted service、credentials、local ports、memory injection 或 open-world writes 的来源，必须先停在 `runtime-security-review`。

最小报告字段：

```md
| Source | Lane | Decision | Absorbed Mechanism | Target Asset | Forbidden Action | Verification |
|---|---|---|---|---|---|---|
```

## 平台兼容吸收

吸收 Claude Code、Codex、TRAE、OpenClaw 或其他平台的 Skill 教程时，先做字段映射：

| 平台概念 | adk 处理 |
|---|---|
| `allowed-tools` / tool allowlist | 转为安全供应链或 MCP tool-call policy，不直接授权 |
| `context: fork` / sub-agent | 转为任务契约、并行治理或 workflow stage |
| `disable-model-invocation` / manual-only | 转为触发边界、non-trigger 和人工审批门槛 |
| 动态命令注入 | 默认高风险，必须有确定性脚本、脱敏和原文证据 |
| marketplace/install command | 保持 report-only，先做来源、license、owner 和 rollback 审查 |
| `command` / `capabilities` / `mcp_servers` / 环境变量注入 | 拆为脚本准入、MCP/tool policy 和供应链审查，不直接继承平台权限 |

平台兼容审查还必须覆盖 runtime 轴：discovery timing、项目规则优先级、memory/context injection、sub-agent delegation、sandbox/approval、hooks 和工具权限。只有目标宿主验证通过的行为才能标为兼容；同名字段或同一份 `SKILL.md` 不代表跨平台语义一致。

## 候选筛选模板

```md
- Candidate Skill:
- Install Scope (global-ready/project-bound):
- Core/Optional Decision:
- Dependency Boundary:
- Pattern Decision:
- Asset Pipeline Boundary (manifest/provenance/QA/repair, if any):
- Evolution Evidence (success invariants/failure fixes):
- Distribution Boundary (local/private-registry/public):
- Routing Triggers:
- Evidence:
```

## 验收门禁

- `proposal.md` 必须包含归属决策与安装范围。
- `proposal.md` 必须说明为何不是 `REFERENCE_ONLY`，以及是否已有等价 Skill 可合并。
- 新建 Skill 前必须附 `templates/governance/reuse-before-rebuild-decision.md` 等价字段；缺少 `existing_asset_search` 或 `build_fresh_reason` 时不得进入 core/optional。
- 触发词路由必须可解释，且不与现有核心技能冲突。
- 缺少依赖边界声明或归属结论时，结论固定为 `needs-fix`。
