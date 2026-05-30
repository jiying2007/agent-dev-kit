# Codify Decision Fixture: Promotion Candidate True

delivery_goal: validate low-token trigger routing in a runtime pilot

reusable_pattern:
  summary: capability-specific runtime phrases must be covered by skill triggers
  reusable_when: documented capability phrases fail to match their owning skill
  not_reusable_when: the phrase is task-specific session wording

affected_asset:
  type: skill-trigger
  path: skills/adk-token-context-governance/SKILL.md
  owner: adk-maintainer

promotion_candidate: true

do_not_promote_reason: not-applicable

owner_review:
  required: true
  reviewer: adk-maintainer
  status: approved
  reviewed_at: 2026-05-30

rollback_path:
  asset: skills/adk-token-context-governance/SKILL.md
  steps:
    - remove the trigger phrases added for the runtime pilot
    - rerun skill trigger and capability uplift tests
  verification_after_rollback: rtk bash tests/test_skill_trigger_matrix.sh

verification_evidence:
  commands:
    - command: rtk bash tests/test_skill_trigger_matrix.sh
      exit_code: 0
      result_summary: trigger matrix passes with runtime capability phrases
      evidence_path: reports/adk-capability-runtime-pilot-2026-05-30.md
  artifacts:
    - reports/adk-capability-runtime-pilot-2026-05-30.md
  negative_or_disproved_path: original low-token phrase did not match before trigger update

decision:
  status: promote
  next_action: keep trigger fixture and semantic gate
  next_review_by: 2026-06-15
