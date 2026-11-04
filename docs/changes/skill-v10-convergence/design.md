# Skill convergence — design

## Single authorities
- `manifest.json`: Skill identity, Profile, default locale and routing intent.
- `manifests/skill_content_contracts_v2.json`: capability class, runtime role, selection and effect ceilings. Delete language-support overrides.
- `adk-code-review-loop/SKILL.md`: snapshot, review, severity, evidence and replan. Optional guidance in `references/review-communication-guidance.md`.
- `adk-commit-pr-quality-gate/SKILL.md`: applicable commit/PR readiness evidence; repository `AGENTS.md` owns formatting/locale.
- `src/agent_dev_kit/commit_message_policy.py`: safe pure validation; output pass/needs-fix and exit 0/2. No filesystem writes or subprocess Git.
- `tests/test_skill_content.sh`: portable identity, typed and OpenAI metadata tests rather than line-count or fixed SOP template.

## Migration
Remove language-only Skill directories and Manifest/Profile references in one atomic Git tree; do not ship shim, alias or duplicate references. Deployment cleans old files only with governed installer ownership/digest evidence. Keep users' modified files untouched and classify as manual conflict.

## Risk controls
Read-only review unchanged. Only user-authorized SCM tool/Agent roles can mutate. E0/E1 minor tasks can record not_applicable evidence; E2/E3/schema/release/authorization cases remain fail-closed. ADK build requires Python 3.11+, deployed Skill assets do not intrinsically require Python.

## Rollback
Do not rewrite immutable tags. Revert the source PR with a new version if verification fails; consumers continue exact-pinned 9.0.0 until independent source-to-live promotion.
