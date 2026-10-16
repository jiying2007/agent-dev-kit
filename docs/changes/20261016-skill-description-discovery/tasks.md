# Tasks

- [x] TASK-001: edit eight near-neighbor descriptions and ensure each SKILL.md UTF-8 byte delta <= 0. Verify: profile context and Skill content tests.
- [x] TASK-002: add static metadata contrast cases to existing trigger matrix. Verify: `bash tests/test_skill_trigger_matrix.sh`.
- [x] TASK-003: separate source proof from G21/G22 evidence and synchronize the generated Skill catalog. Verify: `bash scripts/devkit.sh validate --strict`; `bash tests/test_catalog.sh`.
- [ ] TASK-004: run exact-head PR CI, review, protected merge, fresh-main CI, release, and Root exact pin. Verify: GitHub receipts.
