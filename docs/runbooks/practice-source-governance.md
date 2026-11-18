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

Use Root's existing `external-practice-decision/v1`: [`schemas/external-practice-decision.schema.json`](https://github.com/jiying2007/llm_agent/blob/main/schemas/external-practice-decision.schema.json) and [`docs/absorption-governance.md` §4](https://github.com/jiying2007/llm_agent/blob/main/docs/absorption-governance.md). Its only decision values are `ADOPT | MERGE | ENHANCE | OBSERVE | REJECT`. The independent owner records the decision separately from the candidate; `ADOPT/MERGE/ENHANCE` authorize a change proposal, not implementation, publishing or live effects.

`adapt` describes how a method is changed, not a decision enum: check existing assets before choosing `MERGE` or `ENHANCE`; justify `ADOPT` only for a distinct addition. `archive-only` describes retention, not approval: choose `OBSERVE` for a candidate awaiting specific evidence, or `REJECT` with its reason. Retain historical descriptions as provenance; do not add aliases, fallback readers or a second decision registry.

## Method Record — seven fields, existing evidence

Embed the following in the existing change design/verification or Root decision evidence, linking facts already recorded there. These are human-readable headings, not new schema fields, mandatory extra files or a parallel method catalog. Keep the typed candidate/decision/effect contracts unchanged.

| Field | Minimum useful content |
|---|---|
| 问题与证据 | Expected/observed behavior, affected task and redacted failure pointer; label hypothetical cases as design cases. |
| 方法机制 | One falsifiable explanation of how the proposed change addresses that failure. |
| 适用与不适用条件 | Task/version/permission boundaries, near-miss cases and when existing behavior suffices. |
| 资产归属 | Existing Skill/tool/contract/reference to update, owner and duplicate/conflict check; explain any new asset. |
| 来源与取舍 | Exact source commit and file, or document revision/content digest with retrieval date; license, selected mechanism, rejected assumptions and canonical decision reference. A moving URL alone is not fixed evidence. |
| 验证与效果 | Baseline/candidate, case set, verifier and raw evidence pointers; actual quality, cost and limitations, including missing measurements. Source size is not measured Token savings. |
| 维护与退出 | Review trigger, owner, stop/retire conditions, replacement/consumer impact and rollback pointer. |

Start from a verified problem, reuse existing assets, change one mechanism, verify the affected behavior, then use the existing release/consumer chain. Development examples guide edits; frozen acceptance evidence decides a claim. See [evaluation boundaries](skill-source-eval-and-runtime-qualification.md) and the [behavior protocol](../../optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md); do not copy their rules into every Skill.

Stop a candidate when its registered budget is exhausted or repeated attempts add no distinguishing evidence. Keep missing authorized runtime evidence as unmeasured with a concrete resume condition; do not replace execution with recurring inspection. Verified harm, overlap or obsolete assumptions trigger an owner retirement review under the existing lifecycle gates, never automatic deletion based on age or missing measurements.

For method-only source refs that name a local reference repository, keep the current canonical HTTPS repository URL and exact `reference_pin` beside the read-only `remote_head_observed`, `remote_relation`, `canonical_checked_at` and `ancestry_checked=false`. Preserve an old URL as `historical_url` when ownership or routing changed. `retrieved_at` remains the date of the historical method review; a fresh HEAD observation does not prove that method content was reread, that pin ancestry was checked, or that runtime/install adoption was approved. The checker validates these declared identities offline and never fetches a repository.

Standalone ADK checks keep the parent repository optional. In a governed `llm_agent` workspace, pass `--reference-lock ../manifests/reference_pins.json` to the same checker to compare local method source URLs and exact pins with the Root SSOT. The URL comparison only normalizes an optional `.git` suffix; it does not follow redirects or fetch content. Use `--max-observation-age-days N` (optionally with `--as-of YYYY-MM-DD` for a repeatable review) when current HEAD evidence is required. Without that explicit flag the checker validates dates and declared relationships but does not claim the observation is fresh. This is declaration parity, not a SLSA attestation, remote ancestry check or permission to promote the pin.

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

