# Interactive Discovery Evaluation — Explore / Challenge

## Purpose and evidence boundary
Evaluate **actual multi-turn conversations**, not just Skill metadata/matcher scores. This is the evaluation protocol, **not a claim that any model-level tests were executed**. `tests/fixtures/interactive_discovery_cases.json` is a source-only routing corpus; its obligations are reviewer expectations, not model outputs.

## Pre-registered A/B
1. Freeze model/runtime/version, source SHA, context, tool access, model settings and transcript format. Budget six user response turns per scenario; do not give ADK more context or tools than controls.
2. Compare A: prior ADK 11.0.0 questioning; B: candidate ADK Explore/Challenge; C: separately pinned Superpowers brainstorming or Matt Pocock grilling as a **reference experiment only**. Do not install third-party runtime Skills or treat them as implicit fallbacks.
3. Use at least six unseen tasks: an ambiguous device idea, low-BOM home robot architecture, KWS model research, multi-MCU OTA, a fully specified task (fast-path negative), and a dependent design-tree challenge. Add near-miss negations and a contradictory prior decision.
4. Provide preregistered user replies to semantically equivalent questions; if the conversation branches, record the divergence rather than forcing false equivalence. A distinct interactive user evaluation may supplement this.
5. Blind variant names. Two independent reviewers score anonymized transcripts; reconcile disagreements, record missing/negative results, and keep raw trace pointers. Evaluators may not self-certify their own model outputs.
6. Per case retain original prompt SHA, model and candidate SHA, full transcript, tool evidence, question and decision counts, token/latency use, discovered risks, approval provenance and follow-on handoff quality.

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

Adopt after blind evidence shows substantial behavioral improvement or parity with the chosen reference without fast-path/authorization regression. Otherwise improve the **same** Skill and rerun, not duplicate Agent or Workflow authority.
