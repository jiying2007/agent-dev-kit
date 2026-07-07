# OpenAI Developers Reference Adoption

## Purpose

This note records the official OpenAI Developers content that is safe to use as an `agent-dev-kit` reference source. It is not an instruction to rewrite adk around the Agents SDK. The current strategy is to absorb stable governance patterns into existing adk assets, keep OpenAI-specific implementation details behind freshness gates, and require local validation before promotion. Product names that remain in source IDs, titles or URLs are citation metadata only; promoted ADK contracts must stay platform-neutral and must not carry compatibility bindings.

## Source Inventory

| ID | Source | Retrieved | Expires | Scope | Decision |
|---|---|---:|---:|---|---|
| openai-codex-customization-skills | https://developers.openai.com/codex/concepts/customization#skills | 2026-05-25 | 2026-08-23 | P0 | Adopt for AGENTS, skill, plugin, MCP and subagent layering. |
| openai-agents-sdk-starting-point | https://developers.openai.com/api/docs/guides/agents#choose-your-starting-point | 2026-05-25 | 2026-08-23 | P2 | Adopt as a taxonomy reference, not as a rewrite mandate. |
| openai-agents-tracing | https://developers.openai.com/api/docs/guides/agents/integrations-observability#tracing | 2026-05-25 | 2026-08-23 | P1 | Adopt trace summaries as workflow evidence and eval inputs. |
| openai-agent-evals | https://developers.openai.com/api/docs/guides/agent-evals | 2026-05-25 | 2026-08-23 | P1 | Adopt datasets, graders and eval runs for routing/governance/completion checks. |
| openai-reasoning-models | https://developers.openai.com/api/docs/guides/latest-model#using-reasoning-models | 2026-05-25 | 2026-08-23 | P0 | Adopt context compaction, structured output and tool-description guidance. |
| openai-apps-sdk-review-tool-hints | https://developers.openai.com/apps-sdk/deploy/submission#app-review--approval-faqs | 2026-05-25 | 2026-08-23 | P1 | Adopt read-only/destructive/open-world and PII audit hints for tool governance. |
| openai-codex-config-reference | https://developers.openai.com/codex/config-reference#configtoml | 2026-05-25 | 2026-08-23 | P0 | Adopt runtime config boundaries, project config non-overrides, agent limits and MCP tool approval fields. |
| openai-codex-requirements-toml | https://developers.openai.com/codex/config-reference#requirementstoml | 2026-05-25 | 2026-08-23 | P0 | Adopt admin-enforced policy, managed hooks, MCP identity allowlists, deny_read and restrictive command rules. |
| openai-codex-sandbox-defaults | https://developers.openai.com/codex/concepts/sandboxing#configure-defaults | 2026-05-25 | 2026-08-23 | P0 | Adopt safe sandbox presets and full-access denial gates. |
| openai-codex-rules | https://developers.openai.com/codex/rules#create-a-rules-file | 2026-05-25 | 2026-08-23 | P0 | Adopt prefix_rule fields, inline match/not_match unit tests and restrictive admin command rules. |
| openai-codex-agent-approvals-security-dangerous-settings | https://developers.openai.com/codex/agent-approvals-security#dangerous-settings | 2026-05-25 | 2026-08-23 | P0 | Adopt hard gates for network proxy, Unix sockets, live web search and prompt-injection exposure. |
| openai-codex-mcp-options | https://developers.openai.com/codex/mcp#other-configuration-options | 2026-05-25 | 2026-08-23 | P1 | Adopt MCP timeout, required, enabled/disabled tools, per-tool approval, OAuth callback and scopes audit fields. |
| openai-codex-app-server-api-overview | https://developers.openai.com/codex/app-server#api-overview | 2026-05-25 | 2026-08-23 | P1 | Adopt App Server runtime API read/write/destructive/open-world classification. |
| openai-context-engineering-session-memory | https://developers.openai.com/cookbook/examples/agents_sdk/session_memory#why-context-management-matters | 2026-05-25 | 2026-08-23 | P1 | Adopt latest-goal anchoring, stale-plan invalidation, per-issue summaries and error isolation for handoff context. |
| openai-docs-mcp-quickstart | https://developers.openai.com/learn/docs-mcp#quickstart | 2026-05-25 | 2026-08-23 | P0 | Adopt cross-tool Docs MCP setup strategy for supported MCP-capable clients. |
| openai-responses-migration | https://developers.openai.com/api/docs/guides/migrate-to-responses | 2026-05-25 | 2026-08-23 | P2 | Watch as a future API-backed runner reference; no adk rewrite without local pilot. |
| openai-codex-hooks | https://developers.openai.com/codex/hooks | 2026-05-25 | 2026-08-23 | P1 | Adopt lifecycle hook audit, trust, matcher and side-effect classification. |
| openai-codex-hooks-common-output-fields | https://developers.openai.com/codex/hooks#common-output-fields | 2026-05-25 | 2026-08-23 | P1 | Adopt event-specific hook output field validation. |
| openai-codex-slash-commands | https://developers.openai.com/codex/cli/slash-commands#built-in-slash-commands | 2026-05-25 | 2026-08-23 | P1 | Adopt slash command control-plane classification and runtime evidence capture. |
| openai-codex-as-mcp-server | https://developers.openai.com/codex/guides/agents-sdk#running-codex-as-an-mcp-server | 2026-05-25 | 2026-08-23 | P1 | Adopt generic ADK runner/reply contracts and thread continuation audit. |
| openai-codex-plugin-build | https://developers.openai.com/codex/plugins/build#create-a-plugin-manually | 2026-05-25 | 2026-08-23 | P2 | Adopt optional adk plugin packaging contracts after assets are stable. |
| openai-codex-plugin-marketplace | https://developers.openai.com/codex/plugins/build#marketplace-metadata | 2026-05-25 | 2026-08-23 | P2 | Adopt marketplace metadata, install policy, auth policy and source path containment. |
| openai-codex-best-practices | https://developers.openai.com/codex/learn/best-practices | 2026-05-25 | 2026-08-23 | P0 | Adopt task framing, planning, AGENTS.md, test/review, MCP, skills, automations and session controls. |
| openai-codex-agent-skills | https://developers.openai.com/codex/skills | 2026-05-25 | 2026-08-23 | P0 | Adopt progressive disclosure, trigger descriptions, storage scopes and plugin distribution boundaries. |
| openai-tools-guide | https://developers.openai.com/api/docs/guides/tools | 2026-05-25 | 2026-08-23 | P1 | Adopt tool semantics, Agents SDK tool placement and deferred tool-definition guidance. |
| openai-chatgpt-developer-mode | https://developers.openai.com/api/docs/guides/developer-mode#how-to-use | 2026-05-25 | 2026-08-23 | P1 | Adopt tool disambiguation, input-shape sequencing, JSON payload review and write-action confirmation. |
| openai-mcp-chatgpt-api-integrations | https://developers.openai.com/api/docs/mcp | 2026-05-25 | 2026-08-23 | P1 | Adopt data-only MCP search/fetch compatibility, structuredContent, auth and prompt-injection risk review. |
| openai-agentic-macro-evals | https://developers.openai.com/cookbook/examples/partners/macro_evals_for_agentic_systems/macro_evals_for_agentic_systems | 2026-05-25 | 2026-08-23 | P1 | Adopt recurring behavior-pattern analysis and failure promotion into regression suites. |
| openai-structured-model-outputs | https://developers.openai.com/api/docs/guides/structured-outputs | 2026-05-26 | 2026-08-24 | P1 | Adopt schema-backed task packages, handoffs, evidence reports, trace summaries and refusal handling. |
| openai-function-calling-strict | https://developers.openai.com/api/docs/guides/function-calling | 2026-05-26 | 2026-08-24 | P1 | Adopt strict tool schemas, namespace grouping, call-output correlation and function/tool boundary reviews. |
| openai-tool-search | https://developers.openai.com/api/docs/guides/tools-tool-search | 2026-05-26 | 2026-08-24 | P1 | Adopt lazy loading for skill/tool catalogs, namespace summaries and token-budget-aware progressive disclosure. |
| openai-file-search-retrieval | https://developers.openai.com/api/docs/guides/tools-file-search | 2026-05-26 | 2026-08-24 | P2 | Watch as a local archive/retrieval design reference; hosted file_search is not enabled by default. |
| openai-codex-app-automations | https://developers.openai.com/codex/app/automations | 2026-05-26 | 2026-08-24 | P1 | Adopt report-only automation records, durable prompts, cadence, stop conditions, sandbox policy and review gates. |
| openai-codex-app-worktrees | https://developers.openai.com/codex/app/worktrees | 2026-05-26 | 2026-08-24 | P1 | Adopt background worktree isolation, handoff gates, branch limitations and cleanup policy. |
| openai-agent-improvement-loop | https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop | 2026-05-26 | 2026-08-24 | P1 | Adopt trace-feedback-eval-ADK-handoff improvement loops with human approval before deeper automation. |
| openai-codex-github-action | https://developers.openai.com/codex/github-action | 2026-05-26 | 2026-08-24 | P1 | Adopt controlled CI/PR review runner contracts, protected secret handling, sandbox defaults and prompt-injection checks. |
| openai-codex-code-review-sdk | https://developers.openai.com/cookbook/examples/codex/build_code_review_with_codex_sdk | 2026-05-26 | 2026-08-24 | P1 | Adopt PR diff inputs, structured review findings, SCM review publishing and inline anchoring validation. |
| openai-skills-api-operational-practices | https://developers.openai.com/cookbook/examples/skills_in_api#operational-best-practices | 2026-05-26 | 2026-08-24 | P1 | Adopt skill discoverability, negative examples, version pinning, deterministic stdout and network allowlist governance. |
| openai-optimizing-llm-accuracy | https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy | 2026-05-26 | 2026-08-24 | P2 | Watch for prompt/RAG/fine-tuning optimization decisions; require eval baseline before promotion. |
| openai-codex-agents-sdk-multi-agent-workflows | https://developers.openai.com/codex/guides/agents-sdk#creating-multi-agent-workflows | 2026-05-26 | 2026-08-24 | P2 | Watch as a future multi-agent orchestration reference; do not replace existing adk-first governance without a pilot. |
| openai-latest-model-gpt-5-5 | https://developers.openai.com/api/docs/models | 2026-06-27 | 2026-07-27 | P2 | Watch as a volatile model-selection source; do not hardcode current-model claims into durable ADK rules. |
| openai-prompt-caching | https://developers.openai.com/api/docs/guides/prompt-caching | 2026-05-27 | 2026-08-25 | P1 | Adopt stable-prefix and dynamic-tail prompt layout, cache-key discipline and cached-token observability for API-backed runners. |
| openai-agents-orchestration-handoffs | https://developers.openai.com/api/docs/guides/agents/orchestration | 2026-05-27 | 2026-08-25 | P1 | Adopt handoff vs agents-as-tools ownership vocabulary for ADK orchestration contracts. |
| openai-graders | https://developers.openai.com/api/docs/guides/graders | 2026-05-27 | 2026-08-25 | P1 | Adopt grader taxonomy for deterministic routing, governance, completion and macro-eval gates. |
| openai-prompt-optimization-golden-examples | https://developers.openai.com/cookbook/examples/optimize_prompts#4-using-evaluations-to-arrive-at-these-agents | 2026-05-27 | 2026-08-25 | P1 | Adopt positive and negative golden examples before changing prompts, AGENTS.md routing text or skill descriptions. |
| openai-codex-iterative-repair-loop | https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex | 2026-05-27 | 2026-08-25 | P1 | Adopt Review -> Repair -> Validate as a closed-loop repair and completion-evidence contract. |
| openai-model-optimization-workflow | https://developers.openai.com/api/docs/guides/model-optimization#model-optimization-workflow | 2026-05-27 | 2026-08-25 | P0 | Adopt eval-baseline-first optimization for prompt, model, context and tool changes. |
| openai-prompt-engineering-roles | https://developers.openai.com/api/docs/guides/prompt-engineering#message-roles-and-instruction-following | 2026-05-27 | 2026-08-25 | P0 | Adopt developer/user/context/tool-output authority boundaries. |
| openai-prompt-engineering-formatting | https://developers.openai.com/api/docs/guides/prompt-engineering#message-formatting-with-markdown-and-xml | 2026-05-27 | 2026-08-25 | P0 | Adopt stable prompt sections and explicit context boundaries. |
| openai-stored-completion-monitoring | https://developers.openai.com/cookbook/examples/evaluation/use-cases/completion-monitoring | 2026-05-27 | 2026-08-25 | P1 | Watch as a sanitized session-derived regression monitoring pattern; disabled by default. |
| openai-agentic-governance-test-dataset | https://developers.openai.com/cookbook/examples/partners/agentic_governance_guide/agentic_governance_cookbook#step-2-create-a-test-dataset | 2026-05-27 | 2026-08-25 | P1 | Adopt guardrail datasets with positive, negative, adversarial and borderline cases. |
| openai-eval-driven-system-design | https://developers.openai.com/cookbook/examples/partners/eval_driven_system_design/receipt_inspection#further-improvements | 2026-05-27 | 2026-08-25 | P1 | Adopt improvement ladder and eval/training data separation. |
| openai-model-selection-guide | https://developers.openai.com/cookbook/examples/partners/model_selection_guide/model_selection_guide | 2026-05-27 | 2026-08-25 | P1 | Adopt model-selection decision records with KPI/SLO, cost, latency, A/B and rollback fields. |
| openai-ai-native-engineering-team-docs | https://developers.openai.com/codex/guides/build-ai-native-engineering-team#how-coding-agents-help-5 | 2026-05-27 | 2026-08-25 | P1 | Adopt documentation freshness, diagrams and release summaries as delivery-pipeline artifacts. |
| openai-data-controls-responses | https://developers.openai.com/api/docs/guides/your-data#v1responses | 2026-05-28 | 2026-08-26 | P0 | Adopt Data retention and ZDR fields for API-backed runner, MCP and hosted-tool pilots. |
| openai-responses-migration-statefulness | https://developers.openai.com/api/docs/guides/migrate-to-responses#4-decide-when-to-use-statefulness | 2026-05-28 | 2026-08-26 | P1 | Adopt Responses statefulness choices, encrypted reasoning and call_id correlation as pilot-only contracts. |
| openai-prompt-cache-retention | https://developers.openai.com/api/docs/guides/prompt-caching#prompt-cache-retention | 2026-05-28 | 2026-08-26 | P1 | Adopt Prompt cache retention policy, model-support freshness and cache-miss-safe layout gates. |
| openai-codex-glossary | https://developers.openai.com/codex/glossary | 2026-06-15 | 2026-09-13 | P1 | Adopt Codex glossary mapping for ADK runtime-surface terminology and drift checks. |
| openai-codex-permissions | https://developers.openai.com/codex/permissions | 2026-06-15 | 2026-09-13 | P0 | Adopt permission profile, granular approval and least-privilege runtime boundary checks. |
| openai-codex-memories | https://developers.openai.com/codex/memories | 2026-06-15 | 2026-09-13 | P1 | Adopt opt-in memory runtime, external-context review and raw-evidence fallback policy. |
| openai-codex-subagents-runtime | https://developers.openai.com/codex/subagents | 2026-06-15 | 2026-09-13 | P1 | Adopt subagent runtime limits, nesting policy and delegated-work evidence fields. |
| openai-codex-record-and-replay | https://developers.openai.com/codex/record-and-replay | 2026-07-07 | 2026-10-05 | P1 | Adopt replayable run evidence bundles and workflow-to-skill promotion boundaries. |
| openai-codex-appshots | https://developers.openai.com/codex/appshots | 2026-07-07 | 2026-10-05 | P1 | Adopt frontmost-window UI evidence capture, visible text boundaries and permission/sensitive-content review fields. |
| openai-codex-noninteractive | https://developers.openai.com/codex/noninteractive | 2026-07-07 | 2026-10-05 | P1 | Adopt runner smoke evidence for JSONL/schema output, sandbox/approval records and resume/reply correlation. |

