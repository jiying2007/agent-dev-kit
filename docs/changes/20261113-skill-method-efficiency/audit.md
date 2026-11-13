# Whole-portfolio source review (ADK 11.2.8 baseline)

Scope: 56 core + 9 optional Skills, total 65 SKILL.md entries, **284,427 UTF-8 bytes**, measured from the GitHub main tree at `4c6968f1d95f954788d8dfdba1393dd7e078eb6b`. These are file sizes, not runtime loaded context or billed token usage.

## Priority: evidence and human review
| Candidate | Entry bytes (baseline) | Decision | Reason |
|---|---:|---|---|
| adk-task-breakdown | 8,002 | ENHANCE now | hard 0.5–8h range, mandatory three-point estimate, full schema for simple tasks |
| adk-parallel-agent-governance | 8,347 | ENHANCE now | fixed worker count, full handoff/review overhead even when serial cheaper |
| adk-test-strategy | 6,605 | ENHANCE now | resource/test matrices should be conditional to actual risk and concurrency |
| adk-engineering-growth-review | 6,552 | ENHANCE now | overly wide default data inventory and mandatory full reports |
| adk-verification-before-completion | 9,476 | OBSERVE | authority-critical; deep split already uses references, shrinking could drop verification evidence |
| adk-code-review-loop | 7,146 | OBSERVE | two-verdict/reviewer independence and current ratchets are deliberate; real behavior A/B required |
| adk-commit-pr-quality-gate | 6,974 | STUDY | potential conditional checks; must not weaken branch/release gates |
| adk-embedded-remote-debug-log-triage | 6,746 | STUDY | instrument/transport failures potentially costly but device safety cannot be inferred |
| adk-token-context-governance | 6,540 | KEEP | already defines deferred reads, source preservation and fallback |
| adk-systematic-debugging | 6,133 | KEEP | already separates direct causality from uncertain cases, red/green and no blind retries |
| adk-planning-execution-loop | 3,711 | KEEP | already bounded 1–4 tasks, no model polling and stage-vs-final validation |
| adk-goal-authoring | 3,182 | KEEP | already avoids ungrounded token budgets and redundant planning |

## Negative results / constraints
- **Not every long Skill is wasteful.** Verification, release, security, embedded/HIL and authority gates are intentionally dense; removal needs real failure evidence, not a size-only metric.
- **No blanket source size cap**: keep per-profile source ratchets, not arbitrary line-count targets. A Skill's attached references do not necessarily load into context.
- No added daily ¥ limit, duplicate language Skills, permanent scheduled checks, auto approve, fake tests or paid provider evaluation.
- 20 new cases represent `not-measured` intended behavior; later real measurements must compare same model, workload, tools, permissions, cache and fixed budget, plus task success, refusals, review findings and token/latency.
