# Design: smallest existing-asset improvement

Use existing `adk-adr-writer`, `adk-cross-team-handoff` and `adk-skill-composition-governance` reference; do not introduce parallel workflows. A cold-reader check operates on the final document and its authorized pointers, not on author's accumulated hidden context. It is lightweight self-review by default; independent validation only when actually performed and approved.

Feedback uses `failure_trace_ref` and `source_sha`, separates observed failure from hypothetical cases, adds minimal positive/negative examples in existing tests/fixtures, and preserves train/holdout separation. High-impact changes retain full security/approval/rollback gates; static tests cannot be called real model trials.

The six upstream method comparisons are read-only, blob-pinned, and not software dependencies. Existing public runtime and platform-neutral architecture are retained. Revert this PR to undo new guidance without deleting any existing skill.
