# Design: role-context-ratchet

## Decision
Treat role instructions as a compact role delta over repository-wide governance. Keep role-specific decisions, validation, escalation and output contracts in `agents/*/AGENTS.md`; remove duplicated encyclopedic tooling/background prose.

## Baseline
- 13 built-in role files: 72,394 bytes total.
- Largest: code-review-governor 7,638; test-validation-engineer 7,125; architecture-planner 6,967; requirements-analyst 6,600.

## Target
Rewrite only those four hotspots. Expected aggregate becomes 61,889 bytes and the largest remaining role is 5,750 bytes.

## Ratchet
`scripts/check-role-context-budget.sh` enforces:
- per-role hard limit: 6,000 bytes;
- aggregate hard limit: 64,000 bytes;
- exact role count/aggregate/max path and estimated token reporting via `--summary-json`.

`tests/test_token_budget.sh` runs the role checker in normal and JSON modes and proves both hard limits fail closed with tiny thresholds.

## Compatibility boundary
Existing asset quality remains authoritative for required role headings and `pass`/`needs-fix` examples. Rewrites retain domain-specific machine anchors such as Evidence Index, Replayable Evidence Bundle, Hotspot/YAGNI scope fields, runner smoke contract, done-when and Trigger Matrix.

## Rollback
Revert this isolated change; no profile resolution, skill selection, manifest identity or release state migration is involved.