## 2026-07-07 Delta Landing

- Record & Replay is landed as a replayable evidence-bundle contract, not as Computer Use enablement. Promoted workflows must separate variable inputs from fixed steps, define observable assertions, hash artifacts and record sensitive-data review before they become reusable skills or automations.
- Goal and completion guidance now has explicit negative fixtures. Goals without done-when criteria, required evidence, artifact paths or blocker policy are `needs-fix`, and completion claims without changed files, evidence paths, negative cases or risks are rejected before promotion.
- Automation and worktree governance now includes risk fixtures for missing stop conditions, unattended full-access, dirty worktree launches without a decision and stale heartbeats without stop/replan handling.
- UI evidence now absorbs Appshots boundaries: appshot-derived evidence is limited to the frontmost window and visible or app-exposed text needed for the task, with screen/accessibility permission scope and sensitive-content review recorded.
- Subagent governance now has a context noise budget. Workers return distilled summaries and evidence refs; raw command transcripts or logs are artifact-linked only after an explicit retention and redaction decision.
- Runner governance now has a smoke contract for programmatic adapters. Machine-consumed output must be JSONL or strict-schema backed, and every run records sandbox, approval policy, cwd, thread correlation and failure/cancel path.

## 2026-07-05 Delta Landing

- Tighten subagent context hygiene. Delegated workers must return a distilled `summary`, `evidence_refs` and `raw_output_policy`; raw logs, command transcripts, stack traces and exploratory notes stay out of the parent thread unless explicitly retained as evidence artifacts.
- Treat automation promotion as a staged reliability decision. A recurring workflow must prove usefulness through manual execution, then report-only execution, then owner-reviewed promotion with rollback or disable evidence before it can be enabled or allowed to write externally.
- Keep OpenAI official practice as a governance input, not a parallel runtime. The landing target remains existing ADK manifests and deterministic checks, especially `subagent_contracts.json`, `automation_worktree_contracts.json`, `check-runtime-capabilities.sh` and `check-official-docs-governance.sh`.

