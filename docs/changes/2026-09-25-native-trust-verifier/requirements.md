# Managed native trust verifier requirements

1. Production target loading must not depend on arbitrary caller callbacks for native receipt trust.
2. A managed repository registry must bind authority, policy backend, target scope, receipt canonical digest and signature bundle digest.
3. Signature verification must bind certificate identity and OIDC issuer and use a reviewed verifier binary digest.
4. Verification must be shell-free, bounded, read-only and fail-closed.
5. Static target behavior and current target certification state must not change.
6. The registry must contain no enabled authority by default.
7. Synthetic verifier tests may validate wiring only and must not imply native or product qualification.
8. Public capability addition advances ADK source SemVer to 7.3.0.
