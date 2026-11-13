# Method-only design and external sources

This effort does **not create a new Agent/Skill/Workflow**, change typed runtime permissions, or import external source code. Existing `adk-task-breakdown`, `adk-parallel-agent-governance`, `adk-test-strategy` and `adk-engineering-growth-review` remain owners. Long examples move to on-demand references.

## External methods evaluated
- OpenAI: https://learn.chatgpt.com/docs/build-skills — progressive disclosure, description budgets, selective loading.
- OpenAI: https://developers.openai.com/blog/eval-skills — empirical test baseline and real task behavior before claiming improvement.
- Agent Skills: https://agentskills.io/specification — compact SKILL.md and one-hop references.
- Anthropic: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices — focused examples, edge cases, tests.
- Superpowers v7.0.1: https://github.com/obra/superpowers/releases — ask only when needed; move long procedures to deferred references.
- Microsoft Skills: https://github.com/microsoft/skills — acceptance criteria and bounded iterative evaluation, not automatic endless looping.
- Microsoft Waza: https://github.com/microsoft/waza — separate structural/token checks from measured behavioral effectiveness.
- Addy Osmani: https://github.com/addyosmani/agent-skills/releases — deterministic route cases, non-vacuous negatives and fresh run identity.

All are **method-only** references. No third-party Skill/code copied; no installation or new network permission.

## Technical decisions
- Task decomposition: human short path vs strict machine v2 path, estimate only on demand, ready frontier must be evidence-gated.
- Parallel orchestration: admission includes communication/review/integration cost and resources; may choose serial, 1 worker or any safe number based on benefit, never force 2–4 workers.
- Test strategy: Level 0/1/2 evidence adapted by behavior/risk, resource matrix only when parallel is proposed.
- Growth review: index-first, smallest authorized scope, actionable evidence-backed suggestions; no implicit full history, personal attribute inference or external sending.
- No changes to recently optimized Goal/Loop or verification/release/security gates; they are high-risk and require separate behavior-level tests.

## Rollback and measurement
Revert this PR to restore the four old Skill files, references, tests and docs. Runtime permission/manifest identity unchanged except source patch release number. Static size reduction is **not** model token savings or quality proof. `not-measured` until an approved fixed-budget A/B with real tasks.