## 2026-06-15 Delta Landing

- Refresh Codex config reference into a project-local non-overridable key list. Repo-level settings must not take over provider, auth, base URL, profile, notification, realtime or telemetry routing.
- Treat permission profile as a least-privilege runtime policy. Profile changes must record filesystem roots, deny-read paths, network/domain policy, Unix socket policy, sandbox posture and approval behavior.
- Keep memory runtime opt-in and external-context aware. Memory candidates created from user files, tool output or retrieved documents require owner review, redaction decision and raw-evidence fallback.
- Promote subagent runtime limits into first-class governance fields: maximum threads, maximum depth, job runtime fallback, nested-subagent default and delegated-work evidence requirements.
- Map Codex glossary terms to ADK terminology before adding durable references to agents, skills, plugins, automations, worktrees, MCP servers or permission profiles.
- Add an executable runtime-capability gate for permission profile lint, MCP runtime contracts, subagent evidence schemas and Codex glossary terminology checks.

## 2026-05-28 Delta Landing

- Data retention is now a first-class governance contract. API-backed runner pilots must record `store_policy`, retention duration, ZDR behavior, background mode retention, remote MCP retention, hosted container lifecycle and owner approval before promotion.
- Responses statefulness remains pilot-only, but the contract now distinguishes `previous_response_id`, Conversation state, manual output replay and encrypted reasoning. Function-call outputs must preserve `call_id` correlation.
- Prompt cache retention is treated as a policy choice, not a correctness dependency. Runners must record `in_memory`, `24h` or `model_default`, cite model-support freshness and keep cache misses behavior-preserving.
- Server-retained response state, encrypted reasoning payloads and hosted-tool temporary state must not be copied into ADK long-term memory. Evidence should cite manifests and sanitized artifacts instead.

