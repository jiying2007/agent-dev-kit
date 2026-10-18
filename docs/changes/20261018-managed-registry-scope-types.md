# Trust registry scope-type validation — 8.0.30

## Requirement

Managed native conformance and Agent Value evidence trust registries are untrusted structured input. Invalid nested scope values must reject with the repository's typed `ManifestError` instead of escaping as `TypeError` during set-based deduplication. No trust authority is enabled, no actual G21/G22 receipt is created, and no product qualification changes.

## Implementation

- Validate native `allowed_targets` as bounded, scalar, safe identifiers before detecting duplicates.
- Validate Agent Value `allowed_layers` membership and target identifiers before deduplication.
- Preserve existing semantics for well-formed registries, existing Python 3.8+ syntax and dependency pins, and the registered CI matrix.

## Verification and rollback

Negative tests cover array/object scope values, duplicate IDs and unsafe target identifiers. Required verification: Python 3.8/3.11/3.12 contract and regression CI, static-security, CodeQL, fresh-main, exact-tag immutable Release, followed by Root exact-source promotion through its existing lock/evidence protocol.

Rollback changes the code/contract source through a new versioned release; do not rewrite an immutable tag, loosen registry validation, fabricate a signed native receipt, or claim real runtime or field evidence.
