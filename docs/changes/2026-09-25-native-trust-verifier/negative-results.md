# Negative-result policy

The managed verifier must reject:

- target authority not present or disabled in the registry;
- policy backend mismatch;
- target outside authority scope;
- unregistered receipt ID or canonical receipt drift;
- unsafe/missing/oversized signature bundle or bundle digest mismatch;
- missing verifier binary or verifier binary digest drift;
- missing/invalid certificate identity or OIDC issuer;
- verifier timeout or non-zero signature verification exit;
- target receipt that already fails the typed native receipt contract.

The implementation must not turn any of these into a warning or structural-only PASS. Static targets remain unaffected because the managed verifier is never invoked for static conformance.
