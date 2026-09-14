# Requirements: profile-coherence-observability

## Problem
The profile coherence contract fails closed on invalid inheritance and capability references, but its machine-readable summary only exposes aggregate pass/fail information. Reviewers cannot deterministically inspect each profile's direct, inherited, and resolved capability surface without reimplementing resolution externally.

## Requirements
- Preserve every existing profile coherence failure and warning rule.
- Preserve the `adk-profile-coherence/v2` schema identifier for additive compatibility with existing consumers.
- Emit deterministic per-profile direct, inherited, and resolved agent/skill inventory plus inheritance depth.
- Emit aggregate resolved capability statistics.
- Emit non-failing observations for parentless non-core profiles that overlap resolved `core` capabilities.
- Derive all evidence from canonical `manifest.json`; do not introduce a second profile SSOT.
- Test the emitted evidence by independently resolving inheritance from raw `manifest.json`.

## Non-goals
- No profile membership, inheritance, conflict, or default-profile changes.
- No new profile, including no token-lean profile.
- No manifest physical split or runtime fragment loading.
- No release identity change.
- No change to issues #18/#20/#21.

## Acceptance
- The existing and enhanced profile coherence tests remain compatible.
- The new inventory/statistics/overlap evidence is deterministic and independently verified.
- Exact-head hosted CI passes before merge.
- Fresh-main core CI and keyless OIDC promotion evidence pass after merge.
