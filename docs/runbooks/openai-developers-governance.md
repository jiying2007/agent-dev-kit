# OpenAI Developers Governance Runbook

## Goal

Use official OpenAI Developers guidance as a current reference source while keeping `agent-dev-kit` deterministic, reviewable, locally validated and platform-neutral. OpenAI product-specific pages may be cited as source material, but promoted ADK contracts must use generic runtime, runner, command-policy, tool and handoff terminology.

## Intake Rules

1. Prefer the official OpenAI docs MCP source. Fallback web lookup must stay on official OpenAI domains.
2. Register each adopted source in `manifests/official_docs_freshness_gates.json`.
3. Each record must include `url`, `retrieved_at`, `review_status`, `expires_at`, `adoption_scope`, owner, decision and required checks.
4. Expired sources cannot promote new rules until re-reviewed.
5. Cookbook examples remain examples unless converted into adk-native contracts with tests.

## Landing Map

| Priority | Landing Target | Required Evidence |
|---|---|---|
| P0 | Skill discovery, context compaction, official source freshness | reference doc, freshness manifest, token-budget check |
| P0 | Agent task framing and reusable guidance | task card with Goal/Context/Constraints/Done-when, AGENTS/skill promotion rationale |
| P0 | ADK runtime policy, managed requirements, sandbox defaults | runtime policy manifest, forbidden default list, runtime-boundary check |
| P0 | Codex config, permissions and memory runtime boundaries | config-key deny list, granular approval policy, permission profile policy, memory runtime policy |
| P0 | ADK command rules and Docs MCP setup | rules contract manifest, inline rule examples, cross-tool Docs MCP manifest |
| P1 | Trace/eval contracts and MCP/tool safety hints | eval suite manifest, trace contract, MCP audit manifest, check script |
| P1 | Developer-mode tool selection and data-only MCP shape | action-oriented tool descriptions, JSON payload review, search/fetch structuredContent contract |
| P1 | MCP runtime options, App Server API and session memory | MCP timeout/OAuth fields, runtime API contract, context state contract |
| P1 | Macro eval for repeated agentic failures | trace summary population, recurring pattern report, regression promotion record |
| P1 | Hooks, slash commands and ADK runner contracts | hook audit manifest, slash command audit manifest, ADK runner contract |
| P1 | Structured outputs and strict tool schemas | schema-backed task/evidence/handoff contracts, refusal handling, strict parameter policy |
| P1 | Tool-search style lazy loading | namespace summaries, deferred skill/tool schemas, token budget and loaded-tool evidence |
| P1 | ADK automations and worktrees | report-only automation records, first-run review, worktree handoff and cleanup gates |
| P1 | Agent improvement loop | traces, human/model feedback, eval candidate, validation gate, ranked recommendation and ADK handoff |
| P1 | CI/PR review governance | trusted-trigger decision, protected secret boundary, structured findings schema, SCM payload review and inline anchoring tests |
| P1 | Skill operational reproducibility | discoverability, negative examples, explicit version pinning, deterministic stdout, known output paths and network allowlists |
| P1 | Codex glossary terminology alignment | surface-term manifest, terminology drift review, docs lint candidate |
| P1 | Executable runtime capability gates | permission profile lint, MCP runtime contract lint, subagent evidence schema, terminology lint |
| P2 | Agents SDK taxonomy and future migration boundary | taxonomy note, non-goals, pilot requirement |
| P2 | ADK plugin and marketplace packaging | plugin marketplace contract, source path containment, install/auth policy review |
| P2 | Responses API migration and retrieval | watch-only source record, state-handoff contract, archive/retrieval pilot eval requirement |

## Promotion Gate

Official guidance can become a default adk rule only when:

