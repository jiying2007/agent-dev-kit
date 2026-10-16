# Requirements

REQ-001: Supported Python 3.8, 3.11 and 3.12 contract and regression matrices must all succeed before an already-required GitHub ruleset check can pass.
REQ-002: Failure, cancellation or skipped upstream matrix legs must not turn the required check green, including when no package is produced.
REQ-003: Keep the release promotion exact-source, signing and product-qualification boundaries unchanged.
REQ-004: Add negative regression tests for dropping dependencies, omitting always(), weakening failure conditions and removing Python 3.8.

Acceptance: the existing ruleset-required deterministic-eval-package check fails closed on any supported matrix failure; PR/fresh-main CI and immutable release complete.
Non-goals: introducing a new required GitHub context, changing Python support, claiming real-model effectiveness or altering G21/G22/LTA qualification.
