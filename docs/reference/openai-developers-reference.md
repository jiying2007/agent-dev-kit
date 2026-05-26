# OpenAI Developers Reference Adoption

## Purpose

This note records the official OpenAI Developers content that is safe to use as an `agent-dev-kit` reference source. It is not an instruction to rewrite adk around the Agents SDK. The current strategy is to absorb stable governance patterns into existing adk assets, keep OpenAI-specific implementation details behind freshness gates, and require local validation before promotion.

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
| openai-docs-mcp-quickstart | https://developers.openai.com/learn/docs-mcp#quickstart | 2026-05-25 | 2026-08-23 | P0 | Adopt cross-tool Docs MCP setup strategy for Codex, VS Code, Cursor and Claude Code. |
| openai-responses-migration | https://developers.openai.com/api/docs/guides/migrate-to-responses | 2026-05-25 | 2026-08-23 | P2 | Watch as a future API-backed runner reference; no adk rewrite without local pilot. |
| openai-codex-hooks | https://developers.openai.com/codex/hooks | 2026-05-25 | 2026-08-23 | P1 | Adopt lifecycle hook audit, trust, matcher and side-effect classification. |
| openai-codex-hooks-common-output-fields | https://developers.openai.com/codex/hooks#common-output-fields | 2026-05-25 | 2026-08-23 | P1 | Adopt event-specific hook output field validation. |
| openai-codex-slash-commands | https://developers.openai.com/codex/cli/slash-commands#built-in-slash-commands | 2026-05-25 | 2026-08-23 | P1 | Adopt slash command control-plane classification and runtime evidence capture. |
| openai-codex-as-mcp-server | https://developers.openai.com/codex/guides/agents-sdk#running-codex-as-an-mcp-server | 2026-05-25 | 2026-08-23 | P1 | Adopt Codex MCP runner/reply contracts and thread continuation audit. |
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
| openai-agent-improvement-loop | https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop | 2026-05-26 | 2026-08-24 | P1 | Adopt trace-feedback-eval-Codex-handoff improvement loops with human approval before deeper automation. |
| openai-codex-github-action | https://developers.openai.com/codex/github-action | 2026-05-26 | 2026-08-24 | P1 | Adopt controlled CI/PR review runner contracts, protected secret handling, sandbox defaults and prompt-injection checks. |
| openai-codex-code-review-sdk | https://developers.openai.com/cookbook/examples/codex/build_code_review_with_codex_sdk | 2026-05-26 | 2026-08-24 | P1 | Adopt PR diff inputs, structured review findings, SCM review publishing and inline anchoring validation. |
| openai-skills-api-operational-practices | https://developers.openai.com/cookbook/examples/skills_in_api#operational-best-practices | 2026-05-26 | 2026-08-24 | P1 | Adopt skill discoverability, negative examples, version pinning, deterministic stdout and network allowlist governance. |
| openai-optimizing-llm-accuracy | https://developers.openai.com/api/docs/guides/optimizing-llm-accuracy | 2026-05-26 | 2026-08-24 | P2 | Watch for prompt/RAG/fine-tuning optimization decisions; require eval baseline before promotion. |
| openai-codex-agents-sdk-multi-agent-workflows | https://developers.openai.com/codex/guides/agents-sdk#creating-multi-agent-workflows | 2026-05-26 | 2026-08-24 | P2 | Watch as a future multi-agent orchestration reference; do not replace existing adk-first governance without a pilot. |

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
- Keep project-scoped `.codex/config.toml` away from machine-local provider, auth, notification, profile and telemetry routing keys.
- Require command `prefix_rule` records to include `pattern`, `decision`, `justification`, and inline `match` / `not_match` examples before promotion.
- Keep network proxy dangerous settings, broad Unix socket access and live web search out of defaults. Live web content remains untrusted even when the source is useful.
- Standardize OpenAI Docs MCP lookup across Codex, VS Code, Cursor and Claude Code: MCP first, official OpenAI-domain fallback only, citations required for API/product claims.

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
- Improvement loops must connect trace summaries, human/model feedback, eval candidates, validation results, ranked recommendations and a Codex handoff artifact before changing guidance.
- CI/PR review runners must be disabled by default, treat PR text as untrusted, protect secrets from fork code, require structured findings before SCM publishing and never treat AI review as human approval.
- Inline review comments require validated diff anchoring. If new, renamed, deleted or multi-line locations cannot be mapped safely, keep the finding in the summary instead of posting a misleading inline comment.
- Skill version and model/runtime assumptions must be pinned for production workflows; treat `skill version` as a reproducibility field. Scripted skills need deterministic stdout, known output paths, loud failures and explicit network allowlists when network is needed.
- Audit MCP runtime options: `startup_timeout_sec`, `tool_timeout_sec`, `required`, `enabled_tools`, `disabled_tools`, default and per-tool approval modes, OAuth callback settings and scopes.
- Keep external writes in report-only mode until dry-run, approval and rollback evidence exist.
- Audit hooks by event. Do not rely on unsupported hook output fields, especially `continue` from `PreToolUse` or matchers on `Stop`.
- Classify slash commands as read-only, permission-changing, context-changing or runtime-changing before using them as evidence or control-plane operations.
- If Codex is run as an MCP server, record `threadId`, `cwd`, sandbox, approval policy, profile, approval prompts and result summary.
- Classify Codex App Server methods before exposing them in automation: lifecycle reads, state writes, destructive thread state, sandboxed command exec, open-world process/shell, filesystem/config/plugin writes and MCP/app tool bridge.
- Context summaries must anchor the latest goal, invalidate stale goals, isolate failed assumptions, split multi-issue handoffs and preserve raw evidence fallback.

