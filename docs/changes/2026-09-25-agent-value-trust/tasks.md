# Managed Agent Value trust checkpoint

- [x] Add strict default-empty Agent Value trust registry.
- [x] Add managed digest-pinned Sigstore/cosign receipt verifier.
- [x] Bind contract authority to registry backend/layer/target scope.
- [x] Bind exact receipt canonical digest, signature bundle digest, certificate identity/issuer and verifier binary digest.
- [x] Exercise canonical validate_receipt and emit_measurements with synthetic runtime evidence.
- [x] Keep canonical contract disabled, registry empty, production authority false and lifecycle authority absent.
- [x] Add full/quick regression coverage and update runbook.
- [x] Advance source identity to 7.5.0.
- [ ] Final PR CI, fresh-main CI, immutable Release and Root promotion must come from actual GitHub runs.
- [ ] Real invocation receipts and outcome/retirement evidence remain external facts; fixtures cannot fill them.
