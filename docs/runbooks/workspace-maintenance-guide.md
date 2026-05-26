# Workspace Maintenance Guide

This runbook keeps ADK assets generic, validated and reviewable.

## Cycle

1. Update manifests, skills, agents or docs in a scoped change.
2. Run `bash scripts/devkit.sh validate --strict`.
3. Run `bash scripts/devkit.sh runtime-boundary`.
4. Run the targeted test first, then `bash tests/run_all.sh --fail-fast` when the change touches shared behavior.
5. Record validation evidence in the change or session summary.

## Boundary

Do not put platform-specific delivery paths into ADK core. Add explicit adapters only after contract review, security review and rollback evidence.
