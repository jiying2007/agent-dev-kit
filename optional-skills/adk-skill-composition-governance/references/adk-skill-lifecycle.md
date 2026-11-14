# ADK Skill Lifecycle

## Scope

- Skill name:
- Intended profile: core | optional | reject
- Embedded full-stack layer: silicon/board | boot chain | BSP/rootfs | OS/runtime | driver | middleware/protocol | device application | host/production tool | diagnostics | OTA/field | safety/reliability
- Primary scenario:
- Non-goals:

## Creation Gate

| Gate | Decision | Evidence |
|---|---|---|
| Duplicate skill checked | pass |  |
| Trigger overlap checked | pass |  |
| Profile ownership decided | pass |  |
| Reuse threshold met | pass |  |
| Pilot requirement declared | pass |  |
| Fallback / replaced_by declared | pass |  |
| Output contract declared | pass |  |
| Deterministic guard declared | pass |  |
| Evolution evidence declared | pass |  |
| Distribution channel reviewed | pass |  |

## Pattern Classification

| Pattern | Fit | Required hard gate |
|---|---|---|
| Tool Wrapper | wraps CLI/API/MCP | command allowlist, input validation, rollback |
| Generator | creates code/docs/assets | schema or template, overwrite policy, verification |
| Reviewer | evaluates existing work | severity rubric, evidence paths, false-positive handling |
| Inversion | user gives goal, agent controls workflow | explicit stop/ask conditions, state file, owner |
| Pipeline | multi-stage orchestration | code-level state check, checkpoints, resume and abort path |

Pipeline and Inversion skills must not rely only on prose such as "do not proceed". They need executable state checks, structured output validation, or an external workflow gate.

## Reuse Threshold

- First occurrence: solve directly and record only if there is evidence.
- Second occurrence: draft a reusable checklist, template, or reference.
- Third occurrence: consider a Skill only if the workflow has stable inputs, outputs, done criteria, and failure handling.

Reject or keep as `REFERENCE_ONLY` when the candidate is a one-off tutorial, domain showcase, trend list, external marketplace entry, or requires unreviewed tools. Prefer enhancing an existing Skill over creating a parallel one.

## Evolution Evidence Gate

Skill evolution must be evidence-driven and monotonic:

- Group evidence by existing Skill and repeated failure mode before changing the Skill.
- Preserve success invariants from tasks that already pass; a fix that breaks verified paths is rejected.
- Encode only reusable lessons, not one user's local workaround, temporary path, token, tool ranking, or provider promotion.
- Validate candidate updates against representative success and failure examples before promotion.
- Keep rejected updates as review records; do not silently overwrite the active Skill.
- Treat public marketplaces, private registries and shared folders as distribution channels only. They do not prove safety, quality, license compatibility or production readiness.

## Skill Behavior RED → GREEN → REFACTOR

- **RED（无 Skill 基线）**：固定真实任务、模型/版本、温度、工具与上下文；让未加载该 Skill 的 Agent 执行压力案例，保留原始回答与明确失败模式。没有运行能力则记 `not-measured`，不得编造失败。
- **GREEN（候选 Skill）**：只改一项可验证行为，用同样任务集重跑；记录失败是否消失、原有成功是否回退、额外问答与工具调用成本。
- **REFACTOR**：对成功但有多余规则的修改做减法；加入易误触发、对抗诱导、用户拒绝、已批准快路径及中断恢复样例；保留被拒变更。
- **独立性**：候选作者不担任唯一效果裁判；至少一次盲看不同变体的对照评价，重大用户决策仍归用户。测试数据和评分标准预注册，不能挑案例后补阈值。
- **晋级**：静态路由、合同、授权负例由 CI 证实；原生 discovery/load、任务行为、端到端结果分别核真实 trace。没有 E2–E4 时标 `not-measured`，只可声明 source-ready。

离线试验和评分见 `references/skill-behavior-evaluation.md`，不自动启用付费模型或后台调用。

## Failure Feedback → Deterministic Regression (conditional)
- First freeze an actual, redacted `failure_trace_ref`, `source_sha`, expected/observed, error class and affected Skill; if evidence is only a hypothetical example, label it `design-case`, not a reproduced failure.
- Classify whether the correction is stable and testable: use the **existing** trigger matrix for misrouting, an existing fixture/contract test for schema or permission mistakes, and an approved real-host trial only for semantic task-quality failures. Do not add tests that simply search for the new slogan while missing the behavior.
- Write the smallest positive/negative case with an explicit forbidden outcome; show the deterministic RED if runnable, apply the minimal Skill change, then show GREEN and check previously passing examples. When RED cannot run, record `not-run` and keep the effect `not-measured`.
- Train-case failures can guide edits; reserve frozen holdout cases for final comparison. Do not contaminate holdout, auto-approve rules, rewrite global instructions or leak raw transcripts/credentials.
- Avoid a universal "one correction = one new rule" policy: consolidate repeats by failure cause; retire ineffective instructions after observed regression and owner review.

## Lifecycle Review (report-only)
- Review operational states as `active / deprecation-candidate / deprecated / retired` **only as analyst labels** unless the canonical ADK Manifest explicitly supports that value; never silently add unsupported lifecycle enums or a second state registry.
- Consider verified use, true route overlap, actual task outcomes, target profile footprint, replacement availability, consumer compatibility and rollback evidence. Inactivity or directory age alone is not a reason to delete a Skill.
- For proposed retirement, record `candidate / evidence / owner_decision / replacement / affected_profiles / fallback / required_and_forbidden_footprint / rollback`. Without consent, native evidence or verified replacement, leave the active asset unchanged.

## Atomicity Rule

Do not embed one Skill inside another Skill as an implicit dependency. Use Agent routing, workflow stages, or `adk-skill-composition-governance` to connect atomic skills. Each Skill must remain useful and testable on its own.

## Output Contract

- Expected artifact:
- Schema/template:
- Pass condition:
- Needs-fix condition:
- Deny-path example:

## Metadata

- version:
- last_updated:
- quality_tier:
- owner:
- review_by:

## Validation

- `bash scripts/devkit.sh validate --strict`
- `bash tests/test_skill_trigger_matrix.sh`
- `bash scripts/pilot-readiness.sh --summary-json`
- `bash tests/run_all.sh`