- The source is current and official.
- The adopted rule is expressed in an adk-owned doc, manifest, skill or script.
- A deterministic check catches missing or stale governance fields.
- The change does not widen runtime permissions, network access or external write capability.
- Completion evidence includes command, exit code, result summary and affected artifacts.
- Runtime policy changes preserve the sandbox boundary unless a high-risk exception has explicit approval, rollback and postcondition evidence.
- Command approval rules include `match` and `not_match` examples and are checked before promotion.
- Network proxy dangerous settings, all-Unix-socket access and live web search cannot become defaults.
- Hooks are event-specific and do not rely on unsupported fields or ignored matchers.
- Plugin marketplace entries have source containment, version metadata, publisher metadata, installation policy and authentication policy.
- Context summaries preserve latest goal, invalidated goals, evidence paths, failed assumptions and next action.
- Task framing includes Goal, Context, Constraints and Done-when; adk task cards add Primary Action, Action Mode, Verification, Artifacts and Blockers.
- Skill descriptions can still route correctly when shortened; they front-load use case, boundary and trigger phrases.
- Tool descriptions name when to use the tool, when not to use it, required input shape, parameter constraints and side-effect class.
- Data-only MCP sources declare `search` / `fetch` behavior, structured output shape, citation URL policy and prompt-injection risk review.
- Trace-derived failures are grouped by model version, prompt version, orchestration mode and primary skill before becoming regression tests.
- Machine-consumed task packages, evidence indexes and handoff summaries use schema-backed fields; valid JSON alone is not sufficient.
- Tool/function contracts prefer strict schemas with required fields, enum constraints and explicit additional-property denial.
- Large skill/tool catalogs expose namespace summaries first and defer full bodies, references or schemas until a routing decision is justified.
- Automation records are disabled by default, report-only until reviewed, and include cadence, data source, stop condition, first-run review and cleanup policy.
- Background worktrees record base branch/commit, dirty-state decision, worktree path, handoff gate and retention/cleanup decision.
- Agent improvement loops include traces, feedback, eval candidate, validation result, ranked recommendations and an ADK handoff before changing prompts, skills or workflows.
- CI/PR review runners are disabled by default, restrict protected secrets on untrusted PRs, validate structured findings before SCM write actions and record inline anchoring decisions.
- Production skill usage pins the skill version and compatible runtime/model assumption; scripted skills expose deterministic stdout, known output paths, loud failures and dry-run behavior.
- Project-local runtime config must not override machine-local provider, auth, profile, notification, base URL, experimental realtime or telemetry keys.
- Granular approval policies record sandbox posture, command rules, MCP elicitation, `request_permission` behavior and skill approval behavior. Auto-review is evidence, not human approval.
- Permission profiles define least-privilege filesystem and network boundaries, including workspace roots, deny-read paths, domain policy and Unix socket allowlists.
- Memory runtime remains opt-in and owner-reviewed when external context contributed to the candidate memory. Raw evidence fallback must remain available.
- Codex glossary terms are mapped before new manifests, skills or runbooks use agent, skill, plugin, automation, worktree, MCP server or permission profile language.

## Rejection Gate

Reject or keep as observe-only when:

- The source is non-official, expired or lacks retrieval metadata.
- The content is a product example but not a reusable governance rule.
- The change would replace existing adk lifecycle assets without a pilot.
- The change requires hidden credentials, external writes or broad tool permissions.
- The change treats `danger-full-access + never` as a reusable default.
- The change promotes non-loopback proxy listeners, all Unix socket access or live web search as default behavior.
- The change adds a broad command prefix rule without positive and negative examples.
- The change uses project-local config to override machine-local provider, auth, profile or telemetry routing keys.
- The change uses hooks to bypass sandbox, approvals or managed requirements.
- The change promotes personal marketplace entries without source/auth/install review.
- The change treats structured output parse failure as a successful result.
- The change exposes a large tool or skill catalog up front when a namespace/lazy-loading path would preserve context and routing quality.
- The change schedules unattended automation without first-run review, stop condition or report-only default.
- The change deletes or hands off a worktree without diff/snapshot evidence and retention decision.
- The change promotes model-generated feedback without human or deterministic validation evidence.
- The change enables CI review publishing without trusted-trigger, secret-isolation or schema-validation evidence.
- The change posts inline comments without right-side diff anchoring validation.
- The change promotes an unversioned skill or nondeterministic skill script into production defaults.

