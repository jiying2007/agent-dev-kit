# Agent/Skill Content Architecture vNext — Tasks

## Phase 0 — Baseline Freeze
- [x] Lock base commit `d55c84b5b0ce86e8432d08e8c0d33f95bfb32725`.
- [x] Record 13 Agent identities, 57 core Skills, 8 optional Skills.
- [x] Record legacy content-quality assumptions and known duplication hotspots.
- [x] Add deterministic vNext baseline/ratchet policy.

## Phase 1 — Contract Foundation
- [x] Reuse existing `agent_value_contracts` as Agent permission/authority/handoff/eval typed authority; do not create a parallel behavior SSOT.
- [x] Add `skill-content-contract/v2` schema + full manifest-derived coverage.
- [x] Add `agent-handoff/v1` schema.
- [x] Add durable `content-architecture-policy/v1` for identity/size/content ratchets.
- [x] Register vNext contracts in the unified contract registry.
- [x] Add parity/schema validator.

## Phase 2 — Agent Thin Rewrite
- [x] Rewrite all 13 Agents to thin role contracts.
- [x] Preserve manifest ownership/default-skill/handoff identities.
- [x] Remove embedded SOP/toolbox/commands/examples from Agent core.

## Phase 3 — Skill Contract v2
- [x] Classify all 57 core + 8 optional Skills through derivation + reviewed overrides.
- [x] Add runtime role, selection group, effect ceiling and eval obligations.
- [x] Reconcile every explicit `routing.intents[].primary_skill` with v2 `runtime_role=primary`.
- [x] Rewrite `adk-context-engineering` to context policy planner.
- [x] Rewrite `adk-bsp-analysis` as canonical BSP procedure surface.

## Phase 4 — Content De-duplication
- [x] Add Agent forbidden-heading/command/size ratchets.
- [x] Add Agent↔default-Skill deterministic overlap gate.
- [x] Make BSP the first explicit duplication fixture.

## Phase 5 — Router vNext
- [x] Preserve one-primary/progressive-disclosure runtime-router contract.
- [x] Add deterministic candidate eligibility metadata through Skill v2 contract.
- [x] Add `matcher_vnext` runtime adapter: explicit routing IR remains authoritative, implicit fallback only admits `runtime_role=primary`.
- [x] Apply effect ceiling as a permission upper bound only; never grant permission.
- [x] Promote a supporting lexical trigger only to the unique primary in the same `selection_group`; ambiguity fails closed.
- [x] Make runtime and CI share `resolve_skill_content()` to prevent policy drift.
- [x] Add runtime regression for explicit supporting load, implicit-primary rejection, same-group promotion and valid primary fallback.

## Phase 6 — Guardrail Enforcement
- [x] Add effect-ceiling taxonomy and fail-closed validation.
- [x] Add typed handoff permission boundary.
- [x] Keep external runtime and production authority disabled unless separately activated.

## Phase 7 — Behavioral Eval
- [x] Add routing/collision/authority fixture contract.
- [x] Add structural E0/E1/E3 CI gate for all identities.
- [x] Preserve `not-measured` for unobserved production E2–E4 instead of fabricating evidence.

## Phase 8 — Compatibility Cleanup
- [x] Replace legacy one-template content-quality test.
- [x] Migrate core `validation_contract.py` away from old universal Agent/Skill headings.
- [x] Rewrite canonical runtime/Skill format docs to vNext.
- [x] Do not add permanent Skill v1/v2 parser compatibility shim.
- [x] Remove the attempted parallel Agent behavior manifest/schema and reuse Agent Value authority.
- [x] Move long-lived ratchets out of active change evidence into `manifests/content_architecture_policy.json` so archive is safe.
- [x] Functional exact-head `6ea60edce7f375a226343637d152938027717ced` hosted CI all green: main CI 6/6 jobs, full regression 80/80 on Python 3.11 and 3.12, platform/CodeQL/dependency/branch-gc all success.
- [x] Independent implementation review PASS with blocker=0 / major=0.
- [x] Set change lifecycle to `review-passed` and archive under `docs/changes/archive/20260915-agent-skill-content-vnext/` in the archive-final tree.
- [ ] Revalidate the archived final exact head.
- [ ] Squash merge PR #75 with expected HEAD.
- [ ] Fresh-main validation + promotion evidence all green.

## Closure Rule
Phase 0–8 is terminal only after archived-final exact-head CI, expected-head squash merge and fresh-main CI/promotion evidence. Runtime/field value measurement is a separate evidence-authority concern and may remain explicitly `not-measured`; that state is not treated as a successful runtime claim.
