# Tasks

## Ownership 与并行冲突检查

The implementation reviewer owns the Native diagnostics helper, its two test files, the hosted Native workflow, runbook and this change directory. After the first full regression exposed a timeout-scope integration failure, the coordinating maintainer also assigned this reviewer the bounded fix in `tests/test_hosted_workflow_hygiene.sh`. The coordinating maintainer owns shared CI lists, version synchronization and CHANGELOG. No one in this change writes the active Native registry, target contracts, historical Owner review files or readiness dates.

- [x] TASK-001: Implement bounded failure-only phase and observation collection; integrate stable workflow IDs and guarded upload. VERIFY-001 passed in the 25-case diagnostic regression.
- [x] TASK-002: Add privacy, malformed-input and unsafe-filesystem regression cases. VERIFY-002 passed, including valid plan, empty/partial evidence, unsafe paths and ambiguous JSON.
- [x] TASK-003: Document diagnostic authority and environment limits, verify unchanged success gates and integrate the existing CI scopes. VERIFY-003 passed locally; the coordinating maintainer added the wrapper to existing quick/full lists and the helper to the existing strict mypy scope.

## 轻量工件与收敛结论

Use this one change directory for requirements, design, task tracking and command evidence. The 25 new diagnostics cases and 20 existing Native cases pass on genuine RTK and Python 3.12.14; focused strict mypy, Ruff and change governance also pass. Independent review corrected the valid-plan map/scalar mismatch and the unsupported not-run inference for missing stage records. The first real full regression returned 96 pass / 3 fail; its synthetic credential-shaped literal and timeout-scope integration issues were corrected without changing security rules or execution budgets. The actual product-maturity, hosted-hygiene, workflow-contract, security and diagnostic checks now pass individually. A second full repository regression, protected PR/main CI and release gates are coordinated separately before merge. No real Native runtime result or human Owner verdict is created by this implementation work.
