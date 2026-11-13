# Skill method efficiency — requirements (11.2.9)

## Goal
Follow-up to ADK 11.2.8 document refinement: eliminate *unnecessary work*, not just verbose output, in task decomposition, parallel-agent governance, test strategy, and growth review.

## Scope
- No new Agent, Skill, Workflow, timer or runtime engine.
- Human single-slice tasks must not invoke full task-package v2, three-point estimates or multi-agent review solely to fill a template.
- Machine-dispatched tasks retain strict v2 schema, evidence, permission, exit and handoff rules; shared files have one writer.
- Parallel requires economic benefit and disjoint resources; no indefinite model polling, high-cost model by default, or repeated full-diff transfer.
- Test levels preserve real red/green, resource isolation and validation; mock pass not equated with native/provider evidence.
- Growth review is index-first, privacy-safe, no implicit broad reading, token spend or external messages.

## Acceptance
- Existing triggers/permissions and profiles remain stable.
- Mandatory high-risk verification and authority semantics are preserved in four edited skill entries.
- 20 source-only design cases plus deterministic matcher tests; no claim of live LLM A/B results.
- Source-entry byte counts measured; no fixed per-day budget or paid Codex/Work usage.
