# Design: profile-coherence-observability

## Decision
Extend the existing profile coherence summary with additive observability while keeping the canonical manifest and profile semantics unchanged.

## Compatibility
Keep `schema: adk-profile-coherence/v2`. Existing consumers that validate the schema identifier continue to work; new consumers may read the additive `profile_inventory`, `capability_stats`, and `standalone_core_overlap` fields.

## Profile inventory
For each canonical profile, emit sorted deterministic fields:
- `parents` and `inheritance_depth`
- direct, inherited, and resolved agents
- direct, inherited, and resolved skills

Resolution continues to use the production `Manifest.resolve_profiles()` path. Inherited evidence is the resolved set minus the profile's direct declaration.

## Aggregate evidence
`capability_stats` summarizes profile count, total resolved agent/skill references, unique resolved agents/skills, and maximum inheritance depth.

## Overlap observation
For every non-core profile with no parent, compare its resolved capabilities with resolved `core`. Record overlapping agents/skills and counts under `standalone_core_overlap`.

This is observability only. An overlap does not imply that the profile should extend `core`; changing inheritance can alter capability semantics and remains a separate design decision.

## Independent verification
`tests/test_profile_coherence.sh` reads raw `manifest.json`, independently walks profile inheritance, and recomputes the expected inventory, aggregate statistics, and standalone/core overlap. The test does not import the contract's helper functions.

## Safety boundaries
- Existing fail-closed validation remains authoritative.
- `manifest.json` remains the only profile SSOT.
- No profile or runtime behavior is changed.
- Manifest composition Phase-4A boundaries remain unchanged.

## Rollback
Revert this isolated change. No manifest or runtime migration is required.
