# Archive Lifecycle Promotion Negative Fixture

source_mapping:
  source_reports:
    - reports/oss-analysis-gymaira1990-jpg-Mnemosyne-OS-2026-06-26.md
    - reports/oss-absorption-plan-gymaira1990-jpg-Mnemosyne-OS-2026-06-26.md
  adopted_as: existing memory/archive governance fixture
  upstream_runtime_imported: false

expected_failure: archive lifecycle promotion requires raw_evidence, owner_review, and rollback_path
must_not_promote: true
blocked_promotion_actions:
  - auto_promote_candidate
  - promoted

## Missing Raw Evidence

- id: candidate-missing-raw-evidence
  lifecycle_state: research
  requested_promotion: engineering
  write_route: archive
  raw_evidence:
  owner_review: reviewed-by-owner
  rollback_path: remove candidate from archive promotion queue
  contradiction_status: missing_evidence
  promotion_action: blocked
  expected_failure: missing raw_evidence blocks research to engineering promotion

## Missing Owner Review

- id: candidate-missing-owner-review
  lifecycle_state: research
  requested_promotion: archive
  write_route: archive
  raw_evidence: reports/oss-absorption-plan-gymaira1990-jpg-Mnemosyne-OS-2026-06-26.md
  owner_review:
  rollback_path: keep as research note until owner approval exists
  contradiction_status: missing_evidence
  promotion_action: blocked
  expected_failure: missing owner_review blocks research to archive promotion

## Missing Rollback Path

- id: candidate-missing-rollback-path
  lifecycle_state: engineering
  requested_promotion: archive
  write_route: archive
  raw_evidence: reports/oss-analysis-gymaira1990-jpg-Mnemosyne-OS-2026-06-26.md
  owner_review: reviewed-by-owner
  rollback_path:
  contradiction_status: missing_evidence
  promotion_action: blocked
  expected_failure: missing rollback_path blocks engineering to archive promotion

## Gate Expectation

- lifecycle_states: research, engineering, archive
- promotion_policy: research -> engineering -> archive requires all three gates
- raw_fallback_required: every promotion candidate keeps `raw_evidence`
- owner_gate_required: every promotion candidate keeps `owner_review`
- rollback_required: every promotion candidate keeps `rollback_path`
- safe_action: incomplete candidates stay `promotion_action: blocked`
