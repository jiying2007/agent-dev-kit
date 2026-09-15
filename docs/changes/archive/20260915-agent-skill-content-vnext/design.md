# Agent/Skill Content Architecture vNext — Design

## 1. Architecture

### 1.1 Source-of-truth map
- `manifest.json`: identity、path、quality tier、profile/workflow/product boundary SSOT。
- `manifests/agent_value_contracts.json`: 既有 Agent permission/authority/handoff/eval typed authority + invocation/value evidence contract；本轮直接复用，不复制第二份 behavior authority。
- `manifests/content_architecture_policy.json`: 长期 content ratchet（identity baseline、Agent byte/heading policy、未观测 production evidence 语义）；不依赖 active change 目录。
- `agents/*/AGENTS.md`: thin role instruction，面向模型的稳定常驻上下文。
- `manifests/skill_content_contracts_v2.json`: Skill runtime role/capability class/selection/effect/eval policy；从 manifest 派生，避免 per-skill identity copy。
- `src/agent_dev_kit/matcher_vnext.py`: 对稳定 matcher kernel 的薄 runtime eligibility adapter；显式 routing IR 仍是权威，implicit fallback 受 Skill v2 runtime role/effect ceiling 约束。
- `skills/*/SKILL.md`: procedure 与 portable instruction；复杂知识按需进入 references/scripts/assets。
- `schemas/agent-handoff-v1.schema.json`: 全局 handoff envelope。
- Workflow: composition/state；Tool: deterministic execution；Guardrail: validator/runtime/approval；Eval: behavioral proof。

### 1.2 Seven-layer rule
1. Agent 回答“谁负责”。
2. Skill 回答“能力怎么完成”。
3. Workflow 回答“能力怎么组合”。
4. Tool 回答“真正执行什么”。
5. Guardrail 回答“哪些动作不允许或需审批”。
6. Reference 回答“需要知道什么”。
7. Eval 回答“如何证明选择与行为正确”。

## 2. Agent Contract vNext
每个 Agent 必须围绕：Mission、Owns、Does Not Own、Decision Authority、Permission Boundary、Default Capabilities、Handoff / Escalation、Stop Conditions、Input Contract、Output Contract。

### 2.1 Thin-content ratchet
- `AGENTS.md` hard cap：P0 5000 bytes；P1 4500 bytes。
- 禁止 headings：`执行流程`、`必跑验证`、`工具箱`、`反模式`、`场景输入样例`、`输出样例`。
- Agent 不得承载 shell command cookbook；procedure-specific commands 归 Skill/scripts/reference。
- default skills 以 manifest 为真；Agent 仅列 ID，不复制 Skill workflow。
- 兼容性 marker 只允许作为“字段由哪个 Skill 维护”的轻量 pointer，不允许恢复 procedure/checklist。

### 2.2 Status semantics
不再强制所有角色使用 `pass|needs-fix`：analyst/planner 使用 complete/decided 类状态，producer 使用 done/needs-review，verifier/reviewer 使用 pass/needs-fix，release 使用 go/no-go，curator 使用 candidate-ready/needs-evidence/rejected。状态文本属于 thin role output contract；权限、authority、handoff、eval 的机器权威继续由既有 Agent Value contract 负责。

## 3. Skill Contract v2
Machine contract 与 SKILL body 正交。Skill v2 不复制 65 份 path/description/category identity；它以 manifest `pattern/category/activation_mode` 为 derivation 输入，只为真实语义例外记录 override。

字段语义：
- `capability_class=task|workflow|support|guardrail|tool|knowledge|meta`
- `runtime_role=primary|supporting|governance|fallback`
- `selection_group`
- `effect_ceiling`
- eval obligations

`capability_class` 与 `runtime_role` 正交：tool/guardrail/meta 只要是 manifest routing 中明确的直接用户任务入口，也可以是 primary；真正的 support/knowledge 不能因 trigger 命中而隐式晋升为 primary。

### 3.1 Selection model
`LLM candidate recall -> deterministic contract filter -> selection_group conflict resolution -> exactly one primary -> supporting/governance closure`。

运行态约束：
- manifest `routing.intents[].primary_skill` 必须在 v2 中解析为 `runtime_role=primary`，否则 CI fail-closed。
- reviewed routing IR 的显式选择保持权威。
- implicit Skill-trigger fallback 只允许 v2 `primary`；supporting/governance/fallback 不得抢主技能。
- `--skill` 显式选择可加载 supporting/governance Skill，因为 runtime role 约束的是隐式主技能资格，不是可读/可调用性。
- effect ceiling 只允许收紧 `mutation_permission`，绝不升级授权。
- CI checker 与 runtime adapter 共用 `resolve_skill_content()`，防止两套 derivation 漂移。

## 4. Handoff v1
Typed envelope：objective、source/target agent、facts、assumptions、open questions、scope_read、scope_write、must_not_touch、artifacts、evidence_refs、permission_envelope、stop_conditions、approval_required、context_policy、expected_output、return_schema。

原则：summary-first；raw 只通过 opaque pointer；handoff 不扩大 source agent 权限。

## 5. Guardrail levels
- G0 prompt guidance
- G1 schema/static validator
- G2 runtime/tool guardrail
- G3 explicit approval
- G4 sandbox/worktree/runtime isolation

高风险 side effect 不得只停留 G0。

## 6. Progressive disclosure
稳定 role/authority 常驻；procedure 仅 Skill 激活后加载；长知识进入 references；重复/确定性步骤进入 scripts；原始证据保留 pointer 而不是默认复制全文。

`adk-runtime-router` 的 `skill-catalog-lazy-loading-v1`、`namespace_summary`、`deferred_surface`、`loaded_tools`、`schema_review`、`code_intelligence_provider_contract`、L1/L2/L3/raw、Skipped Skills、Fallback Evidence 等既有 contract 保留。

## 7. Eval pyramid
- E0 schema/parity
- E1 routing/trigger/collision/abstain
- E2 behavior/evidence/failure handling
- E3 authority/permission/handoff negative
- E4 trajectory

当前仓库没有启用 production runtime evidence authority，因此 E2–E4 的生产测量不得伪造；control-plane fixtures 与 structural/runtime routing gates 可闭环，runtime/field receipt 继续 `not-measured`，后续由既有 Agent Value measurement authority 接入。

## 8. De-duplication
Validator 对 Agent 与 default Skill 做确定性长行 overlap ratchet，重点阻止完整 procedure/command/checklist 回流 Agent。BSP 是首个 fixture；后续 duplication debt 只允许下降。

## 9. Compatibility and cleanup
- 不修改 13 个 identity、路径或 target export contract。
- 旧“所有 Agent/Skill 必须同 headings”测试与 core validator 一并替换。
- 不新增长期 v1/v2 Skill parser shim；新 Skill contract 是 additive control plane。
- 不新增 `agent_behavior_contracts` 等平行 Agent behavior SSOT；现有 Agent Value typed contract 继续承担 permission/authority/handoff/eval 机器语义。
- change package 只保存历史 evidence；长期 validator 不读取 active/archive change 路径，因此 review-passed 后可安全归档。
- `skill-content@2`、`agent-handoff@1`、`content-architecture-policy@1` 均登记到统一 contract registry。

## 10. Security
External references 仍为 method-only；不自动下载/安装外部 Skills。Skill contract effect ceiling 是上限，不是授权；最终授权仍需 Agent permission envelope + runtime/tool boundary 同时满足。
