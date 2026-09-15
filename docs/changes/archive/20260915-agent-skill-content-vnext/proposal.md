# Agent/Skill Content Architecture vNext — Proposal

## Decision
将 ADK 内容架构从“Agent 与 Skill 都携带完整 SOP”重构为七层正交模型：

`Agent = Who owns` → `Skill = How to do` → `Workflow = How to compose` → `Tool = Execute` → `Guardrail = Enforce` → `Reference = Know` → `Eval = Prove`。

控制面继续复用现有 manifest、Agent Value、runtime router、evidence 与 target export；本变更新增 Skill v2 machine contract、global handoff schema、durable content policy、thin-content validator 和薄 runtime matcher adapter，但不建立第二份 Agent behavior authority，也不重写成熟 matcher kernel。

## Why now
- `bsp-analyst` 与 `adk-bsp-analysis` 已出现明显 procedure 重复。
- requirements/application/component/driver/build-release/test Agent 中已有大量可复用方法、命令、工具箱和教学内容，增加 always-loaded context。
- 旧 content quality/validation contract 把统一 headings 当质量，反过来推动 Agent SOP 化和 Skill 同构化。
- `agent_value_contracts.json` 已具备 authority/permission/handoff/eval typed authority，应直接复用而不是复制。
- 只建立 Skill v2 metadata 但不让 runtime 消费，会产生“治理声明与真实路由行为分离”；因此 public match surface 必须经过 v2 eligibility/effect ceiling。

## Compatibility
- `manifest.json` identity、profile、workflow、target 路径保持不变。
- Agent 文件路径不变；13 个 identity 第一阶段全部保留。
- Skill 文件路径不变；v2 contract 以 central sidecar registry 承载机器语义，避免给 portable SKILL frontmatter 注入非标准 nested policy。
- 现有 routing IR、runtime-router progressive disclosure 与 evidence marker 保留；`matcher_vnext` 只约束 eligibility/effect ceiling。
- 旧“所有 Agent/Skill 必须同 headings”门禁直接替换，不做永久兼容 shim。
- Agent Value 的既有 API/schema/receipt 行为保持兼容，不为本次内容重构制造第二套 behavior contract。
- 长期 ratchet 位于 `manifests/content_architecture_policy.json`；change evidence 可在 review-passed 后归档而不影响 runtime/CI。

## Rollout
按 Phase 0–8 一次工程 campaign 完成：先 functional exact-head 全绿并完成 independent review，再将 change package 归档；对归档后的最终 exact-head 再跑 hosted CI，expected-head squash merge 后要求 fresh-main CI + promotion evidence，才宣称 terminal closure。
