# Requirements: hosted-workflow-hygiene

## Problem
Three read-only hosted workflows do not consistently disable checkout credential persistence and do not cancel superseded PR runs, creating avoidable credential exposure and hosted-run waste.

## Requirements
- `platform-vnext`, Codex consumer contract, and Digital Worker contract remain `contents: read`.
- Every targeted checkout sets `persist-credentials: false`.
- Superseded runs are cancellable only for `pull_request`; main push and workflow dispatch evidence remain independently runnable.
- Codex and Digital Worker keep `fetch-depth: 0` and `fetch-tags: true` because their immutable release-baseline checks inspect historical tag/commit/tree/blob identities.
- Branch-GC write/cleanup evidence remains non-cancellable.
- A deterministic fail-closed regression protects these invariants.

## Non-goals
- No product workflow/profile/skill semantics change.
- No release identity change.
- No dependency/action version bump.
- No change to issues #18/#20/#21.

## Acceptance
- Exact-head hosted CI passes.
- Targeted hygiene contract passes on both quick/full paths through `test_workflow_contract.sh`.
- Fresh-main core CI and OIDC promotion evidence pass after merge.
