# Reuse Before Rebuild Fixture: Adapt Existing

problem_statement: add a gate for external method absorption without creating a parallel skill

existing_asset_search:
  commands:
    - command: rtk rg -n "external method|upstream intake|skill curation" agent-dev-kit/docs agent-dev-kit/skills
      exit_code: 0
      result_summary: found upstream intake and skill curation assets that can be extended
  searched_paths:
    - agent-dev-kit/docs/runbooks/upstream-intake.md
    - agent-dev-kit/docs/runbooks/skill-curation-delivery.md

candidate_assets:
  - path: agent-dev-kit/docs/runbooks/upstream-intake.md
    fit: adapt-existing
    gap: missing explicit reuse-before-rebuild decision fields
  - path: agent-dev-kit/templates/governance/reuse-before-rebuild-decision.md
    fit: build-fresh
    gap: no existing structured template for this exact decision

decision: adapt-existing

build_fresh_reason: not-applicable

verification_evidence:
  commands:
    - command: rtk bash scripts/check-reuse-before-rebuild.sh
      exit_code: 0
      result_summary: reuse-before-rebuild governance assets are present
      evidence_path: agent-dev-kit/tests/fixtures/reuse-before-rebuild/adapt_existing.md
  negative_or_disproved_path: build-fresh skill rejected because upstream intake and skill curation already own the workflow

