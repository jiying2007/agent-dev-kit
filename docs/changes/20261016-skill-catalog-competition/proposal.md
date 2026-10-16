# Skill Catalog Competition — Proposal

## Canonical Change Contract

| Requirement | Delta | Affected Surface | Acceptance | Task | Verification | Evidence |
|---|---|---|---|---|---|---|
| REQ-001 | ADDED | `tests/fixtures/skill_catalog_competition.tsv` | ACC-001: catalog winner and abstention cases are deterministic | TASK-001 | VERIFY-001 | hosted regression / PR |
| REQ-002 | MODIFIED | `tests/test_skill_trigger_matrix.py` | ACC-002: real competitor is positive when explicitly selected | TASK-002 | VERIFY-001 | hosted regression / PR |
| REQ-003 | ADDED | `docs/analysis/skill-catalog-competition-v1.md` | ACC-003: source-only evidence is not called model behavior proof | TASK-003 | VERIFY-002 | diff review / PR |

Canonical identity and lifecycle continue to use the existing change, matcher, CI and release authorities. This change does not install third-party Skill Packs.
