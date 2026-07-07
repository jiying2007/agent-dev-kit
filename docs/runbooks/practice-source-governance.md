# Practice Source Governance

## Goal

Keep ADK assets source-neutral while allowing `llm_agent` to continuously mine official docs, runtime manuals and high-quality open-source repositories for reusable practices.

## Layer Model

| Layer | Owner | Purpose | Must Not |
|---|---|---|---|
| Reference sources | `llm_agent` | Track source URL/repo, retrieved date, license, freshness, evidence strength and adoption decision | Enable runtime behavior or copy source-specific structure into ADK core |
| Practice patterns | `llm_agent` + ADK governance | Distill Prompt, Context, Harness, Loop, Skill, Agent, Workflow and Profile practices into reusable mechanisms | Preserve source names as ADK capability names |
| Neutral ADK assets | `agent-dev-kit` | Implement patterns as skills, workflows, manifests, runbooks, tests and profiles | Depend on a single runtime, hosted service, user home directory or product-specific command |
| Runtime adapters/handoffs | ADK target owner | Express direct `tool_targets` or external `source-to-live` delivery chains | Change ADK core semantics or imply support without owner review |

## Intake Decision

Every candidate practice must be classified as one of:

- `adopt`: lands in ADK with deterministic validation.
- `adapt`: lands after reducing source-specific assumptions.
- `reject`: not useful, unsafe, duplicate or outside ADK boundaries.
- `archive-only`: valuable provenance, but no ADK asset change.

The decision record must include the source, mechanism, local applicability, target ADK asset, duplicate check, conflict check, maintenance cost, verification command and rollback boundary.

## Promotion Rules

- Prompt Engineering promotes into instruction hierarchy, task framing, examples, refusal/failure handling or eval fixtures.
- Context Engineering promotes into context layers, compression handoff, retrieval policy, memory governance or token budgets.
- Harness Engineering promotes into deterministic checkers, fixtures, evidence schemas, CI gates or review reports.
- Loop Engineering promotes into workflow closure, repair loops, automation report-only gates, worktree handoff or after-action review.
- Skill/Agent/Workflow/Profile patterns promote only through existing ADK taxonomy unless a new taxonomy slot is justified by repeated evidence.

## Hard Boundaries

- Source names may appear in reference docs, `reference_sources`, adoption matrices, archives, freshness manifests and explicit handoff records.
- Source names must not become active command names, default profile names, core skill names or direct tool target names unless the asset is an adapter for that specific runtime.
- Direct runtime support belongs in `tool_targets`; external runtime delivery belongs in `external_handoff_targets`.
- Codex remains an external source-to-live handoff target unless a separate owner-approved direct adapter design is accepted.
- Historical provenance must not be deleted to hide coupling; it must be separated from active runtime behavior.

## Verification

```bash
bash scripts/devkit.sh runtime-boundary
bash scripts/devkit.sh official-docs-governance --summary-json
bash scripts/devkit.sh runtime-capabilities --summary-json
bash scripts/devkit.sh validate --strict
bash tests/run_all.sh --quick
```
