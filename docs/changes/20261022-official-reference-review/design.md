# Design

The existing `manifests/external_agent_pattern_contracts.json` remains the single authority. This change adds no parallel registry or runtime capability. A separate research agent checks the actual official sources and proposes bounded metadata corrections; the coordinator integrates only the four reviewed records and the manifest update date. An independent reviewer checks both source support and the exact candidate difference before release consideration.

Evidence distinguishes current upstream observations from the already adopted local method contract. In particular, retaining a disabled adapter pinned to a previously reviewed revision does not claim compatibility with a newer upstream revision. Unknown or inaccessible facts stay explicit; an inaccessible source cannot receive a fresh reviewed date merely to make a gate pass.

The initial full-suite failure is the red evidence. After integration, run the canonical ecosystem/source gate and relevant governance checks before repeating full regression. Review the current Harness source bindings again if the additional change documentation alters the scanner's required source set. Existing history and earlier review records remain immutable.

Rollback is a source revert of this metadata and its new change record. No live installation, provider call, or source-to-live promotion is part of this change.
