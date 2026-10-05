"""Official documentation runtime checks; read-only owned audit stage."""
from __future__ import annotations


from .official_docs_context import AuditContext


def check(context: AuditContext) -> None:
    context_state = context.bindings["context_state"]
    docs_mcp_tooling = context.bindings["docs_mcp_tooling"]
    fail = context.bindings["fail"]
    hooks = context.bindings["hooks"]
    require_keys = context.bindings["require_keys"]
    rules = context.bindings["rules"]
    runtime_api = context.bindings["runtime_api"]
    runtime_policy = context.bindings["runtime_policy"]
    subagent_runtime_limits = context.bindings["subagent_runtime_limits"]
    subagents = context.bindings["subagents"]
    require_keys(
        subagent_runtime_limits,
        [
            "max_threads_default",
            "max_depth_default",
            "job_max_runtime_seconds_fallback",
            "nested_subagents_default_allowed",
            "must_record",
            "must_not",
        ],
        "subagent runtime_limits",
    )
    if subagent_runtime_limits.get("max_threads_default") != 6:
        fail("subagent runtime_limits max_threads_default must be 6")
    if subagent_runtime_limits.get("max_depth_default") != 1:
        fail("subagent runtime_limits max_depth_default must be 1")
    if subagent_runtime_limits.get("job_max_runtime_seconds_fallback") != 1800:
        fail("subagent runtime_limits job_max_runtime_seconds_fallback must be 1800")
    if subagent_runtime_limits.get("nested_subagents_default_allowed") is not False:
        fail("subagent runtime_limits nested subagents must be disabled by default")
    for field in (
        "features.multi_agent",
        "agents.max_threads",
        "agents.max_depth",
        "agents.job_max_runtime_seconds",
        "scope_write",
        "subagent_result.summary",
        "subagent_result.evidence_refs",
        "subagent_result.raw_output_retention_decision",
    ):
        if field not in subagent_runtime_limits.get("must_record", []):
            fail(f"subagent runtime_limits missing must_record field: {field}")
    if not any("nested" in item.lower() for item in subagent_runtime_limits.get("must_not", [])):
        fail("subagent runtime_limits must forbid implicit nested subagents")
    if not any("raw logs" in item.lower() or "command transcripts" in item.lower() for item in subagent_runtime_limits.get("must_not", [])):
        fail("subagent runtime_limits must forbid raw noisy output by default")

    subagent_noise_budget = subagents.get("context_noise_budget", {})
    require_keys(
        subagent_noise_budget,
        [
            "enabled_default",
            "required_fields",
            "summary_token_budget",
            "raw_output_policy",
            "quality_gates",
            "must_not",
        ],
        "subagent context_noise_budget",
    )
    if subagent_noise_budget.get("enabled_default") is not True:
        fail("subagent context_noise_budget must be enabled by default")
    for field in (
        "summary_token_budget",
        "evidence_ref_count",
        "raw_output_retention_decision",
        "redaction_status",
        "parent_context_merge_policy",
        "noise_rejection_reason",
    ):
        if field not in subagent_noise_budget.get("required_fields", []):
            fail(f"subagent context_noise_budget missing required field: {field}")
    if subagent_noise_budget.get("summary_token_budget", {}).get("default_soft_limit", 0) <= 0:
        fail("subagent context_noise_budget summary soft limit must be positive")
    if not any("raw output" in gate.lower() and "retention" in gate.lower() for gate in subagent_noise_budget.get("quality_gates", [])):
        fail("subagent context_noise_budget must require raw output retention decision")
    if not any("raw command transcripts" in item.lower() for item in subagent_noise_budget.get("must_not", [])):
        fail("subagent context_noise_budget must forbid raw command transcripts by default")

    runtime_layers = runtime_policy.get("policy_layers", [])
    if not runtime_layers:
        fail("runtime policy layers are empty")
    layer_ids = {layer.get("id") for layer in runtime_layers}
    for expected in ("managed-runtime-requirements", "project-runtime-boundary"):
        if expected not in layer_ids:
            fail(f"runtime policy layer missing: {expected}")
    for layer in runtime_layers:
        lid = layer.get("id")
        require_keys(layer, ["id", "owner", "config_file", "precedence", "user_override_allowed", "required_controls", "verification"], f"runtime policy layer {lid}")
        if lid == "managed-runtime-requirements" and layer.get("user_override_allowed") is not False:
            fail("managed runtime requirements must not allow user override")
        if lid == "project-runtime-boundary":
            must_not_override = set(layer.get("must_not_override", []))
            for key in ("openai_base_url", "chatgpt_base_url", "apps_mcp_product_sku", "model_provider", "model_providers", "notify", "profile", "profiles", "experimental_realtime_ws_base_url", "otel"):
                if key not in must_not_override:
                    fail(f"project config boundary missing must_not_override: {key}")
        network = layer.get("network_policy")
        if network:
            if network.get("deny_wins") is not True:
                fail(f"runtime policy layer {lid} must enforce deny-wins network policy")
            if network.get("global_allow_allowed") is not False:
                fail(f"runtime policy layer {lid} must forbid global network allow by default")
            if network.get("network_proxy_required_when_network_enabled") is not True:
                fail(f"runtime policy layer {lid} must require network_proxy when command network is enabled")
            if network.get("allow_local_binding_default") is not False:
                fail(f"runtime policy layer {lid} must keep allow_local_binding disabled by default")
            if network.get("dangerously_allow_non_loopback_proxy_default") is not False:
                fail(f"runtime policy layer {lid} must forbid non-loopback proxy by default")
            if network.get("dangerously_allow_all_unix_sockets_default") is not False:
                fail(f"runtime policy layer {lid} must forbid all Unix sockets by default")
            if network.get("unix_sockets_allowlist_required") is not True:
                fail(f"runtime policy layer {lid} must require Unix socket allowlist")
        web_search = layer.get("web_search_policy")
        if web_search:
            allowed_modes = set(web_search.get("allowed_modes", []))
            if not {"disabled", "cached"}.issubset(allowed_modes):
                fail(f"runtime policy layer {lid} web_search_policy must allow disabled and cached modes")
            if web_search.get("live_requires_explicit_approval") is not True:
                fail(f"runtime policy layer {lid} live web search must require explicit approval")
            if web_search.get("treat_results_as_untrusted") is not True:
                fail(f"runtime policy layer {lid} must treat web results as untrusted")

    sandbox_presets = runtime_policy.get("sandbox_presets", [])
    if not sandbox_presets:
        fail("sandbox presets are empty")
    preset_by_id = {preset.get("id"): preset for preset in sandbox_presets}
    low_risk = preset_by_id.get("low-risk-local-automation", {})
    if low_risk.get("sandbox_mode") != "workspace-write" or low_risk.get("approval_policy") != "on-request":
        fail("low-risk sandbox preset must be workspace-write + on-request")
    full_access = preset_by_id.get("full-access", {})
    if full_access.get("sandbox_mode") != "danger-full-access" or full_access.get("approval_policy") != "never":
        fail("full-access preset must explicitly model danger-full-access + never")
    if full_access.get("default_allowed") is not False or full_access.get("risk") != "critical":
        fail("full-access preset must be critical and not default allowed")
    for forbidden in runtime_policy.get("forbidden_defaults", []):
        require_keys(forbidden, ["id", "reason"], f"forbidden default {forbidden.get('id')}")
    for forbidden_id in ("network-proxy-non-loopback", "all-unix-sockets", "web-search-live-default"):
        if forbidden_id not in {item.get("id") for item in runtime_policy.get("forbidden_defaults", [])}:
            fail(f"runtime forbidden default missing: {forbidden_id}")

    config_boundaries = runtime_policy.get("config_key_boundaries", {})
    require_keys(
        config_boundaries,
        [
            "project_local_must_not_override",
            "user_level_only",
            "project_local_allowed_when_trusted",
            "verification",
        ],
        "runtime config_key_boundaries",
    )
    for key in ("openai_base_url", "chatgpt_base_url", "apps_mcp_product_sku", "model_provider", "model_providers", "notify", "profile", "profiles", "experimental_realtime_ws_base_url", "otel"):
        if key not in config_boundaries.get("project_local_must_not_override", []):
            fail(f"runtime config_key_boundaries missing project-local deny key: {key}")
    for key in ("provider", "auth", "telemetry_routing"):
        if key not in config_boundaries.get("user_level_only", []):
            fail(f"runtime config_key_boundaries missing user-level-only key: {key}")
    if "trust_level" not in " ".join(config_boundaries.get("verification", [])):
        fail("runtime config_key_boundaries must record trust_level verification")

    granular_approval = runtime_policy.get("granular_approval_policy", {})
    require_keys(granular_approval, ["allowed_keys", "default_reviewer", "auto_review_requires_policy", "must_record", "must_not"], "runtime granular_approval_policy")
    for key in ("sandbox_approval", "rules", "mcp_elicitations", "request_permissions", "skill_approval"):
        if key not in granular_approval.get("allowed_keys", []):
            fail(f"runtime granular_approval_policy missing key: {key}")
    if granular_approval.get("auto_review_requires_policy") is not True:
        fail("runtime granular_approval_policy must require auto_review policy")
    if not any("human approval" in item.lower() for item in granular_approval.get("must_not", [])):
        fail("runtime granular_approval_policy must not treat auto_review as human approval")

    permission_policy = runtime_policy.get("permission_profile_policy", {})
    require_keys(permission_policy, ["built_in_profiles", "custom_profile_required_fields", "deny_read_controls", "network_controls", "must_not"], "runtime permission_profile_policy")
    for profile in (":read-only", ":workspace", ":danger-full-access"):
        if profile not in permission_policy.get("built_in_profiles", []):
            fail(f"runtime permission_profile_policy missing built-in profile: {profile}")
    for field in ("description", "extends", "filesystem", "network", "workspace_roots"):
        if field not in permission_policy.get("custom_profile_required_fields", []):
            fail(f"runtime permission_profile_policy missing custom profile field: {field}")
    if not any("deny" in item.lower() for item in permission_policy.get("deny_read_controls", [])):
        fail("runtime permission_profile_policy must include deny-read controls")
    if not any("unix" in item.lower() for item in permission_policy.get("network_controls", [])):
        fail("runtime permission_profile_policy must include Unix socket controls")
    if not any(":danger-full-access" in item for item in permission_policy.get("must_not", [])):
        fail("runtime permission_profile_policy must forbid extending :danger-full-access")

    memory_runtime_policy = runtime_policy.get("memory_runtime_policy", {})
    require_keys(memory_runtime_policy, ["feature_flag", "default_enabled", "required_fields", "external_context_controls", "quality_gates", "must_not"], "runtime memory_runtime_policy")
    if memory_runtime_policy.get("feature_flag") != "features.memories":
        fail("runtime memory_runtime_policy feature_flag must be features.memories")
    if memory_runtime_policy.get("default_enabled") is not False:
        fail("runtime memory_runtime_policy must be disabled by default")
    for field in ("memories.generate_memories", "memories.use_memories", "memories.disable_on_external_context", "memories.max_rollout_age_days", "memories.min_rollout_idle_hours"):
        if field not in memory_runtime_policy.get("required_fields", []):
            fail(f"runtime memory_runtime_policy missing field: {field}")
    for control in ("MCP", "web_search", "tool_search"):
        if control not in memory_runtime_policy.get("external_context_controls", []):
            fail(f"runtime memory_runtime_policy missing external context control: {control}")
    if not any("owner approval" in item.lower() for item in memory_runtime_policy.get("quality_gates", [])):
        fail("runtime memory_runtime_policy must require owner approval")
    if not any("raw session transcripts" in item.lower() for item in memory_runtime_policy.get("must_not", [])):
        fail("runtime memory_runtime_policy must forbid raw session transcript memory")

    rule_contracts = rules.get("contracts", [])
    if not rule_contracts:
        fail("ADK rules contracts are empty")
    for contract in rule_contracts:
        cid = contract.get("id")
        require_keys(
            contract,
            [
                "id",
                "owner",
                "scope",
                "rules_file",
                "decision_values",
                "required_fields",
                "minimum_match_examples",
                "minimum_not_match_examples",
                "compound_shell_policy",
                "forbidden_prefix_examples",
                "verification",
                "promotion_gate",
            ],
            f"rules contract {cid}",
        )
        decisions = set(contract.get("decision_values", []))
        if not decisions.issubset({"allow", "prompt", "forbidden"}):
            fail(f"rules contract {cid} has invalid decision_values")
        fields = set(contract.get("required_fields", []))
        for field in ("pattern", "decision", "justification", "match", "not_match"):
            if field not in fields:
                fail(f"rules contract {cid} missing required_fields entry: {field}")
        if contract.get("minimum_match_examples", 0) < 1:
            fail(f"rules contract {cid} must require at least one match example")
        if contract.get("minimum_not_match_examples", 0) < 1:
            fail(f"rules contract {cid} must require at least one not_match example")

    runtime_api_groups = runtime_api.get("method_groups", [])
    if not runtime_api_groups:
        fail("ADK runtime API method groups are empty")
    required_api_groups = {
        "thread-lifecycle-read",
        "thread-state-write",
        "thread-destructive-state",
        "process-and-shell-open-world",
        "sandboxed-command-exec",
        "fs-config-plugin-write",
        "mcp-app-tool-bridge",
    }
    api_group_ids = {group.get("id") for group in runtime_api_groups}
    for group_id in required_api_groups:
        if group_id not in api_group_ids:
            fail(f"ADK runtime API group missing: {group_id}")
    transport_policy = runtime_api.get("transport_policy", {})
    require_keys(transport_policy, ["supported", "experimental", "forbidden_defaults", "required_auth_for_remote"], "ADK runtime API transport policy")
    if "non-loopback unauthenticated websocket" not in transport_policy.get("forbidden_defaults", []):
        fail("ADK runtime API transport policy must forbid non-loopback unauthenticated websocket")
    for group in runtime_api_groups:
        gid = group.get("id")
        require_keys(group, ["id", "owner", "methods", "risk", "classification", "required_evidence", "approval_boundary"], f"ADK runtime API group {gid}")
        classification = group.get("classification", {})
        for key in ("read_only", "destructive", "open_world", "sandbox_inherited"):
            if key not in classification or not isinstance(classification[key], bool):
                fail(f"ADK runtime API group {gid} missing boolean classification.{key}")
        if gid == "process-and-shell-open-world":
            if "thread/shellCommand" not in group.get("methods", []):
                fail("process-and-shell-open-world must include thread/shellCommand")
            if classification.get("sandbox_inherited") is not False or classification.get("open_world") is not True:
                fail("process-and-shell-open-world must be open-world and not inherit thread sandbox")
        if gid == "fs-config-plugin-write" and classification.get("destructive") is not True:
            fail("fs-config-plugin-write must be destructive")

    context_contracts = context_state.get("contracts", [])
    if not context_contracts:
        fail("context state contracts are empty")
    context_ids = {contract.get("id") for contract in context_contracts}
    if "instruction-hierarchy-context-boundary" not in context_ids:
        fail("context state contract missing: instruction-hierarchy-context-boundary")
    for contract in context_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "applies_to", "required_fields", "quality_gates", "poisoning_controls", "verification"], f"context state contract {cid}")
        if "context_classes" in contract:
            classes = set(contract.get("context_classes", []))
            for context_class in ("stable", "dynamic", "evidence", "excluded"):
                if context_class not in classes:
                    fail(f"context state contract {cid} missing context class: {context_class}")
        required_fields = set(contract.get("required_fields", []))
        if cid == "long-thread-session-summary":
            for field in ("latest_goal", "invalidated_goals", "raw_evidence", "next_goal", "fallback_condition"):
                if field not in required_fields:
                    fail(f"context state contract {cid} missing field: {field}")
        if cid == "responses-state-handoff":
            for field in (
                "previous_response_id_policy",
                "phase_preservation",
                "prompt_cache_layout",
                "retention_mode",
                "encrypted_reasoning_policy",
                "store_false_policy",
                "call_id_correlation_policy",
                "state_retention_evidence",
            ):
                if field not in required_fields:
                    fail(f"context state contract {cid} missing field: {field}")
        if cid == "instruction-hierarchy-context-boundary":
            require_keys(contract, ["authority_layers"], "instruction hierarchy context contract")
            for layer in ("system_developer_policy", "repo_agents_policy", "skill_contract", "user_goal", "dynamic_context", "tool_output"):
                if layer not in contract.get("authority_layers", []):
                    fail(f"instruction hierarchy contract missing authority layer: {layer}")
            for field in ("authority_boundary", "dynamic_context_boundary", "tool_output_trust_level", "conflict_resolution"):
                if field not in required_fields:
                    fail(f"instruction hierarchy contract missing required field: {field}")
            if not any("tool output" in item.lower() and "not policy" in item.lower() for item in contract.get("quality_gates", [])):
                fail("instruction hierarchy contract must state tool outputs are not policy")

    docs_mcp_server = docs_mcp_tooling.get("server", {})
    require_keys(docs_mcp_server, ["name", "url", "transport", "purpose"], "OpenAI Docs MCP server")
    if docs_mcp_server.get("url") != "https://developers.openai.com/mcp":
        fail("OpenAI Docs MCP server URL must be https://developers.openai.com/mcp")
    docs_tool_targets = docs_mcp_tooling.get("tooling_targets", [])
    if not docs_tool_targets:
        fail("OpenAI Docs MCP tooling targets are empty")
    target_ids = {target.get("id") for target in docs_tool_targets}
    for target_id in ("generic-mcp-client", "vscode", "cursor", "claude-code"):
        if target_id not in target_ids:
            fail(f"OpenAI Docs MCP tooling target missing: {target_id}")
    for target in docs_tool_targets:
        tid = target.get("id")
        require_keys(target, ["id", "config_files", "install_command", "verification", "agents_instruction"], f"OpenAI Docs MCP tooling target {tid}")
    freshness_policy = docs_mcp_tooling.get("freshness_policy", {})
    require_keys(freshness_policy, ["source_manifest", "max_age_days", "fallback_domains", "must_not"], "OpenAI Docs MCP freshness policy")
    if "developers.openai.com" not in freshness_policy.get("fallback_domains", []):
        fail("OpenAI Docs MCP freshness policy must include developers.openai.com fallback domain")

    hook_events = hooks.get("events", [])
    if not hook_events:
        fail("hook runtime audits are empty")
    required_hook_fields = set(hooks.get("required_audit_fields", []))
    for field in ("event", "supports_matcher", "supported_output_fields", "must_not_rely_on", "trust_required"):
        if field not in required_hook_fields:
            fail(f"hook required_audit_fields missing: {field}")
    hook_by_event = {event.get("event"): event for event in hook_events}
    for event in ("PreToolUse", "PermissionRequest", "PostToolUse", "Stop"):
        if event not in hook_by_event:
            fail(f"hook event audit missing: {event}")
    for event in hook_events:
        eid = event.get("event")
        require_keys(event, ["event", "supports_matcher", "supported_output_fields", "must_not_rely_on", "side_effect_policy", "trust_required", "concurrency_risk"], f"hook event {eid}")
        if not isinstance(event.get("supports_matcher"), bool):
            fail(f"hook event {eid} supports_matcher must be boolean")
        if event.get("trust_required") is not True:
            fail(f"hook event {eid} must require trust")
    pre_tool = hook_by_event.get("PreToolUse", {})
    if "continue" not in pre_tool.get("must_not_rely_on", []):
        fail("PreToolUse must not rely on continue")
    stop_hook = hook_by_event.get("Stop", {})
    if stop_hook.get("supports_matcher") is not False:
        fail("Stop hook matcher must be marked unsupported")
    if "matcher" not in stop_hook.get("must_not_rely_on", []):
        fail("Stop hook must_not_rely_on must include matcher")
    locals_copy = locals()
    context.bindings.update({name: locals_copy[name] for name in ["context_contracts","docs_tool_targets","hook_events","rule_contracts","runtime_api_groups","runtime_layers","sandbox_presets"] if name in locals_copy})
