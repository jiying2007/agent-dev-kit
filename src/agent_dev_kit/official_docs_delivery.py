"""Official documentation delivery checks; read-only owned audit stage."""
from __future__ import annotations


from .official_docs_context import AuditContext


def check(context: AuditContext) -> None:
    adk_runner = context.bindings["adk_runner"]
    automation_worktree = context.bindings["automation_worktree"]
    fail = context.bindings["fail"]
    hooks = context.bindings["hooks"]
    improvement_loop = context.bindings["improvement_loop"]
    plugins = context.bindings["plugins"]
    require_keys = context.bindings["require_keys"]
    structured_outputs = context.bindings["structured_outputs"]
    tool_search = context.bindings["tool_search"]
    if not hooks.get("deny_path"):
        fail("hooks deny_path is empty")
    if not hooks.get("log_redaction"):
        fail("hooks log_redaction is empty")

    adk_runner_contracts = adk_runner.get("contracts", [])
    if not adk_runner_contracts:
        fail("ADK runner contracts are empty")
    runner_smoke = adk_runner.get("smoke_contract", {})
    require_keys(runner_smoke, ["id", "owner", "applies_to", "required_evidence", "quality_gates", "must_not"], "ADK runner smoke_contract")
    for field in (
        "client_info_or_adapter_id",
        "thread_start_result",
        "turn_start_result",
        "jsonl_or_structured_event_stream",
        "output_schema_validation",
        "sandbox_policy_record",
        "approval_policy_record",
        "cwd_record",
        "resume_or_reply_correlation",
        "failure_or_cancel_path",
    ):
        if field not in runner_smoke.get("required_evidence", []):
            fail(f"ADK runner smoke_contract missing evidence field: {field}")
    if not any("JSONL" in gate or "strict output schema" in gate for gate in runner_smoke.get("quality_gates", [])):
        fail("ADK runner smoke_contract must require JSONL or strict schema output")
    if not any("API keys" in item or "auth files" in item for item in runner_smoke.get("must_not", [])):
        fail("ADK runner smoke_contract must protect API keys or auth files")
    adk_runner_tools = {contract.get("tool") for contract in adk_runner_contracts}
    for tool in ("run-session", "reply-session"):
        if tool not in adk_runner_tools:
            fail(f"ADK runner contract missing tool: {tool}")
    for contract in adk_runner_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "tool", "purpose", "required_inputs", "approval_boundary", "sandbox_boundary", "state_output", "must_record", "stop_condition"], f"ADK runner contract {cid}")
        if contract.get("tool") == "reply-session" and "threadId" not in contract.get("required_inputs", []):
            fail("reply-session contract must require threadId")
        for token in ("pass", "replan", "split", "blocked", "abort"):
            if token not in contract.get("stop_condition", ""):
                fail(f"ADK runner contract {cid} stop_condition missing {token}")

    plugin_contracts = plugins.get("plugin_contracts", [])
    marketplace_contracts = plugins.get("marketplace_contracts", [])
    if not plugin_contracts:
        fail("plugin contracts are empty")
    if not marketplace_contracts:
        fail("marketplace contracts are empty")
    for contract in plugin_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "required_files", "naming", "allowed_extensions", "required_review"], f"plugin contract {cid}")
        files = set(contract.get("required_files", []))
        for required_file in (".adk-plugin/plugin.json", "skills/<skill-name>/SKILL.md"):
            if required_file not in files:
                fail(f"plugin contract {cid} missing required file: {required_file}")
        if "stable kebab-case" not in contract.get("naming", {}).get("plugin_name", ""):
            fail(f"plugin contract {cid} must require stable kebab-case plugin name")
        if "cross-harness invocation parity" not in contract.get("required_review", []):
            fail(f"plugin contract {cid} must require cross-harness invocation parity")
    for contract in marketplace_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "path", "required_fields", "source_path_policy", "install_policy_values", "failure_policy"], f"marketplace contract {cid}")
        required_fields = set(contract.get("required_fields", []))
        for field in ("plugins[].source.path", "plugins[].policy.installation", "plugins[].policy.authentication", "plugins[].category"):
            if field not in required_fields:
                fail(f"marketplace contract {cid} missing required field: {field}")
        for value in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"):
            if value not in contract.get("install_policy_values", []):
                fail(f"marketplace contract {cid} missing install policy value: {value}")

    structured_contracts = structured_outputs.get("contracts", [])
    if not structured_contracts:
        fail("structured output contracts are empty")
    required_schema_targets = {"task_package", "prototype_evidence", "evidence_index", "handoff_summary", "pr_review_findings"}
    seen_schema_targets = {contract.get("schema_target") for contract in structured_contracts}
    for target in required_schema_targets:
        if target not in seen_schema_targets:
            fail(f"structured output schema target missing: {target}")
    for contract in structured_contracts:
        cid = contract.get("id")
        require_keys(
            contract,
            [
                "id",
                "owner",
                "applies_to",
                "schema_target",
                "schema_format",
                "strict",
                "required_fields",
                "additional_properties",
                "refusal_handling",
                "drift_controls",
            ],
            f"structured output contract {cid}",
        )
        if contract.get("schema_format") != "json_schema":
            fail(f"structured output contract {cid} must use json_schema")
        if contract.get("strict") is not True:
            fail(f"structured output contract {cid} must require strict mode")
        if contract.get("additional_properties") is not False:
            fail(f"structured output contract {cid} must deny additional properties")
        if len(contract.get("required_fields", [])) < 5:
            fail(f"structured output contract {cid} has too few required fields")
        if not contract.get("drift_controls"):
            fail(f"structured output contract {cid} missing drift controls")
    task_package = next((item for item in structured_contracts if item.get("schema_target") == "task_package"), {})
    if task_package.get("id") != "adk-task-package-schema-v2":
        fail("task package contract must hard-cut to adk-task-package-schema-v2")
    for field in (
        "work_item_kind",
        "question_to_resolve",
        "evidence_required",
        "implementation_permission",
        "exit_gate",
        "handoff_target",
        "retention_decision",
    ):
        if field not in task_package.get("required_fields", []):
            fail(f"task package v2 missing field: {field}")
    task_field_rules = task_package.get("field_rules", {})
    if set(task_field_rules.get("work_item_kind", [])) != {"decision", "research", "prototype", "implementation"}:
        fail("task package v2 work_item_kind enum is invalid")
    if len(task_package.get("cross_field_rules", [])) < 5:
        fail("task package v2 cross-field permission rules are incomplete")
    prototype_evidence = next(
        (item for item in structured_contracts if item.get("schema_target") == "prototype_evidence"), {}
    )
    for field in (
        "question",
        "base_commit",
        "artifact_path",
        "artifact_sha256",
        "observed_result",
        "verification_command",
        "verification_exit_code",
        "retention_decision",
        "expires_at",
        "cleanup_owner",
        "rollback_anchor",
        "active_references_absent",
    ):
        if field not in prototype_evidence.get("required_fields", []):
            fail(f"prototype evidence contract missing field: {field}")
    if len(prototype_evidence.get("retention_rules", [])) < 5:
        fail("prototype evidence retention rules are incomplete")
    structured_gate = structured_outputs.get("quality_gate", {})
    require_keys(
        structured_gate,
        [
            "must_use_structured_outputs_over_json_mode",
            "json_mode_allowed_only_with_validation",
            "must_detect_refusals",
            "must_not",
        ],
        "structured output quality_gate",
    )
    if structured_gate.get("must_use_structured_outputs_over_json_mode") is not True:
        fail("structured output quality_gate must prefer structured outputs over JSON mode")
    if structured_gate.get("must_detect_refusals") is not True:
        fail("structured output quality_gate must detect refusals")

    tool_search_contracts = tool_search.get("contracts", [])
    if not tool_search_contracts:
        fail("tool search contracts are empty")
    for contract in tool_search_contracts:
        cid = contract.get("id")
        require_keys(
            contract,
            [
                "id",
                "owner",
                "applies_to",
                "namespace",
                "initial_surface",
                "deferred_surface",
                "max_initial_items",
                "max_namespace_tools",
                "selection_evidence",
                "cache_policy",
                "must_not",
            ],
            f"tool search contract {cid}",
        )
        if contract.get("max_initial_items", 0) > 20:
            fail(f"tool search contract {cid} max_initial_items must be <= 20")
        if contract.get("max_namespace_tools", 0) > 10:
            fail(f"tool search contract {cid} max_namespace_tools must be <= 10")
        for field in ("name", "description"):
            if not any(field in item for item in contract.get("initial_surface", [])):
                fail(f"tool search contract {cid} initial_surface must include {field}")
        if not contract.get("deferred_surface"):
            fail(f"tool search contract {cid} missing deferred_surface")
    tool_search_gate = tool_search.get("quality_gate", {})
    require_keys(
        tool_search_gate,
        [
            "deferred_loading_requires_namespace_summary",
            "tool_schema_review_required",
            "client_executed_search_requires_trusted_inventory",
            "must_record_loaded_tools",
        ],
        "tool search quality_gate",
    )
    for key in (
        "deferred_loading_requires_namespace_summary",
        "tool_schema_review_required",
        "client_executed_search_requires_trusted_inventory",
        "must_record_loaded_tools",
    ):
        if tool_search_gate.get(key) is not True:
            fail(f"tool search quality_gate {key} must be true")

    automation_contracts = automation_worktree.get("automation_contracts", [])
    worktree_contracts = automation_worktree.get("worktree_contracts", [])
    if not automation_contracts:
        fail("automation contracts are empty")
    if not worktree_contracts:
        fail("worktree contracts are empty")
    for contract in automation_contracts:
        cid = contract.get("id")
        require_keys(
            contract,
            [
                "id",
                "owner",
                "mode",
                "enabled_default",
                "prompt_requirements",
                "run_context",
                "sandbox_policy",
                "approval_policy",
                "first_run_review",
                "first_run_evidence",
                "reliability_promotion_gate",
                "result_policy",
                "cleanup_policy",
            ],
            f"automation contract {cid}",
        )
        if contract.get("mode") != "report-only":
            fail(f"automation contract {cid} must default to report-only")
        if contract.get("enabled_default") is not False:
            fail(f"automation contract {cid} must be disabled by default")
        if contract.get("first_run_review") is not True:
            fail(f"automation contract {cid} must require first-run review")
        first_run_evidence = contract.get("first_run_evidence", [])
        if len(first_run_evidence) < 3:
            fail(f"automation contract {cid} first_run_evidence must contain at least three evidence items")
        for required_evidence in ("run", "summary"):
            if not any(required_evidence in item for item in first_run_evidence):
                fail(f"automation contract {cid} first_run_evidence missing {required_evidence}")
        for required_prompt in ("durable", "stop"):
            if not any(required_prompt in item for item in contract.get("prompt_requirements", [])):
                fail(f"automation contract {cid} prompt_requirements missing {required_prompt}")
        promotion_gate = contract.get("reliability_promotion_gate", [])
        if len(promotion_gate) < 3:
            fail(f"automation contract {cid} reliability_promotion_gate must contain at least three gate items")
        for required_gate in ("manual", "report-only", "owner approval", "rollback"):
            if not any(required_gate in item for item in promotion_gate):
                fail(f"automation contract {cid} reliability_promotion_gate missing {required_gate}")
    for contract in worktree_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "applies_to", "creation_gate", "handoff_gate", "cleanup_gate", "must_not"], f"worktree contract {cid}")
        for gate_name in ("creation_gate", "handoff_gate", "cleanup_gate"):
            if not contract.get(gate_name):
                fail(f"worktree contract {cid} missing non-empty {gate_name}")
        if not any("branch" in item for item in contract.get("handoff_gate", [])):
            fail(f"worktree contract {cid} handoff_gate must mention branch limitations")
    automation_gate = automation_worktree.get("quality_gate", {})
    require_keys(
        automation_gate,
        [
            "automations_enabled_default_must_be_false",
            "first_runs_require_review",
            "first_run_evidence_required",
            "manual_reliable_before_scheduling",
            "promotion_requires_report_only_history",
            "promotion_evidence_required",
            "enabled_mode_requires_owner_approval_and_rollback",
            "full_access_never_for_default_automation",
            "worktree_cleanup_requires_retention_decision",
            "risk_fixtures_required",
            "dirty_worktree_requires_decision",
            "stale_heartbeat_requires_stop_or_replan",
        ],
        "automation worktree quality_gate",
    )
    for key in (
        "automations_enabled_default_must_be_false",
        "first_runs_require_review",
        "first_run_evidence_required",
        "manual_reliable_before_scheduling",
        "promotion_requires_report_only_history",
        "promotion_evidence_required",
        "enabled_mode_requires_owner_approval_and_rollback",
        "full_access_never_for_default_automation",
        "worktree_cleanup_requires_retention_decision",
        "risk_fixtures_required",
        "dirty_worktree_requires_decision",
        "stale_heartbeat_requires_stop_or_replan",
    ):
        if automation_gate.get(key) is not True:
            fail(f"automation worktree quality_gate {key} must be true")
    automation_risk_fixtures = automation_worktree.get("risk_fixtures", [])
    if len(automation_risk_fixtures) < 4:
        fail("automation worktree risk_fixtures must include at least four cases")
    fixture_expected = {fixture.get("expected") for fixture in automation_risk_fixtures}
    for expected in ("reject", "needs-fix"):
        if expected not in fixture_expected:
            fail(f"automation worktree risk_fixtures missing expected case: {expected}")
    for token in ("stop", "full-access", "dirty", "heartbeat"):
        if not any(token in fixture.get("id", "") or token in fixture.get("input", "") for fixture in automation_risk_fixtures):
            fail(f"automation worktree risk_fixtures missing token: {token}")

    improvement_loops = improvement_loop.get("loops", [])
    if not improvement_loops:
        fail("agent improvement loops are empty")
    improvement_loop_ids = {loop.get("id") for loop in improvement_loops}
    if "eval-baseline-first-optimization-v1" not in improvement_loop_ids:
        fail("agent improvement loop missing: eval-baseline-first-optimization-v1")
    for loop in improvement_loops:
        lid = loop.get("id")
        require_keys(
            loop,
            [
                "id",
                "owner",
                "applies_to",
                "stages",
                "required_artifacts",
                "promotion_gate",
                "must_not",
            ],
            f"agent improvement loop {lid}",
        )
        if lid == "trace-feedback-eval-handoff-v1":
            for stage in ("collect_sanitized_traces", "generate_eval_suite_candidate", "run_validation_gate", "write_adk_handoff", "human_approve_before_merge"):
                if stage not in loop.get("stages", []):
                    fail(f"agent improvement loop {lid} missing stage: {stage}")
            for artifact in ("trace_summary_set", "eval_suite_candidate", "validation_result", "adk_handoff"):
                if artifact not in loop.get("required_artifacts", []):
                    fail(f"agent improvement loop {lid} missing artifact: {artifact}")
        if lid == "eval-baseline-first-optimization-v1":
            for stage in ("define_success_metrics", "capture_eval_baseline", "run_representative_eval", "promote_or_rollback"):
                if stage not in loop.get("stages", []):
                    fail(f"eval-baseline-first loop missing stage: {stage}")
            for step in ("prompt_tuning", "examples_and_context", "tooling_or_retrieval"):
                if step not in loop.get("improvement_ladder", []):
                    fail(f"eval-baseline-first loop missing improvement ladder step: {step}")
            if not any("fine-tuning" in item for item in loop.get("must_not", [])):
                fail("eval-baseline-first loop must block premature fine-tuning")
    locals_copy = locals()
    context.bindings.update({name: locals_copy[name] for name in ["adk_runner_contracts","automation_contracts","improvement_loops","marketplace_contracts","plugin_contracts","structured_contracts","tool_search_contracts","worktree_contracts"] if name in locals_copy})
