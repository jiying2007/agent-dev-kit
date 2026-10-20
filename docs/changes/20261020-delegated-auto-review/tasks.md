# Tasks

## Ownership 与并行冲突检查

The qualification implementation agent owns `review_evidence.py`, Harness implementation files and their focused tests. The coordinating implementer owns `workflow.sh`, workflow tests, policy/authorization records, repository documents, historical lifecycle updates, shared CI lists and version identity. The independent reviewer owns no source writes. Root consumers are changed in a separate repository after the interface is frozen; ADK lock promotion waits for the formal release.

- [x] TASK-001: Freeze the explicit user delegation, single validator API, source/evidence scope and no-fabrication boundary. VERIFY-001: requirements/design and independent design review.
- [x] TASK-002: Implement the strict review validator and Harness consumption. VERIFY-002: focused negative cases and unchanged structural/freshness tests.
- [x] TASK-003: Integrate the existing review/archive lifecycle and explicit repository policy. VERIFY-003: receipt validation before mutation, stale inputs rejected at archive, existing lifecycle tests.
- [ ] TASK-004: Conduct independent reviews, preserve original evidence and complete three historical lifecycles; renew Harness from actual seven-dimension review. VERIFY-004: canonical review validation and actual current-date Harness gate.
- [ ] TASK-005: Complete whole-diff review, full regression and exact-head protected CI; publish a new immutable component version and verify downstream promotion. VERIFY-005: original test/run/release evidence.

## 轻量工件与收敛结论

Use this directory as the single requirements/design/tasks/authorization and verification record. No claimed human review, paid inference, Native run or field observation is created by this change.
