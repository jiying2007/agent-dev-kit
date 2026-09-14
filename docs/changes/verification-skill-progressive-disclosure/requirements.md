# Requirements: verification-skill-progressive-disclosure

## Problem
`skills/adk-verification-before-completion/SKILL.md` is a 13KB+ triggered entry that mixes always-required completion evidence contracts with long-form applicability, sequencing, exception, and anti-rationalization guidance. Every completion-verification task therefore pays for detail that can be loaded only when needed.

## Requirements
- Preserve the existing skill name, description, trigger/non-trigger surface, inputs, outputs, and constraints.
- Preserve the required skill headings and fail-closed completion semantics.
- Keep machine-consumed evidence fields in the entry, including Runtime Control Plane Audit, Trace Eval Regression Evidence, Tool / Skill Evidence Plan, Codify Decision, Completion Guard Payload, lifecycle/review convergence, and Subjective Feature Proof.
- Preserve the Codify decision fields and `templates/governance/codify-decision.md` reference.
- Move detailed 25-step explanation, applicability guidance, exception handling, and rationalization blockers to an on-demand reference.
- Ratchet the triggered entry to at most 9500 bytes.

## Non-goals
- No manifest, profile, workflow, or release identity change.
- No new `token-lean` product profile.
- No manifest physical split or runtime fragment loading.
- No change to issues #18/#20/#21.

## Acceptance
- The entry is <=9500 bytes and all machine evidence anchors remain in `SKILL.md`.
- Detailed verification governance remains available under `references/`.
- Exact-head hosted core and outer checks pass before merge.
- Fresh-main passes all six core jobs plus keyless GitHub OIDC promotion sign and fresh verification.
