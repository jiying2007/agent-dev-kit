# Design

## Decision
Token efficiency is a cross-chain runtime governance concern, not a separate product capability profile.

- Keep `manifest.json` profile taxonomy focused on capability composition.
- Keep `Low Token Profile` as a runtime overlay template only.
- Put machine-readable defaults in `manifests/token_context_policy.json`.
- Put one short always-loaded invariant in root `AGENTS.md`.
- Keep detailed routing/fallback behavior in `adk-token-context-governance` and load it on demand.

## Policy
- Default mode: `balanced` for every profile/workflow.
- Explicit low-token overlay: `fast` with L0/L1 first.
- Root-cause/review escalation: `precision/L2` when needed.
- High risk: `audit/L3`, raw evidence required and compression cannot replace mutation approval.
- Progressive disclosure and deferred tool/skill loading are default.
- Stable reusable context comes before dynamic context to preserve provider cache opportunities.
- When runtime usage exists, record input/output/cached/total tokens.

## Safety / rollback
This change does not alter product manifest resolution, runtime permissions, release identity or write authorization. Rollback is a single commit reverting the policy manifest, root invariant, skill/template text and contract test.
