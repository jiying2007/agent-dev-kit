# Native campaign boundary regression — Requirements

## Intent
Fix two deterministic output-boundary correctness defects in existing ADK native campaign tooling without changing the target schema, trust authority, signed release protocol, or supported Python versions.

## Scope and acceptance
- `_semantic_assertion(stream=combined)` combines stdout, a real LF byte, and stderr; literal backslash-n must not match across streams.
- Direct JSON writing refuses an existing symlink leaf before resolving it.
- CLI native campaign output paths refuse symlink leaf or ancestors below the managed repository root even when the link resolves to an in-repository path.
- Preserve previously enforced external-escape and reports/runtime output restrictions; no broadened runtime permissions.
- Retain exact version lock / campaign IDs and exercise existing full Python CI, security and release promotion before Root pin changes.

## Non-goals
No real native runtime conformance claim, G21/G22 synthetic evidence, Owner re-attestation, automatic Python 3.8 removal or product M5 certification. Race-free filesystem adversary hardening is a separate design scope; this change improves deterministic source-path validation.