## Control Plane Checks

1. Runtime config: compare declared policy against `config.toml` or `/debug-config` output when available.
2. Sandbox: classify preset as low-risk, medium or critical. Critical presets must stay opt-in and evidence-bound.
3. Hooks: verify event support, matcher support, output fields, trust status, timeout and log redaction.
4. Slash commands: classify commands by read-only, destructive, open-world and approval requirements.
5. ADK runner: record `threadId`, `cwd`, sandbox, approval policy, profile and approval prompt correlation.
6. Command rules: verify `pattern`, `decision`, `justification`, `match`, `not_match` and compound-shell behavior.
7. App Server API: classify methods before automation exposure. `thread/shellCommand` and `process/spawn` are open-world because they do not inherit the thread sandbox.
8. Context memory: anchor the newest goal, invalidate stale plans, isolate bad facts, split multi-issue summaries and keep raw evidence fallback.
9. Docs MCP: use OpenAI Docs MCP first for OpenAI product/API questions across supported MCP-capable clients; fallback only to official OpenAI domains.
10. Plugin marketplace: verify `.adk-plugin/plugin.json`, skill path, source path containment, install policy and auth policy.
11. Developer-mode tools: inspect JSON payloads for write actions, keep remembered approvals conversation-local, and do not treat read-only hints as proof of harmlessness.
12. Macro eval: collect many trace summaries, score local failures, cluster recurring patterns, identify suspect agents/tools/handoffs, then promote only the clearest failures into deterministic suites.
13. Structured outputs: require schema target, strict mode, required fields, additional-property policy, refusal handling and drift controls.
14. Tool search: record namespace summary, deferred surface, maximum initial items, loaded-tool evidence and schema review.
15. Automations: require disabled default, report-only mode, durable prompt, bounded cadence/data source, first-run review and cleanup policy.
16. Worktrees: record creation gate, handoff gate, branch limitation and cleanup gate before background work is treated as isolated.
17. Improvement loop: require trace-feedback-eval-validation-ADK handoff linkage and human approval before apply.
18. CI/PR review: record trusted event, actor trust, repository visibility, protected secret exposure decision, schema validation result and SCM write payload review.
19. Inline review anchoring: test new, modified, renamed, deleted and multi-line findings; skip inline publication when anchoring is uncertain.
20. Skill reproducibility: record version pin, model/runtime assumption, deterministic stdout contract, output path and rollback path before production promotion.
21. Codex runtime config: reject project-local attempts to set provider/auth/profile/notification/base URL/telemetry keys; keep those at user, machine or admin scope.
22. Permission profile: compare declared filesystem and network boundary against the intended task; `danger-full-access` cannot be inherited or treated as a safe base profile.
23. Memory runtime: require opt-in, source classification, external-context owner review, raw-evidence fallback and redaction decision before memory candidates can be promoted.
24. Surface terminology: compare new ADK terms against Codex glossary mapping to prevent agent/skill/plugin/automation/worktree/MCP server drift.
25. Runtime capability gate: run `scripts/check-openai-runtime-capabilities.sh` before promoting permission profiles, MCP servers, subagent batch jobs or terminology changes.
26. Runtime pilot fixtures: validate positive and negative examples under `fixtures/openai-runtime-capabilities/` before treating manifest gates as behaviorally covered.

## Verification

```bash
scripts/check-openai-developers-governance.sh
scripts/check-openai-runtime-capabilities.sh
scripts/check-openai-runtime-capabilities.sh --fixture fixtures/openai-runtime-capabilities/pass/permission-safe-profile.json
scripts/devkit.sh validate --strict
tests/test_openai_developers_governance.sh
tests/test_openai_runtime_capabilities.sh
```