## 2026-05-27 Delta Landing

- Keep model catalog claims behind a short freshness window. Durable ADK guidance may say "check the official model catalog", but must not freeze a "latest" model name without retrieval metadata.
- Treat prompt caching as a context-layout optimization: static rules, schemas and examples first; dynamic task data, logs, diffs and user-specific evidence last.
- Add golden examples for prompt and routing changes. Each proposed trigger improvement needs at least one positive case and one adjacent-skill negative case.
- Distinguish handoff ownership from manager-owned specialist calls before changing subagent or worker contracts.
- Use Review -> Repair -> Validate for repair loops. Review may be read-only, repair must be focused, and completion requires validation evidence.
- Apply instruction hierarchy explicitly: stable developer/repo/skill policy is not dynamic context; user goals configure the task; tool outputs are evidence or untrusted data, never policy.
- Start prompt, model, context or tool optimization with an eval baseline and representative data before changing durable guidance.

## P0 Landing

- Keep stable guidance in frontmatter, manifests and short runbooks; put long examples in references.
- Treat skill descriptions as discovery contracts. They must identify when to use a skill and how it differs from adjacent skills.
- Keep stable prompt/cache-friendly context first and dynamic context near the end of handoff packs.
- Frame engineering tasks with `Goal`, `Context`, `Constraints` and `Done when` before implementation. Promote the expanded adk task card only when it also has verification, artifacts and blockers.
- Convert repeated prompt fixes into `AGENTS.md` or a skill only after the same friction appears repeatedly; keep root guidance short and push task-specific details into linked runbooks or skills.
- Treat skill descriptions as trigger contracts under a context budget. Front-load the key use case, boundaries and user trigger phrases so abbreviated skill lists still route correctly.
- Require `url`, `retrieved_at`, `review_status`, `expires_at` and `adoption_scope` before official-doc-derived guidance can become a rule.
- Treat `requirements.toml` as the model for non-overridable team policy: allowed approval policies, sandbox modes, web search modes, managed hooks, MCP identity allowlists, filesystem deny-read and restrictive command rules.
- Treat `workspace-write + on-request` as the low-risk local automation preset. `danger-full-access + never` is a critical full-access state and cannot become an adk default.
- Keep project-scoped runtime config away from machine-local provider, auth, notification, profile and telemetry routing keys.
- Require command `prefix_rule` records to include `pattern`, `decision`, `justification`, and inline `match` / `not_match` examples before promotion.
- Keep network proxy dangerous settings, broad Unix socket access and live web search out of defaults. Live web content remains untrusted even when the source is useful.
- Standardize OpenAI Docs MCP lookup across supported MCP-capable clients: MCP first, official OpenAI-domain fallback only, citations required for API/product claims.
- Keep current-model recommendations short-lived and freshness-gated. Prefer "verify current model catalog" over embedding a model alias in stable ADK instructions.
- Require Data retention evidence for any API-backed pilot that stores response state, polls background responses, uses remote MCP, or relies on hosted containers or hosted skills.
- Check project-local runtime config against the official non-overridable key list before promoting repo-level Codex settings.
- Treat permission profiles as least-privilege runtime policies. `:danger-full-access` cannot be inherited or used as a safe base profile.
- Keep memory runtime disabled by default. Memory generated from external context needs owner approval, redaction decision and raw evidence fallback.

