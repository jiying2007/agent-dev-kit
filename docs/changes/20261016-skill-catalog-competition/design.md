# Design

The existing `test_skill_trigger_matrix.sh` invokes a single Python unittest module. Extend that module with a second fixture parser and a public `match_text(manifest, prompt, scope="auto")` replay. A real collision also invokes the same matcher in explicit skill scope to establish positive overlap. Negated and abstain requests must never authorize mutation. Do not alter the production matcher or add a new CI job.

Risks: hand-curated examples can overfit simple lexical triggers; mitigated by disclosing evidence level and requiring source-fixed real behavior evaluation before any stronger conclusion. Rollback: revert this one candidate commit; no schema or state migration.
