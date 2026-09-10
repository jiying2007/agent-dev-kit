# YAML Consumer Migration

## Goal

`manifest.json` is the only complete structured SSOT. `manifest.yaml` is a temporary legacy compatibility projection and must not acquire new product consumers.

## Policy

- New typed Python product code reads `manifest.json` through `agent_dev_kit.domain.manifest`.
- Only the manifest compatibility contract/facade may parse `manifest.yaml` in typed code.
- Existing shell consumers may continue through `scripts/lib-manifest.sh` while they are migrated incrementally.
- A migrated gate must prove it works with `manifest.json` present and `manifest.yaml` absent.
- Compatibility projection omissions are explicit and bounded to `product` and `schema_version`; expanding the omission set requires a reviewed contract change.

## First migrated consumer

`asset-taxonomy` now executes through `agent_dev_kit.domain.asset_taxonomy`; the shell entry point is a compatibility shim. Its regression creates a JSON-only temporary root to prove the validator has no YAML dependency.

## Exit condition

The compatibility projection can be deleted only after no active shell/product consumer requires `scripts/lib-manifest.sh` for structured manifest reads and all generated human projections are produced from canonical JSON.
