# Managed Agent Value trust requirements

1. Runtime/field invocation receipts must not depend on arbitrary caller verifiers.
2. A repository-governed registry must bind authority, backend, evidence layer, runtime target, canonical receipt digest and signature bundle digest.
3. Signature verification must bind certificate identity/OIDC issuer and a reviewed cosign binary digest.
4. Verification must be shell-free, bounded, privacy-safe and fail-closed.
5. The canonical Agent Value contract and registry must remain disabled/empty by default.
6. Runtime/field measurement may be emitted only after the existing receipt validator and managed verifier both pass.
7. Agent Value v1 must keep production authority false, quality_evidence_eligible=false and lifecycle_authority=none-evidence-only.
8. Synthetic tests prove wiring only; they do not create runtime, field, retirement or product authority.
9. Public managed-trust capability advances source version to 7.5.0.
