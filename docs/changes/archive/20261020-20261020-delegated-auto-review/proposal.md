# Integrate explicitly delegated independent automatic review

## 问题陈述（单问题）

The owner authorized automatic advancement and review on 2026-10-20. Existing lifecycle pass/count arguments and Harness owner/date metadata do not consume an independently reviewed evidence record, so the delegation cannot produce a trustworthy, repeatable qualification outcome.

## 上下文充分性检查

Read the existing lifecycle, seven-dimension Harness evaluator, strict JSON boundary, original three change packages, owner review packet, repository rules and downstream qualification consumers. A separate reviewer actually reviewed the frozen historical diffs and seven source dimensions, reporting one recovery defect that is resolved in the separate `20261020-safe-archive-restore` change.

## Core/Optional 边界检查

Extend the existing typed core and consumers. Reuse strict input reads, the canonical lifecycle and existing review Skill. No external model runner, additional Skill, paid resource, second approval engine or generated semantic verdict is introduced.

## 变更重复性检查

No existing validator binds delegated review identity, scope, current policy/evaluator, source bytes and semantic findings. One canonical validator supplies lifecycle, Harness and downstream consumption; downstream retains its own measurement and field contracts.

## Breaking Change 检查

Repositories without an explicit review policy preserve their existing behavior. This repository opts in, so CLI pass/count strings and refreshed dates alone no longer satisfy review. Existing archived facts remain historical; newly qualified records must satisfy the policy. Root G22/LTA migrate their currently unfulfilled review contracts separately after formal component promotion.

## Spec 链路检查

`requirements.md` and `design.md` freeze scope. The following contract connects implementation, negative tests, actual independent review and protected delivery. The owner authorization is preserved verbatim with its actual timestamp in `.adk/review-authorization.md`, outside relocatable change packages.

## Canonical Change Contract

| Requirement ID | Requirement | Operation | Target | Affected Surface | Acceptance ID | Acceptance Criterion | Task ID | Verification ID | Evidence Target |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Consume delegated review in existing lifecycle | MODIFIED | review/archive | workflow.sh | ACC-001 | Invalid receipts fail before state/report mutation; archive revalidates | TASK-003 | VERIFY-003 | tests/test_review_evidence_workflow.py |
| REQ-002 | Bind identity, authority and exact evidence | ADDED | Single review validator | review_evidence.py | ACC-002 | Separate independent AI verdicts, safe bytes and temporal/source checks | TASK-002 | VERIFY-002 | tests/test_review_evidence.py |
| REQ-003 | Preserve source/freshness/field boundaries | MODIFIED | Seven-dimension Harness | readiness.py and readiness_evidence.py | ACC-003 | Date-only refresh and stale or incomplete review cannot pass | TASK-002 | VERIFY-002 | tests/test_review_evidence.py and test_harness_readiness.sh |
| REQ-004 | Complete real historical semantic review | MODIFIED | Three frozen change packages | source review and canonical archive | ACC-004 | Independent dual verdicts bind original patches and survive archival | TASK-004 | VERIFY-004 | historical review-evidence.json and provenance.md |
| REQ-005 | Deliver through protected versioned gates | MODIFIED | Component and Root integration | CI, version and policy records | ACC-005 | Existing supported matrices and immutable exact-source promotion remain required | TASK-005 | VERIFY-005 | verify-report.md and formal GitHub runs |

## 安装范围与依赖边界

One typed module ships with the existing SDK. No new runtime dependency or installed capability is required. Root consumers import the same formally pinned ADK validator and policy; no duplicate Root review policy is created. Skill guidance remains in the existing core review Skill and its existing reference.

## Prompt 回归证据计划

Before: high-risk review guidance always required human final review, and lifecycle/Harness could not consume explicit AI delegation. After: an actually independent AI reviewer can supply source-bound Spec and Quality verdicts under recorded owner authorization. Source diff, deterministic contract tests and actual independent review prove these behavior and wording changes; no model quality or discovery improvement is claimed.

## 收敛模式与退出条件

Complete source implementation, negative tests, actual semantic review, three historical lifecycles, a current source-bound Harness review and normal protected component/Root delivery. Real Native execution, effect measurements, longitudinal observations and conditional Product M5 evidence remain governed by their original substantive requirements. No human intervention is needed for the explicitly delegated review scopes.
