# Control Plane Convergence v1 — Implementation Status

- status: implementation-in-progress
- product_version: 5.0.0-rc.2
- canonical_manifest: `manifest.json`
- legacy_manifest_yaml: removed
- compatibility_policy: no persistent Manifest mirror
- runtime_boundary: no LLM inference loop / no session scheduler
- release_authorized: false until fresh release evidence exists

## Implemented

- Manifest JSON is the sole structured SSOT.
- Persistent `manifest.yaml` has been removed.
- Manifest shell consumers route through the JSON query adapter.
- Asset validation, taxonomy, profile coherence and health checks use typed/canonical contracts.
- CI separates contract, regression, deterministic package/evaluation and static security evidence.
- External reference wording is evaluated by semantic product surface rather than broad documentation keyword scans.

## Remaining before merge

- Full Python 3.11 and 3.12 regression must be fresh green on the exact PR HEAD.
- Release/catalog active surfaces must not reintroduce a Manifest YAML dependency.
- Historical migration evidence may retain references to removed formats, but it is not runtime SSOT.
- Native runtime and field evidence remain separate evidence classes and are not implied by source/test success.
