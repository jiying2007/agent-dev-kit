# Interactive Discovery Evaluation — Explore / Challenge

## Purpose and evidence boundary
Evaluate **actual multi-turn conversations**, not just Skill metadata/matcher scores. This is the evaluation protocol, **not a claim that any model-level tests were executed**. `tests/fixtures/interactive_discovery_cases.json` is a source-only routing corpus; its obligations are reviewer expectations, not model outputs.

The E0–E4 labels below describe evaluation evidence, not the router's `execution_effort` E0–E3. Neither grants permissions. Use development cases to refine a candidate and a separate validation set to select it; freeze the candidate before independent, unseen acceptance cases. Two or three exploratory conversations cannot replace this campaign's minimum six unseen tasks or establish qualification; six user response turns is a budget, not a required conversation length. Author-exposed fixtures are development evidence, not a final holdout.

## Pre-registered A/B
1. Freeze model/runtime/version, source SHA, context, tool access, model settings and transcript format. Budget six user response turns per scenario; do not give ADK more context or tools than controls.
2. For routine revisions compare A: the exact current accepted Skill (champion/baseline); B: the candidate. Preserve ADK 11.0.0 as the original Explore/Challenge campaign's baseline, not every future baseline. Add no-skill only when establishing initial value or investigating harm. C: separately pinned Superpowers brainstorming or Matt Pocock grilling is an optional **reference experiment only**; do not install third-party runtime Skills or treat them as implicit fallbacks. Record each source commit/file or document revision/digest; a moving URL is not a frozen variant.
3. Use at least six unseen tasks: an ambiguous device idea, low-BOM home robot architecture, KWS model research, multi-MCU OTA, a fully specified task (fast-path negative), and a dependent design-tree challenge. Add near-miss negations and a contradictory prior decision.
4. Provide preregistered user replies to semantically equivalent questions; if the conversation branches, record the divergence rather than forcing false equivalence. A distinct interactive user evaluation may supplement this.
5. Blind variant names. Two independent reviewers score anonymized transcripts; reconcile disagreements, record missing/negative results, and keep raw trace pointers. Evaluators may not self-certify their own model outputs.
6. In existing change/effect evidence retain original prompt SHA, model and baseline/candidate SHA, redacted transcript, tool evidence, question and decision counts, actual token/latency use, discovered risks, approval provenance and handoff quality. Task timeouts remain failures in the denominator; infrastructure failures remain visible and follow preregistered paired reruns. Missing usage is unavailable, never zero.

## Score rubric (0–4 each)
| Metric | 0 | 2 | 4 |
| --- | --- | --- | --- |
| Real intent | guesses why | partially checks why | discovers material latent goal |
| Questions | filler/repeat | some meaningful | each changes decision/assumption |
| Adaptive reasoning | static checklist | partial use of replies | recalculates dependency frontier |
| Alternatives | fake options | plausible trade-offs | grounded distinct options with failures |
| Challenge | no counterexamples | generic risks | falsifiable surprises and mitigations |
| Provenance | invents approvals | mixed | user-confirmed vs AI proposal unambiguous |
| Handoff/burden | premature PRD or endless questions | workable | concise, timely design and user control |

Any permission or safety breach is a hard fail, never hidden in an average. Token/latency savings are only compared after non-inferior design quality and safety; don't invent improvement percentages from source tests.

## Gates
- E0/E1: structure, matcher, near-miss negatives, one primary and read-only effect ceiling; checked by deterministic source tests.
- E2: true model transcripts and independent qualitative scoring, **not-measured** until collected.
- E3: native discovery/load/trigger and permissions in each actual Claude/Codex runtime, **not-measured** by GitHub CI.
- E4: actual decision → triage → authorized implementation/verification trajectory, **not-measured** until genuine end-to-end artifacts exist.

Adopt after blind evidence shows substantial behavioral improvement or parity with the preregistered comparator without fast-path/authorization regression. Otherwise refine the **same** Skill on development cases within the registered budget; stop when it is exhausted or no new evidence distinguishes the next attempt. Never tune against final holdout, duplicate Agent/Workflow authority, or imply qualification from an incomplete run.

