# Requirements: code-review-skill-progressive-disclosure

## Problem
`skills/adk-code-review-loop/SKILL.md` carries both the always-needed review contract and long-form governance detail in one 10KB+ entry file. That makes every triggered code-review task pay for severity tables, full multi-step explanation, convergence exceptions and CI publication details even when those details are not needed.

## Requirements
- Preserve the existing skill name, description, triggers, non-triggers, inputs, outputs and core constraints.
- Preserve required skill headings and all existing machine/test anchors used by review governance.
- Keep snapshot identity, working-tree overlay, reviewer independence, mechanical-vs-semantic separation, design-change routing and convergence rules in the entry skill.
- Move secondary explanation to an on-demand reference without weakening any fail-closed rule.
- Add a deterministic byte ratchet so the entry remains at or below 7200 bytes.
- Keep `review-evidence-template.md` and `review-feedback-fixtures.md` as dedicated references.

## Non-goals
- No change to manifest/profile/workflow/release semantics.
- No change to severity meanings or review pass criteria.
- No removal of trigger phrases for token savings.
- No new token-lean product profile.
- No change to issues #18/#20/#21.

## Acceptance
- The entry skill is <=7200 bytes and still satisfies asset/trigger/SOP tests.
- Detailed review governance remains available under `references/`.
- Exact-head hosted CI passes before merge.
- Fresh-main 6 core jobs and keyless OIDC promotion sign/fresh verify pass after merge.
