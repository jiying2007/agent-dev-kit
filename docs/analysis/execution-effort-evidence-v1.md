# Execution Effort and Evidence Quality v1

Status: source candidate — operational A/B not measured
Canonical source: production `matcher.py` projects E0–E3 from *existing* Routing IR, risk and Skill Content v2 effect metadata.

## Invariants

1. High-risk route, release mode and declared live-device/publish escalation always recommend E3, even when readonly is requested.
2. Explicit read-only without high-risk escalations recommends E0 but always denies mutation.
3. E1 requires an already-reviewed low-risk implementation route, workspace-write ceiling and actual workspace-write permission. No default unknown-risk promotion or relaxed R2.
4. Unknown risk and remaining tasks default E2; abstain means no capability selected and never grants writes.
5. The effort hint does not authorize side effects or change the canonical change/approval/release authorities. Human escalation may increase effort; it must not bypass existing approval.
6. Performance claims require run-validity, equivalent inputs/outputs, alternated A/B and full distribution evidence. A green test is not model or hardware efficiency evidence.
7. Risk-based independent falsification is a bounded E2/E3 review item, not compulsory extra agent calls.

## Boundaries and observed evidence

`tests/test_skill_governance.py` checks the E0/E2/E3 route projection, synthetic E1 guards, escalation precedence and evidence wording. This is deterministic source-level proof only. Agent runtime/task outcomes, real Token/time reduction, board performance and cross-host SKILL.md description discovery are not measured. Do not record invented percentage gains.

Only promote after exact-head PR CI, fresh-main CI, immutable release, Root exact pin and independent rollout evidence. For uncontrolled environments use `not-measured` instead of `pass`.

Method sources (no copy/runtime dependency): Addy agent-skills `aeac41d4`; Matt Pocock skills `49dd158d`; pstack `f713f142`. Independent external-practice acceptance remains in Root, not ADK.
