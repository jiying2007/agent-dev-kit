# Native campaign output leaf safety

## Goal and evidence

Reject an existing symbolic-link output leaf before native campaign CLI path resolution can erase its identity. On ADK 8.0.37 / `19a89bab07c42f4fe506bafe5b8c8e64e1e1baf3`, independent real `prepare` invocations accepted both an external link to an existing file and a dangling external link. The first target was overwritten; the second target was created. These were owned temporary fixtures, not native runtime campaigns.

## Acceptance

1. Every `_safe_output_path` consumer rejects external and repository-local symbolic-link leaves, including dangling links, before writing either output.
2. The original link and its target remain unchanged on rejection. A rejected `prepare` must not create the sibling plan or candidate output.
3. Ordinary external output files remain supported; repository output confinement and existing internal ancestor-link checks remain effective.
4. Deterministic CLI regression, independent Spec/Quality review, supported regression and protected source/release gates bind the exact candidate.
5. `run` validates the output path before invoking `run_campaign`, so an invalid output leaf cannot consume provider resources before rejection.

## Boundary

This change repairs file-output handling only. It does not execute a provider, certify a native target, change the trust registry, authorize a product release or replace ADK #153's real campaign evidence.
