# Codify Decision Fixture: Promotion Candidate False

delivery_goal: record a one-off runtime observation without promoting it

reusable_pattern:
  summary: a single dirty worktree status is evidence for this pilot only
  reusable_when: not applicable
  not_reusable_when: the observation depends on this session's uncommitted files

affected_asset:
  type: report
  path: reports/adk-capability-runtime-pilot-2026-05-30.md
  owner: adk-maintainer

promotion_candidate: false

next_task_friction_reduced: false

reduced_by:
  - none

reduction_evidence:
  summary: no durable asset reduces future work for this one-off observation
  evidence_path: reports/adk-capability-runtime-pilot-2026-05-30.md

do_not_promote_reason: one-off runtime observation

owner_review:
  required: false
  reviewer: none
  status: not-required
  reviewed_at: 2026-05-30

rollback_path:
  asset: reports/adk-capability-runtime-pilot-2026-05-30.md
  steps:
    - remove or supersede the one-off observation from the pilot report
  verification_after_rollback: rtk bash scripts/check-all.sh --quick

verification_evidence:
  commands:
    - command: rtk bash scripts/evidence-bundle.sh . --format json --max-summary-chars 1000
      exit_code: 0
      result_summary: evidence bundle reports current dirty strict subrepo state
      evidence_path: reports/adk-capability-runtime-pilot-2026-05-30.md
  artifacts:
    - reports/adk-capability-runtime-pilot-2026-05-30.md
  negative_or_disproved_path: not promoted because it is not a stable workflow rule

decision:
  status: do-not-promote
  next_action: keep as pilot evidence only
  next_review_by: 2026-06-15
