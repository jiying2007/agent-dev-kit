# Design

Use a pure `_derive_effort` in the existing `matcher.py` v2 adapter, invoked *after* the permission ceiling. It reads existing `risk`, `task_mode`, `effect_ceiling`, `escalation_effects`, and resolved permission; it adds output hints `execution_effort`, `effort_basis`. It does not write the route, bypass policy or add a sidecar authority.

Order: release/high risk/escalation E3; explicit readonly E0; explicit low-risk implementation + workspace-write + authorized permission E1; otherwise E2. Abstain remains mutation deny and no selected Skill. Acknowledged gap: existing production routes do not label low-risk implementation, so E1 is intentionally not guessed at runtime.

Update only existing compact Skill entrypoints, preserving the common Skill metadata and deferred references. Measure source-only tests; do not infer model changes. Rollback: revert exact PR; no data migration or compat facade.
