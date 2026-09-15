# Agent/Skill Content Architecture vNext — Checklist

## Identity / SSOT
- [x] `manifest.json` remains identity/product-boundary SSOT.
- [x] New contracts reference or derive from IDs; no duplicate path/description/default-skill catalog.
- [x] Agent identity count remains 13.
- [x] Existing Agent Value contract remains the single typed Agent permission/authority/handoff/eval authority.
- [x] Long-lived content ratchets live in registered `content-architecture-policy/v1`, not active change evidence.

## Agent
- [x] All agents use thin role contract headings.
- [x] No Agent carries procedural SOP/toolbox/command cookbook/examples.
- [x] Permission boundary and handoff are explicit.
- [x] Default capabilities reference manifest Skill IDs only.

## Skill
- [x] All core and optional skills covered by v2 derivation/override policy.
- [x] Capability class and runtime role are orthogonal.
- [x] Every explicit routing primary resolves `runtime_role=primary`.
- [x] Primary/supporting/governance/fallback semantics are explicit.
- [x] Effect ceiling is a ceiling, never an authorization grant.

## Routing / Guardrails
- [x] Exactly-one-primary remains runtime invariant.
- [x] `matcher_vnext` consumes Skill v2 on public match surfaces.
- [x] Implicit fallback cannot promote supporting/governance/fallback assets directly to primary.
- [x] Supporting lexical triggers may promote only the unique primary in the same selection group; ambiguity fails closed.
- [x] Explicit supporting Skill load remains available.
- [x] Runtime and CI share the same Skill v2 resolver.
- [x] Selection group and effect ceiling are machine-checkable.
- [x] Handoff cannot expand permission.
- [x] External runtime remains disabled by default.

## Eval
- [x] Schema/parity gate.
- [x] Routing/collision fixture gate.
- [x] Authority/permission negative fixture contract.
- [x] Runtime eligibility regression covers supporting rejection, same-group primary promotion and normal primary fallback.
- [x] Full repository regression is 80/80 on Python 3.11 and Python 3.12 at functional exact head `6ea60edce7f375a226343637d152938027717ced`.
- [x] Unobserved production metrics remain `not-measured`.

## Cleanup
- [x] Legacy mandatory headings gate removed from test and core validator.
- [x] Canonical Agent/Skill runtime docs rewritten to vNext.
- [x] No permanent Skill v1/v2 parser shim added.
- [x] No Agent identity deleted without value evidence.
- [x] Parallel Agent behavior manifest/schema removed; no duplicate behavior authority retained.
- [x] Hosted functional exact-head CI passed.
- [x] Independent review PASS / change state `review-passed`.
- [x] Change package moved to the archive path in the archive-final tree.
- [ ] Archived-final exact-head hosted CI passed.
- [ ] PR squash merged with expected head.
- [ ] Fresh-main hosted CI + promotion evidence passed.
