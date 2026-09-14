# Design: code-review-skill-progressive-disclosure

## Decision
Convert `adk-code-review-loop` from a monolithic entry skill into a progressive-disclosure layout while preserving its behavioral contract.

## Entry layer
`SKILL.md` remains the triggered runtime entry and keeps:
- frontmatter trigger surface and constraints
- core review prerequisites and compact workflow
- snapshot/overlay/independence evidence anchors
- mechanical-vs-semantic separation
- `design-change` routing and convergence stop conditions
- fail-closed quality gate
- compact evidence template

The entry is ratcheted to <=7200 bytes. This is a byte budget, not permission to delete required semantics; future growth should prefer on-demand references.

## On-demand layer
New `references/review-governance-details.md` holds:
- full severity classification table
- detailed 18-step review workflow
- convergence protocol and review-mode boundaries
- CI/PR publication boundary
- snapshot/evidence detail

Existing `review-evidence-template.md` and `review-feedback-fixtures.md` remain unchanged and continue to own full report fields and examples.

## Compatibility
- Keep existing trigger phrases exactly so routing behavior does not drift.
- Keep exact machine/test anchors in `SKILL.md`; references supplement but do not replace them.
- No manifest record or profile membership change is needed.
- Skill version moves from 1.6.0 to 1.7.0 because the content architecture changes while public semantics remain compatible.

## Verification
`tests/test_skill_sop_quality.sh` continues all previous review anchors, additionally requires the new reference link, and enforces the 7200-byte entry ratchet. Existing asset-content, trigger-matrix and full-regression suites provide compatibility coverage.

## Rollback
Revert this isolated skill/reference/test change. No runtime data or manifest migration is required.
