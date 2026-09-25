# Managed native trust verifier checkpoint

- [x] Add bounded managed trust registry loader.
- [x] Add digest-pinned cosign blob verifier adapter.
- [x] Bind policy backend, trusted authority, target scope, canonical receipt digest, bundle digest, certificate identity/issuer and verifier binary digest.
- [x] Auto-inject managed verifier from production target-contract loader only for runtime conformance.
- [x] Keep registry empty and current target contracts static/not-certified.
- [x] Add positive synthetic wiring and negative drift/scope/binary/bundle/signature tests.
- [x] Advance source identity to 7.3.0.
- [ ] Final PR CI, fresh-main CI and immutable Release must come from actual GitHub runs.
- [ ] A real native runtime campaign and signed receipt remain independent evidence; no fixture fills that requirement.