## P2 Landing

- Use Agents SDK docs as a vocabulary reference for agent definitions, running state, sandbox, handoffs, guardrails, tools and observability.
- Do not replace existing adk lifecycle assets unless a local pilot proves lower complexity and better verification.
- Any future SDK-backed implementation must first pass supply-chain review, permission review, local regression and rollback planning.
- Package adk assets as Codex plugins only after the underlying skills/workflows are stable. Plugin promotion requires `.codex-plugin/plugin.json`, `skills/<skill-name>/SKILL.md`, version/publisher metadata, install policy, auth policy and marketplace source path containment.
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
scripts/check-openai-developers-governance.sh
scripts/validate-assets.sh --strict
tests/test_openai_developers_governance.sh
```

## Manifest Map

| Manifest | Purpose |
|---|---|
| `manifests/official_docs_freshness_gates.json` | Official URL inventory, retrieval dates, review status, expiry and adoption scope. |
| `manifests/codex_runtime_policy_gates.json` | Runtime config, admin requirements, sandbox presets and forbidden defaults. |
| `manifests/codex_rules_contracts.json` | Codex `.rules` / `requirements.toml` prefix-rule fields, inline examples and promotion gates. |
| `manifests/codex_runtime_api_contracts.json` | Codex App Server method groups classified by read/write/destructive/open-world and sandbox inheritance. |
| `manifests/context_state_contracts.json` | Long-thread session summaries, stale-goal invalidation, evidence fallback and future Responses state handoff contracts. |
| `manifests/official_docs_mcp_tooling.json` | OpenAI Docs MCP setup and fallback policy across Codex, VS Code, Cursor and Claude Code. |
| `manifests/hooks_runtime_audits.json` | Hook event support, output-field support, trust, side-effect and log-redaction policy. |
| `manifests/slash_command_runtime_audits.json` | Slash command read/write/open-world/destructive classification. |
| `manifests/codex_mcp_runner_contracts.json` | Codex MCP `codex` and `codex-reply` runner contracts. |
| `manifests/plugin_marketplace_contracts.json` | Codex plugin and marketplace packaging contracts. |
| `manifests/structured_output_contracts.json` | Schema-backed task package, evidence index and handoff summary contracts. |
| `manifests/tool_search_contracts.json` | Skill/tool namespace lazy-loading and deferred schema exposure contracts. |
| `manifests/pr_review_governance_contracts.json` | CI/PR review runner, untrusted PR isolation and inline comment anchoring contracts. |
| `manifests/skill_reproducibility_contracts.json` | Skill discoverability, version pinning and tiny-CLI reproducibility contracts. |
| `manifests/automation_worktree_contracts.json` | Report-only automation, thread heartbeat and worktree handoff/cleanup contracts. |
| `manifests/agent_improvement_loop_contracts.json` | Trace-feedback-eval-validation-Codex handoff improvement loop contracts. |
