# Design — one interactive Skill, two modes

- Keep `adk-structured-requirements-questioning` as a single primary. `interactive_discovery` has explicit matcher phrases; no external runtime reference is installed.
- Explore: read context, open Why, one question/turn, 2–3 grounded options once intent is known, playback and concise design.
- Challenge: session-local dependency tree, numbered independent frontier, falsifiable counterexamples, user-approved decisions and no unrequested implementation.
- Confirmed decisions hand back to `adk-requirements-triage` for acceptance, then existing ADK execution and authorization continue. Never weaken R2, review or tool security.
- Matcher/contract source tests vs native multi-turn model A/B evidence are separate. Rollback by reverting PR; no persistent data migration.