## P1 Landing

- Use trace summaries to record `run_id`, goal, phase, model calls, tool calls, handoffs, guardrails, verification, blockers and next goal.
- Maintain three eval suite categories: routing, governance and completion.
- Audit MCP/tool surfaces with `readOnlyHint`, `destructiveHint`, `openWorldHint`, auth boundary, PII policy, dry-run requirement and fallback.
- Require action-oriented tool names and descriptions with "Use this when" guidance, disallowed cases, parameter descriptions and enum constraints before any tool enters a profile.
- For data-only MCP servers, prefer the `search` / `fetch` compatibility shape, declare `structuredContent`, include citation-capable URLs and keep raw document text out of long-term memory unless explicitly archived.
- Review JSON tool payloads before write actions. Tool approval remembers are conversation-local decisions, not durable adk permission grants.
- Aggregate trace summaries by model version, prompt version, orchestration mode and primary skill. Promote frequent, consequential failures into deterministic regression suites.
- Use structured outputs for machine-consumed task packages, evidence indexes and handoff summaries. Valid JSON is not enough; schema adherence, refusal detection and parse-failure handling must be explicit.
- Treat strict tool schemas as the default for future tool/MCP contracts: required fields, `additionalProperties=false`, enum constraints and clear output correlation.
- Use tool-search style lazy loading for large skill/tool catalogs: route on short namespace summaries first, then load full `SKILL.md`, references or tool schemas only after the intent match is justified.
- Automation records must be report-only by default, disabled until reviewed, bounded by data source/cadence/stop condition, and tested manually before scheduling.
- Worktree-backed background work must record base branch/commit, dirty-state decision, worktree path, handoff plan and cleanup/retention decision.
- Improvement loops must connect trace summaries, human/model feedback, eval candidates, validation results, ranked recommendations and an ADK handoff artifact before changing guidance.
- CI/PR review runners must be disabled by default, treat PR text as untrusted, protect secrets from fork code, require structured findings before SCM publishing and never treat AI review as human approval.
- Inline review comments require validated diff anchoring. If new, renamed, deleted or multi-line locations cannot be mapped safely, keep the finding in the summary instead of posting a misleading inline comment.
- Skill version and model/runtime assumptions must be pinned for production workflows; treat `skill version` as a reproducibility field. Scripted skills need deterministic stdout, known output paths, loud failures and explicit network allowlists when network is needed.
- Audit MCP runtime options: `startup_timeout_sec`, `tool_timeout_sec`, `required`, `enabled_tools`, `disabled_tools`, default and per-tool approval modes, OAuth callback settings and scopes.
- Keep external writes in report-only mode until dry-run, approval and rollback evidence exist.
- Audit hooks by event. Do not rely on unsupported hook output fields, especially `continue` from `PreToolUse` or matchers on `Stop`.
- Classify slash commands as read-only, permission-changing, context-changing or runtime-changing before using them as evidence or control-plane operations.
- If an agent runtime is exposed through MCP, record `threadId`, `cwd`, sandbox, approval policy, profile, runtime adapter, approval prompts and result summary.
- Classify runtime API methods before exposing them in automation: lifecycle reads, state writes, destructive thread state, sandboxed command exec, open-world process/shell, filesystem/config/plugin writes and MCP/app tool bridge.
- Context summaries must anchor the latest goal, invalidate stale goals, isolate failed assumptions, split multi-issue handoffs and preserve raw evidence fallback.
- Prompt and skill-routing changes require golden-case eval coverage, including adjacent-skill negative cases.
- Repair workflows must keep review, focused edit and validation evidence distinct in artifacts.
- Orchestration contracts must state whether a specialist takes ownership or only acts as a bounded helper under a manager.
- Guardrail changes need positive, negative, adversarial and borderline regression examples before promotion.
- Stored-session or stored-completion monitoring remains disabled by default until retention, redaction and owner approval are recorded.
- Model selection changes require a decision record with measurable KPI/SLO, cost, latency, version pinning, A/B plan and rollback.
- Prompt cache retention must be explicit for cache-sensitive model decisions. Cached-token metrics are observability signals only; they do not prove correctness.
- Responses state handoff must document retention mode, encrypted reasoning policy, `store=false` behavior, conversation-state policy and `call_id` correlation before any API-backed runner promotion.
- Documentation freshness is part of delivery evidence; release summaries and codebase diagrams should be generated or refreshed through the delivery pipeline when relevant.
- Align runtime-surface terminology with the Codex glossary before new manifests, skills or runbooks mention agents, plugins, automations, worktrees, MCP servers or permission profiles.
- Record subagent runtime limits and nested-subagent policy before delegated agents are used for multi-stage work.
- Subagent reports must be summary-first and evidence-linked. Do not merge raw worker output into the parent context unless a retention decision, redaction boundary and artifact reference are explicit.
- Automation promotion must move through manual proof, report-only history and owner approval before scheduling or enabling writes.
- Replayable workflow evidence must include input snapshots, environment snapshots, artifact hashes, expected assertions, sensitive-data review and manual replay notes before any skill or automation promotion.
- UI/App evidence can cite appshots only within the frontmost-window and visible/app-exposed-text boundary; Computer Use, browser runtime and desktop control remain disabled unless separately approved.
- Programmatic runner adapters need a smoke record with JSONL or strict-schema output, sandbox/approval policy, cwd, thread correlation and observable failure/cancel handling.

