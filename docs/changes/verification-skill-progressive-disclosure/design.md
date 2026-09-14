# Design: verification-skill-progressive-disclosure

## Decision
Convert `adk-verification-before-completion` into a progressive-disclosure layout without changing completion semantics or evidence requirements.

## Entry layer
`SKILL.md` remains the triggered runtime entry and keeps:
- unchanged trigger/non-trigger and frontmatter contracts
- compact completion workflow and fail-closed quality gates
- the full machine-facing Evidence Template surface
- Runtime Control Plane Audit and Trace Eval Regression fields
- Tool / Skill Evidence Plan and skipped-skill/fallback evidence
- Codify Decision fields and promotion gate
- Completion Guard Payload
- Lifecycle Operation Evidence and Review Convergence Evidence
- Subjective Feature Proof and `independent_verifier`

The entry is ratcheted to <=9500 bytes. The byte budget is a regression guard, not permission to remove evidence semantics.

## On-demand layer
`references/verification-governance-details.md` owns detailed applicability guidance, the expanded 25-step verification mapping, extended fail-closed rules, evidence-index explanation, exception handling, and anti-rationalization examples.

## Compatibility
- Machine/test markers remain in `SKILL.md`; the reference supplements rather than replaces them.
- `templates/governance/codify-decision.md` remains the Codify SSOT.
- No manifest/profile/workflow membership changes are required.
- Skill version advances to 1.7.0 because content architecture changes while public behavior remains compatible.

## Verification
`tests/test_skill_sop_quality.sh` pins the reference, critical machine anchors, and <=9500-byte entry budget. Existing trigger, content, codify, tool/skill evidence, asset, and full regression suites remain authoritative compatibility gates.

## Rollback
Revert this isolated skill/reference/test change. No state, manifest, runtime, or release migration is required.
