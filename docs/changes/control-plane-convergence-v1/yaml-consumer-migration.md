# Manifest Consumer Migration

## Final state

`manifest.json` is the only structured Manifest SSOT. The persistent `manifest.yaml` compatibility projection has been removed and must not be recreated.

## Active consumer policy

- Typed product code reads `manifest.json` through `agent_dev_kit.model` / `agent_dev_kit.domain.manifest`.
- Shell entry points may remain for command compatibility, but structured Manifest reads must flow through the JSON query adapter or typed contracts.
- Asset validation, taxonomy, profile coherence, catalog generation and repository health checks are canonical JSON consumers.
- Generated catalog/reference documents are one-way projections and must identify `manifest.json` as their source.
- General YAML support remains valid for independent formats such as Skill frontmatter, Workflow or Target contracts; this policy only retires the duplicate Manifest representation.

## Regression boundary

`tests/test_manifest_consumer_boundary.sh` requires the legacy mirror to be absent and checks active Manifest entry points for accidental `manifest.yaml` dependencies. The taxonomy contract is also exercised against a JSON-only temporary root.

## Historical evidence

Old migration/change records may mention `manifest.yaml` when describing prior behavior or its removal. Those references are provenance only and must never be interpreted as an active runtime, release or configuration source.

## Exit status

The persistent Manifest compatibility projection is retired. Remaining work is limited to deleting obsolete one-shot migration/tombstone utilities and any historical naming that no longer describes current behavior; none of those may be required by the active product path.
