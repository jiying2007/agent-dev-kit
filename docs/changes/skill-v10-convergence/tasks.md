# Skill convergence — implementation and verification

- [x] Snapshot main at `f9984ca91e6b511937137df0558d51d179ff2a8f`.
- [x] Normalize nine malformed OpenAI Skill metadata files.
- [x] Remove two language-only Skill identities and move their unique capability guidance to primary owners.
- [x] Remove old duplicated reference identities and procedures in seven retained `details.md`.
- [x] Add deterministic read-only commit message checker and tests.
- [x] Replace legacy one-size-fits-all Skill content gate with portable identity/policy tests.
- [x] Add locale routing, negative tests and risk-aware requirement and PR gates.
- [x] Bump source version and document breaking migration.
- [x] Fresh GitHub Actions Python 3.11/3.12 contract, full regression, security and target checks on `42d4ffddfdfc76b90b5e7512594b233af11a2712` (run 41781560766 and required security/platform runs).
- [x] Reconcile installer rollback-first behavior with 10.0.0 migration docs; add a negative upgrade/rollback/reinstall test (requires fresh CI on the new head).
- [ ] Independent source-bound review and protected PR merge.
- [ ] Immutable Release, verified `llm_agent` lock and `~/codex` source-to-live promotion. These are downstream deliverables, not automatically satisfied by PR CI.
