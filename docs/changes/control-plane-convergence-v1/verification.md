# Control Plane Convergence Verification

This change set is intentionally fail-closed. Fresh CI evidence is required before the PR can leave draft state.

## Evidence rules

- Contract jobs must pass independently on Python 3.11 and 3.12.
- Full regression must pass independently on Python 3.11 and 3.12.
- Static security and deterministic evaluation/package jobs must remain independent of regression failures.
- A missing executable bit, stale projection, unavailable runtime, or missing credential is never recorded as pass.
- Source/test evidence does not certify native runtime or field behavior.

## Current iteration

The first refactor CI exposed executable-mode and semantic projection defects. They are treated as defects in this change rather than suppressed by weakening tests.
