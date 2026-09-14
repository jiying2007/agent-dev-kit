# Requirements: role-context-ratchet

## Problem
Built-in role instructions repeat generic tool lists, background prose and anti-pattern explanations. The 13 role `AGENTS.md` files total 72,394 bytes, with four roles above 6.5 KB, increasing selected-agent context cost without adding equivalent decision value.

## Requirements
- Preserve every role's required headings and `pass` / `needs-fix` examples.
- Preserve role-specific decision gates, evidence fields, escalation paths and machine anchors.
- Slim the four largest role files by keeping role delta over repository-wide rules instead of duplicating generic guidance.
- Enforce every built-in role `AGENTS.md` at <= 6,000 bytes.
- Enforce all built-in role `AGENTS.md` at <= 64,000 bytes aggregate.
- Provide deterministic machine-readable budget evidence and fail-closed negative tests.

## Non-goals
- No profile, skill, manifest, release identity or runtime routing changes.
- No physical manifest split.
- No changes to issues #18/#20/#21.

## Acceptance
- 13 roles remain covered by asset-content quality checks.
- Role context aggregate is materially below the 72,394-byte baseline.
- Tiny per-file and aggregate limits fail closed.
- Exact-head CI, expected-head squash merge, fresh-main 6-core CI and OIDC promotion verification pass.
