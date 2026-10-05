"""Official documentation adoption checks; read-only owned audit stage."""
from __future__ import annotations


from .official_docs_context import AuditContext


def check(context: AuditContext) -> None:
    codex_surface_terms = context.bindings["codex_surface_terms"]
    data_retention = context.bindings["data_retention"]
    doc = context.bindings["doc"]
    fail = context.bindings["fail"]
    improvement_loop = context.bindings["improvement_loop"]
    model_selection = context.bindings["model_selection"]
    pr_review = context.bindings["pr_review"]
    prompt_cache = context.bindings["prompt_cache"]
    require_keys = context.bindings["require_keys"]
    skill_repro = context.bindings["skill_repro"]
    improvement_gate = improvement_loop.get("quality_gate", {})
    require_keys(
        improvement_gate,
        [
            "requires_human_approval_before_apply",
            "requires_validation_gate",
            "requires_adk_handoff_artifact",
            "requires_trace_feedback_linkage",
        ],
        "agent improvement loop quality_gate",
    )
    for key in (
        "requires_human_approval_before_apply",
        "requires_validation_gate",
        "requires_adk_handoff_artifact",
        "requires_trace_feedback_linkage",
    ):
        if improvement_gate.get(key) is not True:
            fail(f"agent improvement loop quality_gate {key} must be true")

    pr_review_contracts = pr_review.get("contracts", [])
    if not pr_review_contracts:
        fail("PR review governance contracts are empty")
    pr_review_ids = {contract.get("id") for contract in pr_review_contracts}
    for expected in ("adk-ci-pr-review-runner-v1", "untrusted-pr-isolation-v1", "inline-review-anchoring-v1"):
        if expected not in pr_review_ids:
            fail(f"PR review governance contract missing: {expected}")
    for contract in pr_review_contracts:
        cid = contract.get("id")
        require_keys(
            contract,
            [
                "id",
                "owner",
                "applies_to",
                "enabled_default",
                "mode",
                "required_inputs",
                "runner_policy",
                "prompt_injection_controls",
                "publishing_policy",
                "must_not",
            ],
            f"PR review governance contract {cid}",
        )
        if contract.get("enabled_default") is not False:
            fail(f"PR review governance contract {cid} must be disabled by default")
        if len(contract.get("required_inputs", [])) < 5:
            fail(f"PR review governance contract {cid} has too few required inputs")
        if not any("prompt" in item.lower() for item in contract.get("prompt_injection_controls", [])):
            fail(f"PR review governance contract {cid} must include prompt injection controls")
        if cid == "adk-ci-pr-review-runner-v1":
            policy = contract.get("runner_policy", {})
            if policy.get("sandbox") != "workspace-write":
                fail("ADK CI PR review runner must default to workspace-write sandbox")
            if "drop-sudo" not in policy.get("safety_strategy", ""):
                fail("ADK CI PR review runner must require drop-sudo or equivalent")
            if not any("structured output" in item.lower() for item in contract.get("publishing_policy", [])):
                fail("ADK CI PR review runner publishing policy must require structured output validation")
        if cid == "untrusted-pr-isolation-v1":
            policy = contract.get("runner_policy", {})
            if "fork pull_request" not in policy.get("untrusted_events", []):
                fail("untrusted PR isolation must include fork pull_request")
            if "no protected LLM provider key exposure" not in policy.get("default_for_untrusted", ""):
                fail("untrusted PR isolation must deny protected LLM provider key exposure")
        if cid == "inline-review-anchoring-v1":
            policy = contract.get("runner_policy", {})
            for case in ("new file", "modified file", "renamed file", "deleted file", "multi-line finding"):
                if case not in policy.get("anchoring_cases_to_test", []):
                    fail(f"inline review anchoring missing test case: {case}")
            if not any("right-side diff" in item for item in contract.get("publishing_policy", [])):
                fail("inline review anchoring must require right-side diff validation")
    pr_review_gate = pr_review.get("quality_gate", {})
    for key in (
        "ci_review_enabled_default_must_be_false",
        "untrusted_pr_must_not_receive_protected_secrets",
        "structured_output_required_for_machine_publishing",
        "inline_comments_require_anchor_validation",
        "ai_review_is_not_human_approval",
    ):
        if pr_review_gate.get(key) is not True:
            fail(f"PR review quality_gate {key} must be true")

    skill_repro_contracts = skill_repro.get("contracts", [])
    if not skill_repro_contracts:
        fail("skill reproducibility contracts are empty")
    skill_repro_ids = {contract.get("id") for contract in skill_repro_contracts}
    for expected in (
        "skill-discoverability-v1",
        "skill-version-pin-v1",
        "cross-harness-skill-invocation-v1",
        "skill-tiny-cli-v1",
        "third-party-skill-domain-policy-v1",
    ):
        if expected not in skill_repro_ids:
            fail(f"skill reproducibility contract missing: {expected}")
    for contract in skill_repro_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "applies_to", "required_fields", "must_not"], f"skill reproducibility contract {cid}")
        if len(contract.get("required_fields", [])) < 5:
            fail(f"skill reproducibility contract {cid} has too few required fields")
        if cid == "skill-discoverability-v1":
            examples = contract.get("routing_examples", {})
            if examples.get("positive_required") is not True or examples.get("negative_required") is not True:
                fail("skill discoverability must require positive and negative examples")
        if cid == "skill-version-pin-v1":
            pinning = contract.get("pinning_policy", {})
            if "pin explicit skill version" not in pinning.get("production", ""):
                fail("skill version pin policy must require explicit production version pin")
        if cid == "skill-tiny-cli-v1":
            execution = contract.get("execution_policy", {})
            if "deterministic" not in execution.get("stdout", ""):
                fail("skill tiny CLI policy must require deterministic stdout")
        if cid == "cross-harness-skill-invocation-v1":
            policy = contract.get("invocation_policy", {})
            if set(policy.get("allowed_modes", [])) != {"implicit", "explicit-only"}:
                fail("cross-harness invocation allowed modes are invalid")
            if policy.get("default_mode") != "implicit":
                fail("cross-harness invocation must default to implicit")
            mappings = contract.get("target_mappings", {})
            if mappings.get("claude-code", {}).get("explicit-only") != "disable-model-invocation: true":
                fail("Claude explicit-only mapping is missing")
            if mappings.get("codex", {}).get("explicit-only") != "policy.allow_implicit_invocation: false":
                fail("Codex explicit-only mapping is missing")
            codex_metadata = contract.get("codex_metadata_contract", {})
            if codex_metadata.get("required_root") != "interface":
                fail("Codex skill metadata must use nested interface root")
            if codex_metadata.get("explicit_true_forbidden") is not True:
                fail("Codex explicit implicit=true output must be forbidden")
        if cid == "third-party-skill-domain-policy-v1":
            for field in ("trust_level", "review_status", "license", "source_revision", "runtime_boundary", "install_scope", "attribution"):
                if field not in contract.get("required_fields", []):
                    fail(f"third-party skill domain policy missing field: {field}")
            trust = contract.get("trust_policy", {})
            if trust.get("default") != "review-required":
                fail("third-party skill domain policy must default to review-required")
    skill_repro_gate = skill_repro.get("quality_gate", {})
    for key in (
        "negative_examples_required_for_routing_changes",
        "production_skill_version_must_be_pinned",
        "scripted_skills_require_deterministic_cli_contract",
        "networked_skills_require_allowlist_and_egress_policy",
        "third_party_skills_default_review_required",
        "cross_harness_invocation_must_be_explicit",
    ):
        if skill_repro_gate.get(key) is not True:
            fail(f"skill reproducibility quality_gate {key} must be true")

    model_records = model_selection.get("records", [])
    if not model_records:
        fail("model selection decision records are empty")
    model_record_ids = {record.get("id") for record in model_records}
    if "adk-model-selection-record-v1" not in model_record_ids:
        fail("model selection decision record missing: adk-model-selection-record-v1")
    for record in model_records:
        rid = record.get("id")
        require_keys(record, ["id", "owner", "applies_to", "required_fields", "quality_gates", "must_not"], f"model selection record {rid}")
        for field in (
            "quality_kpis",
            "service_slos",
            "eval_baseline",
            "version_pinning_strategy",
            "ab_test_plan",
            "rollback_plan",
            "owner_approval",
            "prompt_cache_retention_policy",
            "service_tier_policy",
            "retention_privacy_rationale",
        ):
            if field not in record.get("required_fields", []):
                fail(f"model selection record {rid} missing required field: {field}")
        if not any("retrieved_at" in item or "freshness" in item.lower() or "official model catalog" in item for item in record.get("quality_gates", [])):
            fail(f"model selection record {rid} must require freshness evidence")
        if not any("single informal trial" in item for item in record.get("must_not", [])):
            fail(f"model selection record {rid} must reject single informal trials")
    model_gate = model_selection.get("quality_gate", {})
    for key in (
        "freshness_required_for_model_catalog",
        "kpi_slo_required_before_promotion",
        "eval_baseline_required_before_change",
        "rollback_required_for_default_change",
        "owner_approval_required",
    ):
        if model_gate.get(key) is not True:
            fail(f"model selection quality_gate {key} must be true")

    data_retention_contracts = data_retention.get("contracts", [])
    if not data_retention_contracts:
        fail("data retention contracts are empty")
    data_retention_ids = {contract.get("id") for contract in data_retention_contracts}
    if "api-state-retention-boundary-v1" not in data_retention_ids:
        fail("data retention contract missing: api-state-retention-boundary-v1")
    for contract in data_retention_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "applies_to", "state_classes", "required_fields", "quality_gates", "must_not"], f"data retention contract {cid}")
        state_classes = set(contract.get("state_classes", []))
        for state_class in (
            "persistent_application_state",
            "temporary_background_state",
            "third_party_mcp_state",
            "hosted_container_state",
            "prompt_cache_state",
            "client_retained_encrypted_state",
            "no_retention_store_false",
        ):
            if state_class not in state_classes:
                fail(f"data retention contract {cid} missing state class: {state_class}")
        required_fields = set(contract.get("required_fields", []))
        for field in (
            "store_policy",
            "retention_duration",
            "zdr_behavior",
            "background_mode_policy",
            "third_party_retention_policy",
            "hosted_container_lifecycle",
            "prompt_cache_retention_policy",
        ):
            if field not in required_fields:
                fail(f"data retention contract {cid} missing required field: {field}")
    data_retention_gate = data_retention.get("quality_gate", {})
    for key in (
        "retention_policy_required",
        "zdr_store_false_required",
        "third_party_mcp_retention_required",
        "hosted_container_lifecycle_required",
        "owner_approval_required_for_persistent_state",
    ):
        if data_retention_gate.get(key) is not True:
            fail(f"data retention quality_gate {key} must be true")

    prompt_cache_contracts = prompt_cache.get("contracts", [])
    if not prompt_cache_contracts:
        fail("prompt cache contracts are empty")
    prompt_cache_ids = {contract.get("id") for contract in prompt_cache_contracts}
    if "prompt-cache-retention-policy-v1" not in prompt_cache_ids:
        fail("prompt cache contract missing: prompt-cache-retention-policy-v1")
    for contract in prompt_cache_contracts:
        cid = contract.get("id")
        require_keys(contract, ["id", "owner", "applies_to", "required_fields", "allowed_retention_policies", "quality_gates", "must_not"], f"prompt cache contract {cid}")
        required_fields = set(contract.get("required_fields", []))
        for field in (
            "prompt_cache_key_strategy",
            "stable_prefix_boundary",
            "dynamic_tail_boundary",
            "retention_policy",
            "model_support_source",
            "cached_token_metric",
            "privacy_boundary",
        ):
            if field not in required_fields:
                fail(f"prompt cache contract {cid} missing required field: {field}")
        allowed_policies = set(contract.get("allowed_retention_policies", []))
        for policy in ("in_memory", "24h", "model_default"):
            if policy not in allowed_policies:
                fail(f"prompt cache contract {cid} missing allowed retention policy: {policy}")
        gate_text = " ".join(contract.get("quality_gates", [])).lower()
        for token in ("stable prefix", "dynamic tail", "model support", "freshness"):
            if token not in gate_text:
                fail(f"prompt cache contract {cid} quality gates must mention {token}")
    prompt_cache_gate = prompt_cache.get("quality_gate", {})
    for key in (
        "stable_dynamic_boundary_required",
        "retention_policy_required",
        "model_support_freshness_required",
        "cache_miss_must_be_behavior_preserving",
        "cached_token_metric_observation_only",
    ):
        if prompt_cache_gate.get(key) is not True:
            fail(f"prompt cache quality_gate {key} must be true")

    surface_terms = codex_surface_terms.get("terms", [])
    if not surface_terms:
        fail("Codex surface terms are empty")
    surface_terms_by_name = {term.get("official_term"): term for term in surface_terms}
    surface_gate = codex_surface_terms.get("quality_gate", {})
    require_keys(surface_gate, ["required_terms", "must_not"], "Codex surface terms quality_gate")
    for term_name in ("Agent", "Skill", "Plugin", "MCP server", "Automation", "Subagent", "Worktree", "Permission profile"):
        if term_name not in surface_terms_by_name:
            fail(f"Codex surface term missing: {term_name}")
        if term_name not in surface_gate.get("required_terms", []):
            fail(f"Codex surface terms quality_gate missing required term: {term_name}")
    for term in surface_terms:
        tid = term.get("official_term")
        require_keys(term, ["official_term", "adk_term", "surface", "definition_boundary", "adk_usage"], f"Codex surface term {tid}")
        if not isinstance(term.get("surface"), list) or not term.get("surface"):
            fail(f"Codex surface term {tid} must define non-empty surface list")
    if not any("workflow" in item.lower() and "agent" in item.lower() for item in surface_gate.get("must_not", [])):
        fail("Codex surface terms must forbid calling every workflow an agent")
    if not any("plugin" in item.lower() and "installable" in item.lower() for item in surface_gate.get("must_not", [])):
        fail("Codex surface terms must distinguish plugin from non-installable skills")

    doc_text = doc.read_text(encoding="utf-8") if doc.is_file() else ""
    for marker in ("P0", "P1", "P2", "developers.openai.com", "Non-Goals", "structured outputs", "tool-search", "automation", "CI/PR review", "skill version", "Model selection", "Guardrail", "Stored-session", "Data retention", "Prompt cache retention", "ZDR", "Codex glossary", "permission profile", "memory runtime"):
        if marker not in doc_text:
            fail(f"reference doc missing marker: {marker}")
    locals_copy = locals()
    context.bindings.update({name: locals_copy[name] for name in ["data_retention_contracts","model_records","pr_review_contracts","prompt_cache_contracts","skill_repro_contracts","surface_terms"] if name in locals_copy})
