# Design: smallest existing-asset improvement

Use existing `adk-adr-writer`, `adk-cross-team-handoff` and `adk-skill-composition-governance` reference; do not introduce parallel workflows. A cold-reader check operates on the final document and its authorized pointers, not on author's accumulated hidden context. It is lightweight self-review by default; independent validation only when actually performed and approved.

Feedback uses `failure_trace_ref` and `source_sha`, separates observed failure from hypothetical cases, adds minimal positive/negative examples in existing tests/fixtures, and preserves train/holdout separation. High-impact changes retain full security/approval/rollback gates; static tests cannot be called real model trials.

The six upstream method comparisons are read-only, blob-pinned, and not software dependencies. Existing public runtime and platform-neutral architecture are retained. Revert this PR to undo new guidance without deleting any existing skill.

## Extension: production routing and lowest-cost implementation

The public matcher must select external-practice absorption for explicit **continued adoption** language, not just the read-only source-analysis skill. New catalog cases drive the real matcher with core and optional scopes, including local negation. Existing verified sources and PR context become the initial delta; never recreate a whole new campaign for each candidate. Inline Goal execution stays single-owner for nonconflicting write scopes, with phase checks and a final independent review when applicable; privilege/acceptance changes still go through protected gates.

The direct comparison added by this extension is in `docs/evals/external-skill-method-comparison-20261114-round3.md`. This is E0/E1 source and production-matcher behavior only; no native host model calls, task completion or Token improvement are claimed.