## P2 Landing

- Use Agents SDK docs as a vocabulary reference for agent definitions, running state, sandbox, handoffs, guardrails, tools and observability.
- Do not replace existing adk lifecycle assets unless a local pilot proves lower complexity and better verification.
- Any future SDK-backed implementation must first pass supply-chain review, permission review, local regression and rollback planning.
- Package adk assets as ADK plugins only after the underlying skills/workflows are stable. Plugin promotion requires `.adk-plugin/plugin.json`, `skills/<skill-name>/SKILL.md`, version/publisher metadata, install policy, auth policy and marketplace source path containment.
- Treat Responses API migration as watch/pilot only for now. Future API-backed runners must prove statefulness, `previous_response_id`, phase preservation, structured outputs and retention policy in evals before promotion.
- Treat hosted file search and external vector stores as watch-only until a local archive/retrieval pilot proves metadata filtering, citation handling, freshness and sensitive-data boundaries.

## Non-Goals

- Do not copy OpenAI cookbook examples into core adk assets.
- Do not enable hosted tools, external MCP servers or runtime connectors just because they appear in docs.
- Do not treat an official example as production approval. Local owner, scope, denial path and verification remain mandatory.
- Do not use hooks as a substitute for sandbox or approval policy.
- Do not publish personal marketplace entries as adk defaults without source, auth and install-surface review.
- Do not enable CI review publishing on public or fork PRs without explicit trusted-trigger, secret-isolation and write-permission evidence.
- Do not post SCM review comments from free-form prose or unvalidated line references.
- Do not promote unversioned or nondeterministic skills into production defaults.

