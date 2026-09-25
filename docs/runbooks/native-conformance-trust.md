# Native conformance trust

Native target conformance remains opt-in. Static target contracts do not invoke a trust verifier.

A runtime target may promote only when all of the following are true:

1. The target contract switches to runtime conformance and enables `conformance_trust_policy`.
2. Every receipt passes the existing typed receipt, runtime identity, bundle/contract digest, stage ordering, privacy and authority checks.
3. `manifests/native_conformance_trust_registry.json` contains the same trusted authority, policy backend and target scope.
4. The exact receipt ID is registered with its canonical receipt SHA-256 and a bounded in-repository Sigstore bundle path/digest.
5. The configured cosign binary exists and matches its reviewed SHA-256.
6. `cosign verify-blob` succeeds with the registry certificate identity and OIDC issuer.

The production loader builds this verifier automatically. Callers do not provide an arbitrary callback to `load_target_contract`.

The registry is intentionally empty by default. Adding an enabled authority is a separate owner-reviewed change and does not itself certify a target. A real native campaign must still create independent discovery/load/trigger evidence and a signed receipt.

Failure of any registry, target, receipt, bundle, binary, identity, timeout or signature check is fail-closed. Verification uses subprocess arguments without a shell, discards verifier output, and never stores prompt/message/raw tool content.

Synthetic tests may use a fake verifier binary only to prove wiring and failure semantics. Such tests provide no cryptographic, runtime or product authority.
