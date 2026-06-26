# Protected Key Collision Negative Fixture

source_mapping:
  source_reports:
    - reports/oss-analysis-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md
    - reports/oss-absorption-plan-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md
  adopted_as: existing memory/context governance fixture
  upstream_runtime_imported: false

expected_failure: duplicate stable identity key must enter conflict_review and must not auto-promote
must_not_auto_promote: true
blocked_promotion_actions:
  - auto_promote_candidate
  - promoted

## Correction Collision

- id: candidate-correction-old
  stable_identity_key: correction:llm_agent:contract-fixture-source-boundary
  protected_entry_class: correction
  event: ADD
  duplicate_key_status: first-seen
  contradiction_status: none
  promotion_action: review
  raw_evidence: reports/harness-loop-engineering-adoption-candidates-2026-06-26-batch2.md
- id: candidate-correction-new
  stable_identity_key: correction:llm_agent:contract-fixture-source-boundary
  protected_entry_class: correction
  event: UPDATE
  duplicate_key_status: collision
  contradiction_status: conflict_review
  promotion_action: conflict_review
  raw_evidence: reports/oss-analysis-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md

## Decision Collision

- id: candidate-decision-old
  stable_identity_key: decision:llm_agent:memory-fixture-scope
  protected_entry_class: decision
  event: ADD
  duplicate_key_status: first-seen
  contradiction_status: none
  promotion_action: review
  raw_evidence: reports/oss-absorption-plan-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md
- id: candidate-decision-new
  stable_identity_key: decision:llm_agent:memory-fixture-scope
  protected_entry_class: decision
  event: UPDATE
  duplicate_key_status: collision
  contradiction_status: conflict_review
  promotion_action: conflict_review
  raw_evidence: reports/oss-absorption-plan-gymaira1990-jpg-Mnemosyne-OS-2026-06-26.md

## Progress Collision

- id: candidate-progress-old
  stable_identity_key: progress:llm_agent:context-governance-fixture
  protected_entry_class: progress
  event: ADD
  duplicate_key_status: first-seen
  contradiction_status: none
  promotion_action: review
  raw_evidence: reports/oss-analysis-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md
- id: candidate-progress-new
  stable_identity_key: progress:llm_agent:context-governance-fixture
  protected_entry_class: progress
  event: UPDATE
  duplicate_key_status: collision
  contradiction_status: conflict_review
  promotion_action: conflict_review
  raw_evidence: reports/oss-absorption-plan-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md

## Execution Log Collision

- id: candidate-execution-log-old
  stable_identity_key: execution-log:llm_agent:check-token-budget
  protected_entry_class: execution-log
  event: ADD
  duplicate_key_status: first-seen
  contradiction_status: none
  promotion_action: review
  raw_evidence: reports/oss-analysis-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md
- id: candidate-execution-log-new
  stable_identity_key: execution-log:llm_agent:check-token-budget
  protected_entry_class: execution-log
  event: UPDATE
  duplicate_key_status: collision
  contradiction_status: conflict_review
  promotion_action: conflict_review
  raw_evidence: reports/oss-absorption-plan-gymaira1990-jpg-noah-gen3-type2-2026-06-26.md

## Gate Expectation

- deterministic_pre_filter: protected entry classes are recognized before LLM summarization
- stable_key_preservation: duplicate stable identity keys are not collapsed as noise
- conflict_policy: collision entries require `conflict_review`
- raw_fallback_required: every collision case keeps `raw_evidence`
