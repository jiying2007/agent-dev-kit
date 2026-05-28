# Codex Pilot Evidence Runbook

## Purpose

Keep Codex pilot evidence reviewable before adk assets are promoted into live
`~/codex -> ~/.codex` usage.

## Required Evidence Fields

Every completed pilot scenario must record:

- scenario key and completion state
- artifact labels for plan, review and test evidence
- commands, exit codes and result summaries
- evidence path that can be checked from this workspace
- known issues, rollback path and follow-up owner

## Pilot Coverage

The current coverage baseline is the six-scenario adk self-pilot:

- feature delivery
- bugfix delivery
- refactor hardening
- release hardening
- team handoff
- upstream intake

The canonical report is `reports/codex-pilot-report.md`. This runbook exists as
the stable adoption-matrix evidence target; detailed historical evidence remains
in reports.

## Verification

```bash
rtk bash scripts/check-codex-pilot.sh . evidence
rtk bash scripts/check-codex-pilot-coverage.sh .
rtk bash scripts/check-evidence-bundle.sh .
```

Promotion is blocked when a completed pilot lacks command-level evidence or when
review and test conclusions conflict.
