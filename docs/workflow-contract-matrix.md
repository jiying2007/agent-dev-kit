# Workflow Contract Matrix

- generated_at: 2026-06-02T01:40:04Z
- source: manifest.yaml

## Workflow Matrix

| Workflow | Profiles | Command Risk | Primary Agent | Primary Skill | Supporting Skills | Verification |
|---|---|---|---|---|---|---|
| `adk-delivery-gate` | core, embedded-fullstack | low | `code-review-governor` | `adk-verification-before-completion` | adk-runtime-router, adk-requirements-triage, adk-task-breakdown, adk-test-strategy, adk-code-review-loop, adk-after-action-review, adk-token-context-governance, adk-commit-pr-quality-gate | rtk bash tests/run_all.sh --fail-fast |
| `feature-delivery` | core, embedded-fullstack | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-interface-contract-design, adk-unit-test-embedded, adk-verification-before-completion, adk-code-review-loop | rtk bash tests/test_validate.sh, rtk bash tests/test_workflow_closure.sh |
| `bugfix-delivery` | embedded-fullstack | low | `application-engineer` | `adk-systematic-debugging` | adk-task-breakdown, adk-verification-before-completion, adk-code-review-loop | rtk bash tests/test_workflow.sh, rtk bash tests/test_integration.sh |
| `release-hardening` | release-hardening | medium | `build-release-engineer` | `adk-release-versioning` | adk-test-strategy, adk-code-review-loop, adk-branch-closeout, adk-verification-before-completion, adk-commit-pr-quality-gate | rtk bash tests/test_validate.sh, rtk bash tests/test_profile_coherence.sh |
| `runtime-routing` | core, embedded-fullstack | low | `architecture-planner` | `adk-runtime-router` | adk-verification-before-completion, adk-repo-drift-remediation | rtk bash tests/test_skill_trigger_matrix.sh, rtk bash tests/test_workflow_closure.sh |
| `skill-curation-delivery` | core, team-core | low | `requirements-analyst` | `adk-requirements-triage` | adk-task-breakdown, adk-commit-pr-quality-gate, adk-verification-before-completion | rtk bash tests/test_catalog.sh, rtk bash tests/test_skill_sop_quality.sh |
