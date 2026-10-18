# Release source authority — 2026-10-18

## Scope
GitHub tag-triggered workflows can execute the workflow definition from an unreviewed tag. Validating only inside such a workflow cannot establish a trustworthy component publishing authority. Manual dispatch from arbitrary refs has a similar source risk.

## Decision
- The privileged `release.yml` accepts reusable `workflow_call` only; no direct tag-push or manual branch entrypoint.
- The caller must be the successful push-to-main CI `workflow_run` promotion flow.
- Verify exact annotated tag/commit identity, refresh `origin/main`, and require release commit ancestry on protected main.
- Exact current release CI run ID may enable quick-regression reuse. Orphan-release repair must independently locate the historical commit's own successful main push CI and still execute full regression.
- Missing Git history, malformed API reply, conflicting identity or absent successful main CI stops publication, including repair.

## Verification and rollback
Existing mandatory contract and workflow-hygiene tests enforce these boundaries; real protected PR CI, merged main CI and immutable Release provide end-to-end evidence. Native tag creation Ruleset is an optional administrative defense in depth, not claimed applied by this source change. Rollback only via protected PR preserving protected-main source qualification.

## Non-claims
Component publishing is not a current-source Product M5 authorization, G21/G22 real runtime/effect evidence, LTA-04 field evidence or Owner attestation.
