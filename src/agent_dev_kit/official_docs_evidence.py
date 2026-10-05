"""Official documentation evidence checks; read-only owned audit stage."""
from __future__ import annotations


from .official_docs_context import AuditContext


def check(context: AuditContext) -> None:
    adk_runner = context.bindings["adk_runner"]
    automation_worktree = context.bindings["automation_worktree"]
    codex_surface_terms = context.bindings["codex_surface_terms"]
    context_state = context.bindings["context_state"]
    data_retention = context.bindings["data_retention"]
    docs_mcp_tooling = context.bindings["docs_mcp_tooling"]
    evals = context.bindings["evals"]
    fail = context.bindings["fail"]
    hooks = context.bindings["hooks"]
    improvement_loop = context.bindings["improvement_loop"]
    mcp = context.bindings["mcp"]
    model_selection = context.bindings["model_selection"]
    plugins = context.bindings["plugins"]
    pr_review = context.bindings["pr_review"]
    prompt_cache = context.bindings["prompt_cache"]
    require_keys = context.bindings["require_keys"]
    root = context.bindings["root"]
    rules = context.bindings["rules"]
    runtime_api = context.bindings["runtime_api"]
    runtime_policy = context.bindings["runtime_policy"]
    skill_repro = context.bindings["skill_repro"]
    slash = context.bindings["slash"]
    source_ids = context.bindings["source_ids"]
    structured_outputs = context.bindings["structured_outputs"]
    subagents = context.bindings["subagents"]
    tool_search = context.bindings["tool_search"]
    trace = context.bindings["trace"]
    for required_sid in (
        "openai-codex-best-practices",
        "openai-codex-agent-skills",
        "openai-tools-guide",
        "openai-chatgpt-developer-mode",
        "openai-mcp-chatgpt-api-integrations",
        "openai-agentic-macro-evals",
        "openai-structured-model-outputs",
        "openai-function-calling-strict",
        "openai-tool-search",
        "openai-file-search-retrieval",
        "openai-codex-app-automations",
        "openai-codex-app-worktrees",
        "openai-agent-improvement-loop",
        "openai-codex-github-action",
        "openai-codex-code-review-sdk",
        "openai-skills-api-operational-practices",
        "openai-optimizing-llm-accuracy",
        "openai-codex-agents-sdk-multi-agent-workflows",
        "openai-model-optimization-workflow",
        "openai-prompt-engineering-roles",
        "openai-prompt-engineering-formatting",
        "openai-stored-completion-monitoring",
        "openai-agentic-governance-test-dataset",
        "openai-eval-driven-system-design",
        "openai-model-selection-guide",
        "openai-ai-native-engineering-team-docs",
        "openai-data-controls-responses",
        "openai-responses-migration-statefulness",
        "openai-prompt-cache-retention",
        "openai-codex-glossary",
        "openai-codex-permissions",
        "openai-codex-memories",
        "openai-codex-subagents-runtime",
        "openai-codex-record-and-replay",
        "openai-codex-appshots",
        "openai-codex-noninteractive",
    ):
        if required_sid not in source_ids:
            fail(f"official docs source missing: {required_sid}")

    def require_source_refs(manifest, rel):
        for sid in manifest.get("source_docs", []):
            if sid not in source_ids:
                fail(f"{rel} references unknown official source: {sid}")

    for manifest, rel in (
        (evals, "manifests/eval_suites.json"),
        (trace, "manifests/trace_eval_contracts.json"),
        (mcp, "manifests/skill_mcp_dependencies.json"),
        (slash, "manifests/slash_command_runtime_audits.json"),
        (subagents, "manifests/subagent_contracts.json"),
        (runtime_policy, "manifests/adk_runtime_policy_gates.json"),
        (rules, "manifests/adk_rules_contracts.json"),
        (runtime_api, "manifests/adk_runtime_api_contracts.json"),
        (context_state, "manifests/context_state_contracts.json"),
        (docs_mcp_tooling, "manifests/official_docs_mcp_tooling.json"),
        (hooks, "manifests/hooks_runtime_audits.json"),
        (adk_runner, "manifests/adk_runner_contracts.json"),
        (plugins, "manifests/plugin_marketplace_contracts.json"),
        (structured_outputs, "manifests/structured_output_contracts.json"),
        (tool_search, "manifests/tool_search_contracts.json"),
        (automation_worktree, "manifests/automation_worktree_contracts.json"),
        (improvement_loop, "manifests/agent_improvement_loop_contracts.json"),
        (pr_review, "manifests/pr_review_governance_contracts.json"),
        (skill_repro, "manifests/skill_reproducibility_contracts.json"),
        (model_selection, "manifests/model_selection_decision_records.json"),
        (data_retention, "manifests/data_retention_state_contracts.json"),
        (prompt_cache, "manifests/prompt_cache_policy_contracts.json"),
        (codex_surface_terms, "manifests/codex_surface_terms.json"),
    ):
        require_source_refs(manifest, rel)

    for forbidden_manifest in (
        "manifests/codex_runtime_policy_gates.json",
        "manifests/codex_rules_contracts.json",
        "manifests/codex_runtime_api_contracts.json",
        "manifests/codex_mcp_runner_contracts.json",
    ):
        if (root / forbidden_manifest).exists():
            fail(f"stale Codex-bound manifest must be removed: {forbidden_manifest}")

    for manifest, rel in (
        (runtime_policy, "manifests/adk_runtime_policy_gates.json"),
        (rules, "manifests/adk_rules_contracts.json"),
        (runtime_api, "manifests/adk_runtime_api_contracts.json"),
        (adk_runner, "manifests/adk_runner_contracts.json"),
    ):
        if "platform_bindings" in manifest:
            fail(f"{rel} must not define platform_bindings")
        if not manifest.get("reference_boundary"):
            fail(f"{rel} missing reference_boundary")
        if not str(manifest.get("scope_model", "")).startswith("platform-neutral-adk-"):
            fail(f"{rel} must use a platform-neutral ADK scope_model")

    suite_categories = {suite.get("category") for suite in evals.get("suites", [])}
    for category in ("routing", "governance", "completion", "macro-eval"):
        if category not in suite_categories:
            fail(f"eval suite category missing: {category}")
    for suite in evals.get("suites", []):
        require_keys(suite, ["id", "category", "owner", "goal", "dataset_path", "fixtures", "graders", "minimum_gate"], f"eval suite {suite.get('id')}")
    suite_ids = {suite.get("id") for suite in evals.get("suites", [])}
    for expected_suite in (
        "governance-eval-guardrail-regression-dataset",
        "macro-eval-stored-session-regression-monitoring",
        "completion-eval-goal-done-when-negative-fixtures",
    ):
        if expected_suite not in suite_ids:
            fail(f"eval suite missing: {expected_suite}")
    for suite in evals.get("suites", []):
        if suite.get("id") == "governance-eval-guardrail-regression-dataset":
            expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
            for expected in ("trigger", "do-not-trigger", "analyze-with-boundary"):
                if expected not in expected_values:
                    fail(f"guardrail regression suite missing expected case: {expected}")
        if suite.get("id") == "macro-eval-stored-session-regression-monitoring":
            expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
            for expected in ("reject", "accept", "promote-to-regression-candidate"):
                if expected not in expected_values:
                    fail(f"stored-session monitoring suite missing expected case: {expected}")
            grader_names = {grader.get("name") for grader in suite.get("graders", [])}
            if "regression_link_present" not in grader_names:
                fail("stored-session monitoring suite missing regression_link_present grader")
        if suite.get("id") == "completion-eval-goal-done-when-negative-fixtures":
            expected_values = {fixture.get("expected") for fixture in suite.get("fixtures", [])}
            for expected in ("needs-fix", "pass"):
                if expected not in expected_values:
                    fail(f"goal done-when suite missing expected case: {expected}")
            if not any("done-when" in fixture.get("id", "") for fixture in suite.get("fixtures", [])):
                fail("goal done-when suite missing explicit done-when negative fixture")

    trace_contracts = trace.get("contracts", [])
    if not trace_contracts:
        fail("trace contracts are empty")
    required_trace_fields = {
        "run_id",
        "task_id",
        "primary_skill",
        "model_version",
        "prompt_version",
        "orchestration_mode",
        "tool_calls",
        "tools_used",
        "handoffs",
        "guardrails",
        "verification",
        "blockers",
        "failure_pattern",
    }
    trace_contract_ids = {contract.get("id") for contract in trace_contracts}
    if "adk-workflow-trace-summary-v1" in trace_contract_ids:
        fail("retired adk-workflow-trace-summary-v1 contract must not return")
    canonical_trace_id = trace.get("canonical_trace_summary_contract", {}).get("id")
    if canonical_trace_id != "adk-workflow-trace-summary-v2":
        fail("canonical trace summary contract must remain v2")
    canonical_trace = next(
        (contract for contract in trace_contracts if contract.get("id") == canonical_trace_id),
        None,
    )
    if not canonical_trace:
        fail("canonical v2 trace summary contract is missing")
    else:
        canonical_fields = set(canonical_trace.get("required_fields", []))
        for field in ("asset_bundle_sha256", "runtime_target", "runtime_version", "goal_ref", "next_goal_ref"):
            if field not in canonical_fields:
                fail(f"canonical v2 trace contract missing field: {field}")
        for retired_field in ("goal", "next_goal"):
            if retired_field in canonical_fields:
                fail(f"canonical v2 trace contract contains retired field: {retired_field}")
        if "deprecated_compatibility_fields" in canonical_trace or "compatibility" in canonical_trace:
            fail("canonical v2 trace contract must not carry v1 compatibility metadata")
    for contract in trace_contracts:
        fields = set(contract.get("required_fields", []))
        missing = sorted(required_trace_fields - fields)
        if missing:
            fail(f"trace contract {contract.get('id')} missing fields: {', '.join(missing)}")
        require_keys(contract, ["id", "owner", "applies_to", "evidence_policy", "eval_use"], f"trace contract {contract.get('id')}")
        macro_policy = contract.get("macro_eval_policy", {})
        if macro_policy:
            require_keys(macro_policy, ["group_by", "promotion_rule", "must_not"], f"trace macro_eval_policy {contract.get('id')}")
            for field in ("model_version", "prompt_version", "orchestration_mode", "primary_skill", "failure_pattern"):
                if field not in macro_policy.get("group_by", []):
                    fail(f"trace macro_eval_policy {contract.get('id')} missing group_by field: {field}")
        stored_policy = contract.get("stored_session_monitoring_policy", {})
        if stored_policy:
            require_keys(stored_policy, ["enabled_default", "allowed_sources", "required_fields", "must_not"], f"stored_session_monitoring_policy {contract.get('id')}")
            if stored_policy.get("enabled_default") is not False:
                fail(f"stored_session_monitoring_policy {contract.get('id')} must be disabled by default")
            for field in ("source_id", "retention_policy", "redaction_status", "prompt_version", "owner_approval"):
                if field not in stored_policy.get("required_fields", []):
                    fail(f"stored_session_monitoring_policy {contract.get('id')} missing required field: {field}")
            if not any("raw user prompts" in item for item in stored_policy.get("must_not", [])):
                fail(f"stored_session_monitoring_policy {contract.get('id')} must reject raw user prompts")
        regression_policy = contract.get("regression_case_policy", {})
        if regression_policy:
            require_keys(regression_policy, ["enabled_default", "required_fields", "promotion_rule", "must_not"], f"regression_case_policy {contract.get('id')}")
            if regression_policy.get("enabled_default") is not False:
                fail(f"regression_case_policy {contract.get('id')} must be disabled by default")
            for field in ("dataset_id", "case_id", "source_trace_id", "prompt_version", "candidate_prompt_version", "expected_regression_signal", "grader", "score_threshold", "regression_link", "retention_policy", "redaction_status", "owner_approval"):
                if field not in regression_policy.get("required_fields", []):
                    fail(f"regression_case_policy {contract.get('id')} missing required field: {field}")
            if not any("raw sessions" in item.lower() or "unredacted traces" in item.lower() for item in regression_policy.get("must_not", [])):
                fail(f"regression_case_policy {contract.get('id')} must reject raw sessions or unredacted traces")
        replay_policy = contract.get("replay_policy", {})
        if contract.get("id") == "replayable-run-evidence-bundle-v1":
            fields = set(contract.get("required_fields", []))
            for field in (
                "input_snapshot",
                "environment_snapshot",
                "tool_transcript_digest",
                "artifact_hashes",
                "expected_assertions",
                "replay_safety_boundary",
                "sensitive_data_review",
                "manual_replay_notes",
                "non_replayable_reason",
            ):
                if field not in fields:
                    fail(f"replayable run evidence contract missing field: {field}")
            require_keys(replay_policy, ["enabled_default", "promotion_rule", "required_assertions", "must_not"], "replayable run evidence policy")
            if replay_policy.get("enabled_default") is not False:
                fail("replayable run evidence policy must be disabled by default")
            if not any("sensitive" in item.lower() for item in replay_policy.get("required_assertions", [])):
                fail("replayable run evidence policy must require sensitive-data assertion")
            if not any("unattended automation" in item.lower() for item in replay_policy.get("must_not", [])):
                fail("replayable run evidence policy must not promote unattended automation from one demonstration")
    if "replayable-run-evidence-bundle-v1" not in {contract.get("id") for contract in trace_contracts}:
        fail("trace contracts missing replayable-run-evidence-bundle-v1")
    if not any(contract.get("regression_case_policy") for contract in trace_contracts):
        fail("trace contracts missing regression_case_policy")

    tool_description_policy = mcp.get("tool_description_policy", {})
    require_keys(tool_description_policy, ["required_elements", "review_payloads", "remembered_approvals"], "mcp tool_description_policy")
    for element in ("Use this when guidance", "disallowed or edge cases", "parameter descriptions and enums when applicable", "side-effect and approval class"):
        if element not in tool_description_policy.get("required_elements", []):
            fail(f"mcp tool_description_policy missing required element: {element}")

    data_only_mcp = mcp.get("data_only_mcp_compatibility", {})
    require_keys(data_only_mcp, ["preferred_tools", "search_required_output", "fetch_required_output", "compatibility_note", "risk_review"], "mcp data_only_mcp_compatibility")
    for tool in ("search", "fetch"):
        if tool not in data_only_mcp.get("preferred_tools", []):
            fail(f"mcp data_only_mcp_compatibility missing preferred tool: {tool}")
    for field in ("structuredContent.results[].id", "structuredContent.results[].title", "structuredContent.results[].url"):
        if field not in data_only_mcp.get("search_required_output", []):
            fail(f"mcp data_only_mcp_compatibility missing search field: {field}")
    for field in ("structuredContent.id", "structuredContent.title", "structuredContent.text", "structuredContent.url"):
        if field not in data_only_mcp.get("fetch_required_output", []):
            fail(f"mcp data_only_mcp_compatibility missing fetch field: {field}")

    mcp_runtime_policy = mcp.get("runtime_config_policy", {})
    require_keys(
        mcp_runtime_policy,
        [
            "required_server_fields",
            "required_http_fields",
            "required_oauth_fields",
            "approval_modes",
            "quality_gates",
            "must_not",
        ],
        "mcp runtime_config_policy",
    )
    for field in ("enabled", "required", "startup_timeout_sec", "tool_timeout_sec", "enabled_tools", "disabled_tools", "default_tools_approval_mode"):
        if field not in mcp_runtime_policy.get("required_server_fields", []):
            fail(f"mcp runtime_config_policy missing server field: {field}")
    for field in ("bearer_token_env_var", "env_http_headers"):
        if field not in mcp_runtime_policy.get("required_http_fields", []):
            fail(f"mcp runtime_config_policy missing HTTP field: {field}")
    for field in ("mcp_oauth_credentials_store", "mcp_oauth_callback_port", "mcp_oauth_callback_url", "scopes"):
        if field not in mcp_runtime_policy.get("required_oauth_fields", []):
            fail(f"mcp runtime_config_policy missing OAuth field: {field}")
    for mode in ("auto", "prompt", "approve"):
        if mode not in mcp_runtime_policy.get("approval_modes", []):
            fail(f"mcp runtime_config_policy missing approval mode: {mode}")
    if not any("destructive" in item.lower() and "prompt" in item.lower() for item in mcp_runtime_policy.get("quality_gates", [])):
        fail("mcp runtime_config_policy must require prompt mode for write-capable/open-world tools")
    if not any("bearer tokens" in item.lower() for item in mcp_runtime_policy.get("must_not", [])):
        fail("mcp runtime_config_policy must forbid bearer tokens in manifests or project config")

    for dep in mcp.get("dependencies", []):
        require_keys(
            dep,
            [
                "skill",
                "mcp_server",
                "purpose",
                "transport",
                "required",
                "startup_timeout_sec",
                "tool_timeout_sec",
                "default_tools_approval_mode",
                "per_tool_approval_mode",
                "oauth",
                "tool_hints",
                "auth_boundary",
                "pii_policy",
                "dry_run",
                "fallback",
            ],
            f"mcp dependency {dep.get('skill')}",
        )
        for key in ("enabled_tools", "disabled_tools"):
            if key not in dep or not isinstance(dep[key], list):
                fail(f"mcp dependency {dep.get('skill')} missing list key: {key}")
        hints = dep.get("tool_hints", {})
        for key in ("readOnlyHint", "destructiveHint", "openWorldHint"):
            if key not in hints or not isinstance(hints[key], bool):
                fail(f"mcp dependency {dep.get('skill')} missing boolean tool_hints.{key}")
        if dep.get("startup_timeout_sec", 0) <= 0:
            fail(f"mcp dependency {dep.get('skill')} startup_timeout_sec must be positive")
        if dep.get("tool_timeout_sec", 0) <= 0:
            fail(f"mcp dependency {dep.get('skill')} tool_timeout_sec must be positive")
        if dep.get("default_tools_approval_mode") not in {"auto", "prompt", "approve"}:
            fail(f"mcp dependency {dep.get('skill')} has invalid default_tools_approval_mode")
        oauth = dep.get("oauth", {})
        for key in ("callback_port", "callback_url", "scopes"):
            if key not in oauth:
                fail(f"mcp dependency {dep.get('skill')} missing oauth.{key}")
    if not mcp.get("dependencies"):
        fail("mcp dependencies are empty")

    for audit in slash.get("audits", []):
        require_keys(audit, ["command_id", "command", "owner", "mode", "read_only", "destructive", "open_world", "approval", "evidence_required"], f"slash audit {audit.get('command_id')}")
        if audit.get("destructive") and audit.get("mode") in {"approved", "auto-approved"}:
            fail(f"slash audit {audit.get('command_id')} destructive command cannot default to approved mode")
    if not slash.get("audits"):
        fail("slash command audits are empty")

    for contract in subagents.get("contracts", []):
        require_keys(contract, ["id", "owner", "scope_read", "scope_write", "must_not_touch", "handoff_condition", "reply_owner", "stop_condition", "report_schema", "conflict_policy"], f"subagent contract {contract.get('id')}")
        stop_condition = contract.get("stop_condition", "")
        for token in ("pass", "replan", "split", "blocked", "abort"):
            if token not in stop_condition:
                fail(f"subagent contract {contract.get('id')} stop_condition missing {token}")
        report_schema = contract.get("report_schema", [])
        for field in ("summary", "evidence_refs", "raw_output_policy"):
            if field not in report_schema:
                fail(f"subagent contract {contract.get('id')} report_schema missing {field}")
    if not subagents.get("contracts"):
        fail("subagent contracts are empty")

    subagent_runtime_limits = subagents.get("runtime_limits", {})
    locals_copy = locals()
    context.bindings.update({name: locals_copy[name] for name in ["subagent_runtime_limits","trace_contracts"] if name in locals_copy})