## Verification

```bash
scripts/check-official-docs-governance.sh
scripts/check-runtime-capabilities.sh
scripts/validate-assets.sh --strict
tests/test_official_docs_governance.sh
tests/test_runtime_capabilities.sh
```

## Manifest Map

| Manifest | Purpose |
|---|---|
| `manifests/official_docs_freshness_gates.json` | Official URL inventory, retrieval dates, review status, expiry and adoption scope. |
| `manifests/adk_runtime_policy_gates.json` | Runtime config, managed requirements, sandbox presets and forbidden defaults. |
| `manifests/adk_rules_contracts.json` | ADK command prefix-rule fields, inline examples and promotion gates. |
| `manifests/adk_runtime_api_contracts.json` | ADK runtime API method groups classified by read/write/destructive/open-world and sandbox inheritance. |
| `manifests/context_state_contracts.json` | Long-thread session summaries, stale-goal invalidation, evidence fallback and future Responses state handoff contracts. |
| `manifests/official_docs_mcp_tooling.json` | OpenAI Docs MCP setup and fallback policy across supported MCP-capable clients. |
| `manifests/hooks_runtime_audits.json` | Hook event support, output-field support, trust, side-effect and log-redaction policy. |
| `manifests/slash_command_runtime_audits.json` | Slash command read/write/open-world/destructive classification. |
| `manifests/adk_runner_contracts.json` | ADK `run-session` and `reply-session` runner contracts. |
| `manifests/plugin_marketplace_contracts.json` | ADK plugin and marketplace packaging contracts. |
| `manifests/structured_output_contracts.json` | Schema-backed task package, evidence index and handoff summary contracts. |
| `manifests/tool_search_contracts.json` | Skill/tool namespace lazy-loading and deferred schema exposure contracts. |
| `manifests/pr_review_governance_contracts.json` | CI/PR review runner, untrusted PR isolation and inline comment anchoring contracts. |
| `manifests/skill_reproducibility_contracts.json` | Skill discoverability, version pinning and tiny-CLI reproducibility contracts. |
| `manifests/automation_worktree_contracts.json` | Report-only automation, thread heartbeat and worktree handoff/cleanup contracts. |
| `manifests/agent_improvement_loop_contracts.json` | Trace-feedback-eval-validation-ADK handoff improvement loop contracts. |
| `manifests/external_agent_pattern_contracts.json` | Method-only UI/browser/Appshots evidence and third-party pattern boundary contracts. |
| `manifests/model_selection_decision_records.json` | Model selection KPI/SLO, cost, latency, version pinning, A/B and rollback decision records. |
| `manifests/data_retention_state_contracts.json` | Data retention, ZDR, background mode, remote MCP, hosted container and prompt-cache state boundary contracts. |
| `manifests/prompt_cache_policy_contracts.json` | Prompt cache retention policy, stable/dynamic context boundary and cache-miss behavior contracts. |
| `manifests/codex_surface_terms.json` | Codex glossary to ADK terminology mapping for runtime-surface drift control. |
