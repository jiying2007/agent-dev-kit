# 7.2.0 context observability requirements

1. Measure resolved profile entry bytes without assuming all support material is initially loaded.
2. Account for `references/`, `scripts/`, and `assets/` separately as deferred potential context.
3. Expose profile-to-profile deltas without a quality score.
4. Clearly label bytes/4 token counts as a heuristic, never a provider tokenizer measurement.
5. Probe direct-target exported layouts in an isolated temporary root and verify file digests/loadability.
6. Never claim native runtime discovery/load/trigger from the source-layout probe.
7. Do not write user live HOME or change runtime/product qualification.
8. Enter quick/full regression and advance SemVer because this adds public CLI capability.
