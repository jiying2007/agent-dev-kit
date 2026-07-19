# 变更提案：intent-boundary-governance-v2

## 来源与 owner decision

- source：`https://github.com/mattpocock/skills`
- source revision：`9603c1cc8118d08bc1b3bf34cf714f62178dea3b`
- comparison base：`v1.1.0`（peeled commit `d574778f94cf620fcc8ce741584093bc650a61d3`）
- retrieved_at：`2026-07-19`
- license：MIT；本变更只吸收方法与合同，不复制上游 Skill 正文或代码。
- owner decision：用户于当前会话明确批准按评估建议落地；决策为 `ENHANCE`，目标为既有 ADK/Codex 合同，禁止安装、整仓导入或恢复 submodule。
- review status：source candidate 继续保持 `review-required`；本 proposal 是独立 owner 批准后的实现工件，不把 candidate 改写为自动批准状态。

## 问题陈述（单问题）

ADK 已有 Skill 路由、通用 task package、长任务、并行、架构规划和 worktree/retention 治理，但“调用意图、工作项权限、扫描扩域、原型保留”仍分散在自然语言中：

1. 没有平台中立的 `invocation_mode` SSOT，Claude/Codex metadata 可能使用不同语义或旧格式。
2. `adk-task-package-schema-v1` 不能区分 `decision|research|prototype|implementation`，也不能机械阻止研究或原型直接取得实现权限。
3. 架构评审没有确定性的默认扫描落点和扩域理由字段，容易从局部任务漂移为全仓重构。
4. 原型缺少统一 provenance、保留期限和清理 owner 合同，保留或丢弃依赖临时判断。

以上都是同一个治理缺口：意图与权限边界没有成为可验证的声明式合同。

## 目标

1. 新增平台中立 Skill invocation contract：`implicit|explicit-only`，目标 adapter 显式映射，默认不把平台私有字段写进 ADK core。
2. 将 `adk-task-package-schema-v1` 硬切为 `adk-task-package-schema-v2`，强制工作项类型、待解决问题、证据、实现权限、退出门、handoff 和 retention 决策。
3. 把 architecture hotspot/YAGNI 范围选择并入现有 `architecture-planner`，默认只审用户范围、当前 diff、近期热点和一阶依赖。
4. 新增严格 `prototype_evidence` 结构化合同，并由现有 planning/worktree/artifact 链消费；不新增 prototype Skill。
5. 更新既有 Skill、模板、机械门禁、正反例和 eval，保证 research/prototype 不可静默进入 implementation。
6. 在 Codex source adapter 中生成官方当前 `agents/openai.yaml` 结构，硬拒绝顶层 legacy metadata；再通过既有 source-to-live 链验证。

## 非目标

- 不安装 `mattpocock/skills`、`skills.sh` 或 Claude plugin。
- 不复制上游 41 个 `agents/openai.yaml`、Skill 正文、`.scratch` 目录约定或 plugin manifest。
- 不恢复 `mattpocock-skills` submodule，不执行上游脚本、hook、MCP 或依赖安装。
- 不新增 `wayfinder`、`batch-grill-me`、`to-questionnaire`、`setup-ts-deep-modules`、prototype 或 architecture Skill。
- 不把 `explicit-only` 当作权限授予；网络、写入、子代理、commit、publish 和 source-to-live 仍受独立审批与安全门禁约束。
- 不宣称 fixture 等于真实运行效果；本地 metadata/task contract smoke 与真实长期使用复审分离。

## 能力归属与复用结论

- Invocation：新增 manifest contract；运行时差异留在 target adapter/external handoff。
- Task kind：增强 `adk-task-breakdown`、`adk-planning-execution-loop`、`adk-parallel-agent-governance`，不新增 Skill。
- Architecture scope：增强现有 `architecture-planner`，不新增 Agent。
- Prototype：新增结构化 evidence contract，并复用 artifact/worktree/retention 治理。
- 外部实践吸收：继续使用既有 `adk-external-practice-absorption` Workflow，不新增 provider 专属流程。

## Breaking Change

本变更是硬切换，无兼容期：

- 删除 `adk-task-package-schema-v1` 标识与所有活跃引用，只接受 v2。
- 机器消费的 task package 缺少 v2 新字段时直接失败，不补默认值、不读取旧 schema、不双写。
- Codex adapter 只生成 `interface.display_name`、`interface.short_description` 和可选 `policy.allow_implicit_invocation`；顶层 `display_name/short_description` 直接失败。
- `implicit` 默认省略 policy；`explicit-only` 必须生成 `allow_implicit_invocation: false`。显式 `true` 作为冗余 legacy 输出被拒绝。
- 不保留 alias、warning-only wrapper 或兼容转换器。

回退只能整体 revert 本 change，并从 source-to-live 备份恢复运行资产；禁止恢复双 schema 或双 metadata 格式。

## 成功标准

1. ADK active tree 不再出现 `adk-task-package-schema-v1`。
2. Invocation contract 能机械校验 mode、target mapping、legacy deny-list 和显式调用不等于权限授予。
3. task-package v2 对四种工作项实施跨字段权限规则；负 fixture 能证明 research/prototype 无法取得实现权限。
4. architecture-planner 输出包含 `base_ref/history_window/selected_hotspots/expansion_reason/broad_scan`。
5. prototype evidence 包含 question、base commit、artifact hash、结果、retention、expiry 和 cleanup owner。
6. 修改的 Skill/Agent/manifest/template 具有定向回归；ADK strict/quick/full、release check 均通过。
7. Codex source metadata 全部采用官方当前嵌套结构，source-to-live build/doctor/plan/dry-run/apply/routing/check 有证据。
8. adoption matrix 同时记录吸收机制与拒绝项，lifecycle 继续 `sampled watch`，不恢复全量追踪。

## 风险与控制

- schema breaking：同一 change 更新全部消费方、模板和测试；残留扫描为零才允许完成。
- token 增量：新字段短名、枚举和按需 evidence；Skill 入口仍受行数/token budget 门禁。
- 误设 explicit-only：默认 `implicit`，override 必须有正反路由 fixture 和 owner 理由。
- 子代理越权：invocation 只决定 discovery；实际调度仍要求 scope、permission、must_not_touch 和显式调度门禁。
- 原型污染 Git：默认 evidence artifact；只有独立批准时才创建 branch/worktree，并带 expiry/cleanup owner。
- source-to-live 覆盖：先分类 `~/codex` 既有 dirty，使用 plan/dry-run/备份，不直接写 `~/.codex`。

## 安装范围与发布边界

- ADK contract/Skill/Agent/template：`global-ready`，平台中立。
- Codex metadata adapter：Codex project source only，经 `~/codex -> ~/.codex` external handoff 发布。
- 上游仓：reference-only/sample-watch，不进入生产依赖。
- pilot：静态 contract + Codex metadata build smoke；长期路由命中率另设复审，不以本 change fixture 冒充现场数据。

## 收敛与停止条件

- retry_budget：同一根因最多 2 次；第三次前必须 replan 或 split。
- staleness_threshold：每完成一个任务或 45 分钟更新工件与证据。
- stop_condition：`pass|replan|split|blocked|abort`。
- completion claim：只有 source、decision、implementation、verification、rehearsal、review/retire 六类本地证据完整，且 blocker/major 为 0，才能声明本地终态闭环。
