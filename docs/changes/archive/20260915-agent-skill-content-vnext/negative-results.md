# Agent/Skill Content Architecture vNext — Negative Results

1. **未采用：删除/合并 13 个 Agent。** 当前 production/runtime invocation evidence authority 仍未启用，缺少足够 value evidence 支撑 identity consolidation；先 thin rewrite，后续再基于真实 delegation/value 证据判断。
2. **未采用：把所有 ADK Skill policy 塞入 SKILL YAML frontmatter。** Portable metadata 应保持轻量；复杂 runtime policy 放 typed sidecar/registry，避免污染可移植表面。
3. **未采用：description 完全替代 typed routing contract。** description 用于 discovery；selection group、effect ceiling、dependency、runtime role 必须 machine-checkable。
4. **未采用：所有自然语言规则全部 schema 化。** 架构权衡与领域判断仍保留模型推理；只有跨 runtime、需要 enforcement 或 regression 的信息进入 typed contract。
5. **未采用：把 token/cost 作为 quality KPI。** 继续作为 efficiency metric；quality 由 task success、evidence、authority、trajectory 等证明。
6. **未采用：长期 Skill v1/v2 双轨 parser。** 本次 Skill v2 是 additive machine control plane；旧 mandatory-heading content contract 直接退役。
7. **未采用：伪造 Phase 7 production behavior pass。** 没有受管 authority/receipt 的 runtime/field 指标继续明确 `not-measured`；只关闭可由仓库 CI 证明的 schema/routing/authority control-plane 工作。
8. **未采用：新增长期 `agent_behavior_contracts` 平行 SSOT。** 首版候选验证后确认现有 `agent_value_contracts.json` 已经是 permission/authority/handoff/eval 的成熟 typed authority；再保留一份行为 manifest 会制造双 SSOT，并迫使成熟 validator/receipt API 为无收益拆分承担迁移风险。最终删除该临时 manifest/schema，content vNext validator 直接复用 Agent Value authority。
9. **未采用：为了旧 official-docs/intent marker 测试恢复 Agent SOP。** 仅保留指向对应 Skill 的字段级 pointer；procedure/checklist 仍由 Skill/reference 拥有。
10. **未采用：把 guardrail/tool/meta capability 一律降级为 supporting/governance。** 深审发现 manifest routing 已把一部分治理、工具、meta Skill 作为真实用户任务入口；`capability_class` 与 `runtime_role` 必须正交。最终规则是 explicit routing primary 必须解析为 `runtime_role=primary`，真正 helper/knowledge 才禁止隐式抢主技能。
11. **未采用：重写成熟的 `matcher.py` 内核承载 vNext policy。** 直接改稳定 matcher 会扩大回归面并混合旧 IR 与新 eligibility concern。最终使用薄 `matcher_vnext` adapter：复用稳定 kernel，公共 match surface 叠加 Skill v2 eligibility/effect ceiling，CI 与 runtime 共用同一 resolver。
12. **未采用：让长期 validator 读取 `docs/changes/agent-skill-content-vnext/baseline.json`。** Change package 是历史 evidence，归档后路径会变化；长期 ratchet 已迁到注册的 `manifests/content_architecture_policy.json`，因此 archive 不改变运行时/CI 语义。
13. **首轮失败：core validator 仍强制旧 Agent headings。** 早期 hosted contract gate 因 `角色定位/执行流程/必跑验证/...` 缺失而失败；没有把旧 headings 塞回 Agent，而是迁移 `validation_contract.py` 与 content-quality gate 到职责感知 vNext contract。
14. **首版 Skill v2 仅做静态 metadata 不足。** 深审发现 public matcher 不消费 `runtime_role/effect_ceiling`；因此新增薄 runtime adapter，禁止 supporting/governance/fallback 资产在 implicit fallback 中静默成为 primary。
15. **首版 runtime-role 分类过度降级。** `adk-token-context-governance`、`adk-verification-before-completion` 等是显式 routing primary，不能因为 capability 是 guardrail/meta 就强制 governance/supporting；修正为“capability class 与 runtime role 正交”。
16. **代码审查近邻冲突暴露 selection-group 需要。** `代码审查` 会先命中 supporting 的 `adk-chinese-code-review`；不是把 supporting 直接提升 primary，而是只允许 lexical supporting trigger 提升同一 selection group 的唯一 primary `adk-code-review-loop`，多 primary 时 fail-closed。
17. **旧 permission 测试错误期待 workspace-write。** “明确授权实现新功能并修改代码”仍会先路由只读 requirements triage；Skill effect ceiling 必须把 mutation 收紧为 deny，用户授权文本不能越过被选 capability 的副作用上限。
18. **两项 workflow 被错误分类为 supporting。** `adk-context-compress-handoff` 与 `adk-branch-closeout` 都可以独立完成用户目标且存在明确流程，最终统一为 workflow primary，而不是继续在 runtime 添加例外。
19. **最后一个 79/80 红点是旧测试触发词。** `adk-context-engineering` v2 已重写触发词为“上下文工程/上下文膨胀/context planning”等，但 smoke 仍使用退役的 `context 构建`；只更新 fixture 为 canonical v2 trigger，没有改变产品行为。

## Evidence trail
- 初始候选：旧 universal-heading contract 阻塞 hosted validation。
- 中间候选：full regression 从 68/80 → 78/80 → 79/80，失败被逐轮收窄到真实 contract/fixture 不一致。
- 功能 exact head `6ea60edce7f375a226343637d152938027717ced`：`agent-dev-kit-ci` run `34929408924` 6/6 jobs SUCCESS，Python 3.11/3.12 full regression 均 80/80；`platform-vnext` `34929408957`、CodeQL `34929408987`、dependency review `34929408936`、branch-gc `34929408947` 全部 SUCCESS。
