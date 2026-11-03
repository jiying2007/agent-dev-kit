# Independent AI Harness source review — ADK 8.2.2

- Reviewer: `ai/chatgpt/adk233-independent-source-review` — an independent AI source-review context, not a human, GitHub principal, implementation author, owner or APPROVE event.
- Source reviewed: PR #233, exact implementation HEAD `f9fd246436d603d6ca20fb5e945b801707aa6f55`; fresh 8.2.1 base `950c63a3c0e943f80e57f032486985362260c129`, 15 changed file patches.
- Reviewed at (UTC): `2026-11-03T12:44:48Z`.
- Scope: repository-source Spec/Quality and seven Harness dimensions only. This does **not** certify Product M5, native runtime campaigns, devices, field observations, credentials, Root pin, a merge, tag or release.

## Independent Spec finding

**PASS for the bounded 8.2.2 source change.** The existing three managed Skills are attached to specialist Profiles rather than expanded into default `core`: `adk-planning-execution-loop` belongs to `team-core`, `adk-offline-core-dump-triage` to `embedded-fullstack` and `incident-response`, and `adk-embedded-storage-layout-migration` to `embedded-fullstack`. The `long_execution` route is explicitly `team-core`; false optional-install availability is removed. The prior Major in review #5752110429 is fixed in current `_routing_primary_coverage`: it checks each declared scenario Profile, including a mixed valid+invalid Profile set, against actual resolved Skill membership; unknown, empty, duplicate Profile declarations and unknown intents fail closed. Optional Skills retain explicit opt-in. The source route matrix, generated Catalog projection, and negative fixtures agree for the reviewed paths. Neither device-write permission nor a new runtime is implied.

## Independent Quality finding

**PASS for source semantics and existing deterministic regressions, with CI bootstrap limitation.** The complete 15-file patch was inspected. Candidate/source version is 8.2.2 across `.version-lock`, manifest, pyproject, package and docs; requires-python remains `>=3.8`. Profile source-byte ratchets changed only for impacted specialist/inheriting profiles, not default core. M5 minimum tasks and thresholds are not weakened. Active protected Ruleset 23394761 and required checks were read without modification. Native PR run [41636174078](https://github.com/jiying2007/agent-dev-kit/actions/runs/41636174078) at implementation HEAD confirmed all three Python 3.8/3.11/3.12 contract jobs passed. In all three regressions, `test_manifest_consumer_boundary`, `test_profile_coherence`, `test_profile_context_footprint` and `test_asset_taxonomy` passed; each was 100/101. Sole regression failure `test_harness_readiness` diagnosed the pre-existing 8.2.1 record's stale source digest. The aggregate `deterministic-eval-package` correctly failed closed, not bypassed. This new source-bound record requires fresh canonical validation and post-commit native CI and is not itself evidence of CI green.

## Seven dimension observations

1. **context_legibility** — Reviewed `AGENTS.md`, `README.md`, `CONTEXT.md`, versioned user-facing Catalog and routing reference; new specialist selection is described without implying default-core installation.
2. **spec_and_execution_contract** — Checked exact `manifest.json` routing/intent/profile selection, 14 route scenarios, planned vs execution distinction, source-version gates, changed source implementation and deterministic negative fixtures; each declared required Profile must load its routed primary.
3. **tool_and_permission_boundary** — No new provider/credential/field automation, native campaign or live-device write authority in patch. Explicit Profile selection and Optional Skill opt-in stay separate from mutation permission; default `core` remains unchanged.
4. **state_and_knowledge_continuity** — Inspected the raw evaluator's state/runbook references, seven source-bound dimension owner/date requirements, preserved 8.2.1 history and new 8.2.2 source identity.
5. **verification_review_and_eval** — Inspected CI/CodeQL/Dependency/Platform/Branch-GC evidence and three-version native regression logs, including `test_profile_coherence`, `test_manifest_consumer_boundary`, `test_asset_taxonomy`, 8.2.1 stale digest failure and aggregate fail-closed. No real Claude/Codex native campaign was run.
6. **recovery_and_rollback** — Source-checked existing `scripts/backup-rollback.sh`, governed runbooks and no change to release rollback or source-to-live boundaries.
7. **freshness_and_entropy_control** — Validated source version, Catalog projections, ownership markers, formatter/catalog tests, default-core no-growth, byte ratchet changes and preserved unmodified CI/Ruleset/M5 thresholds.

## Source identity and readiness contract

The repository-source plan was derived from the **untruncated** current evaluator: 44 unique raw scan evidence paths (including the hidden path `docs/runbooks/codex-runtime-method-boundary.md` and all required test entries); union with all 15 changed paths plus all three mandatory Harness evaluator/contract sources and `manifests/workflow_ir_policy.json` gives **62 distinct current sources**, plus this independent reviewer-authored report as one evidence reference = 63/64. All 62 source UTF-8 bytes, current Policy and authorization, and three validator modules were fetched from this exact GitHub HEAD and independently SHA256 hashed; the companion JSON record binds those bytes. The report is an independent observation, not a replacement for canonical `validate_review` or `run_harness_readiness` in a full checkout.

## Limitations and non-authorization

This is an AI source review, not a human approval or GitHub independent principal. The only old-HEAD CI failure was stale 8.2.1 source-bound evidence; source and Quality verdicts do not pre-approve the new artifact. This evidence-only change must pass canonical validation and all required exact-new-HEAD GitHub jobs before any seven-dimension claim of validated readiness. No real device, field/M5 qualification, runtime provider execution, user-value metrics, Release/Tag/Root pin, deployment or merge is claimed.
