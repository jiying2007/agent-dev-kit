"""Official documentation sources checks; read-only owned audit stage."""
from __future__ import annotations

import datetime as dt
import re
from urllib.parse import urlparse

from .official_docs_context import AuditContext
from .strict_json import StrictJSONError, read as read_json


def check(context: AuditContext) -> None:
    fail = context.bindings["fail"]
    load_json = context.bindings["load_json"]
    require_file_contains = context.bindings["require_file_contains"]
    require_keys = context.bindings["require_keys"]
    root = context.bindings["root"]
    official = load_json("manifests/official_docs_freshness_gates.json")
    evals = load_json("manifests/eval_suites.json")
    trace = load_json("manifests/trace_eval_contracts.json")
    mcp = load_json("manifests/skill_mcp_dependencies.json")
    slash = load_json("manifests/slash_command_runtime_audits.json")
    subagents = load_json("manifests/subagent_contracts.json")
    runtime_policy = load_json("manifests/adk_runtime_policy_gates.json")
    rules = load_json("manifests/adk_rules_contracts.json")
    runtime_api = load_json("manifests/adk_runtime_api_contracts.json")
    context_state = load_json("manifests/context_state_contracts.json")
    docs_mcp_tooling = load_json("manifests/official_docs_mcp_tooling.json")
    hooks = load_json("manifests/hooks_runtime_audits.json")
    adk_runner = load_json("manifests/adk_runner_contracts.json")
    plugins = load_json("manifests/plugin_marketplace_contracts.json")
    structured_outputs = load_json("manifests/structured_output_contracts.json")
    tool_search = load_json("manifests/tool_search_contracts.json")
    automation_worktree = load_json("manifests/automation_worktree_contracts.json")
    improvement_loop = load_json("manifests/agent_improvement_loop_contracts.json")
    pr_review = load_json("manifests/pr_review_governance_contracts.json")
    skill_repro = load_json("manifests/skill_reproducibility_contracts.json")
    model_selection = load_json("manifests/model_selection_decision_records.json")
    data_retention = load_json("manifests/data_retention_state_contracts.json")
    prompt_cache = load_json("manifests/prompt_cache_policy_contracts.json")
    codex_surface_terms = load_json("manifests/codex_surface_terms.json")

    for manifest_path in sorted((root / "manifests").glob("*.json")):
        try:
            manifest_data = read_json(manifest_path)
        except StrictJSONError as exc:
            fail("invalid manifest JSON: {}: {}".format(manifest_path.name, exc))
            continue
        source_refs = manifest_data.get("source_docs") or manifest_data.get("source_refs") or []
        if not isinstance(source_refs, list):
            continue
        if not any("openai" in str(ref).lower() or "codex" in str(ref).lower() for ref in source_refs):
            continue
        boundary = manifest_data.get("reference_boundary")
        rel_manifest = manifest_path.relative_to(root)
        if not boundary:
            fail(f"{rel_manifest} references OpenAI/Codex sources but lacks reference_boundary")
            continue
        boundary_text = str(boundary).lower()
        if not any(marker in boundary_text for marker in ("citation", "reference", "source docs", "source material")):
            fail(f"{rel_manifest} reference_boundary must state source/reference-only semantics")
        if not any(marker in boundary_text for marker in ("must not", "does not", "not enable", "not make")):
            fail(f"{rel_manifest} reference_boundary must state non-enablement or non-binding semantics")

    doc = root / "docs/reference/openai-developers-reference.md"
    runbook = root / "docs/runbooks/official-docs-governance.md"
    for rel_path in (doc, runbook):
        if not rel_path.is_file():
            fail(f"missing doc: {rel_path.relative_to(root)}")

    execution_layer_markers = {
        "workflows/adk-delivery-gate/WORKFLOW.md": [
            "done-when",
            "replayable-evidence-bundle.md",
            "source-to-live-evidence.md",
            "negative-results",
        ],
        "skills/adk-verification-before-completion/SKILL.md": [
            "Replayable Evidence Bundle",
            "Appshots / UI Evidence Boundary",
            "Runner Smoke Contract",
            "Runtime Control Plane Audit",
            "runtime_config_diff",
            "Trace Eval Regression Evidence",
        ],
        "skills/adk-commit-pr-quality-gate/SKILL.md": [
            "Runtime Control Plane",
            "permission_profile_decision",
            "deny-path test",
        ],
        "skills/adk-requirements-triage/SKILL.md": [
            "Done-when",
            "Required Evidence",
            "Artifact Paths",
            "Blocker Policy",
        ],
        "skills/adk-parallel-agent-governance/SKILL.md": [
            "context_noise_budget",
            "raw_output_retention_decision",
            "parent_merge_policy",
        ],
        "skills/adk-worktree-governance/SKILL.md": [
            "Dirty Worktree Decision",
            "Automation Risk Decision",
            "Heartbeat / Staleness Threshold",
        ],
        "agents/requirements-analyst/AGENTS.md": [
            "done-when",
            "required evidence",
            "artifact paths",
            "blocker policy",
        ],
        "agents/code-review-governor/AGENTS.md": [
            "Completion Claim Audit",
            "Replayable Evidence Bundle",
            "context_noise_budget",
        ],
        "agents/test-validation-engineer/AGENTS.md": [
            "Replayable Evidence Bundle",
            "Appshots/UI evidence boundary",
            "runner smoke contract",
        ],
        "skills/adk-task-breakdown/SKILL.md": [
            "structured_output_schema",
            "strict_schema_decision",
            "adk-task-package-schema-v2",
            "work_item_kind",
            "implementation_permission",
        ],
        "skills/adk-interface-contract-design/SKILL.md": [
            "strict schema",
            "additionalProperties=false",
            "refusal handling",
        ],
        "skills/adk-after-action-review/SKILL.md": [
            "trace-feedback-eval-handoff",
            "sanitized trace",
            "trace_eval_regression_case",
            "human approval",
        ],
        "skills/adk-engineering-growth-review/SKILL.md": [
            "trace-feedback-eval-handoff",
            "eval candidate",
            "human approval",
        ],
        "skills/adk-code-review-loop/SKILL.md": [
            "schema-backed findings",
            "untrusted PR",
            "trace-feedback-eval-handoff",
        ],
        "workflows/skill-curation-delivery/WORKFLOW.md": [
            "plugin-packaging-review.md",
            "hooks: {}",
            "source path containment",
        ],
        "skills/adk-runtime-router/SKILL.md": [
            "skill-catalog-lazy-loading-v1",
            "namespace_summary",
            "loaded_tools",
        ],
        "skills/adk-token-context-governance/SKILL.md": [
            "tool_search_context_contract",
            "deferred_surface",
            "trusted_inventory",
        ],
        "optional-skills/adk-skill-composition-governance/SKILL.md": [
            "skill-catalog-lazy-loading-v1",
            "initial_surface",
            "deferred_surface",
        ],
        "optional-skills/adk-security-supply-chain/SKILL.md": [
            "Runtime Control Plane Audit",
            "mcp_runtime_contract",
            "permission_profile_decision",
        ],
        "workflows/runtime-routing/WORKFLOW.md": [
            "runtime-control-plane-audit",
            "slash_command_runtime_audit",
            "loaded_tools",
        ],
    }
    for rel, markers in execution_layer_markers.items():
        require_file_contains(rel, markers, f"execution-layer contract {rel}")

    review_policy = official.get("review_policy", {})
    date_basis = review_policy.get("date_basis", {})
    require_keys(date_basis, ["kind", "label", "utc_offset"], "official docs date_basis")
    date_basis_label = date_basis.get("label")
    date_basis_offset = date_basis.get("utc_offset")
    offset_match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", str(date_basis_offset))
    if date_basis.get("kind") != "fixed_utc_offset":
        fail("official docs date_basis kind must be fixed_utc_offset")
    if date_basis_label != "Asia/Hong_Kong":
        fail("official docs date_basis label must be Asia/Hong_Kong")
    if offset_match is None:
        fail("official docs date_basis utc_offset must use signed HH:MM")
        governance_timezone = dt.timezone.utc
    else:
        offset_hours = int(offset_match.group(2))
        offset_minutes = int(offset_match.group(3))
        if offset_hours > 23 or offset_minutes > 59:
            fail("official docs date_basis utc_offset is out of range")
            governance_timezone = dt.timezone.utc
        else:
            offset_delta = dt.timedelta(hours=offset_hours, minutes=offset_minutes)
            if offset_match.group(1) == "-":
                offset_delta = -offset_delta
            governance_timezone = dt.timezone(offset_delta)
    today = dt.datetime.now(governance_timezone).date()
    date_basis_summary = f"fixed_utc_offset:{date_basis_offset};label={date_basis_label}"
    allowed_domains = set(review_policy.get("allowed_domains", []))
    adoption_review_policy = official.get("adoption_review_policy", {})
    require_keys(
        adoption_review_policy,
        [
            "linked_matrices",
            "source_expiry_action",
            "missing_review_status_action",
            "missing_target_evidence_action",
            "review_queue_output",
            "required_target_evidence_prefixes",
            "quality_gates",
        ],
        "official docs adoption_review_policy",
    )
    for linked_matrix in (
        "agent-dev-kit/docs/reference-adoption-matrix.md",
        "subrepos/adoption-matrix.jsonl",
    ):
        if linked_matrix not in adoption_review_policy.get("linked_matrices", []):
            fail(f"official docs adoption_review_policy missing linked matrix: {linked_matrix}")
    if adoption_review_policy.get("source_expiry_action") != "needs-review":
        fail("official docs adoption_review_policy source_expiry_action must be needs-review")
    if adoption_review_policy.get("missing_review_status_action") != "fail":
        fail("official docs adoption_review_policy missing_review_status_action must be fail")
    if adoption_review_policy.get("missing_target_evidence_action") != "fail":
        fail("official docs adoption_review_policy missing_target_evidence_action must be fail")
    if adoption_review_policy.get("review_queue_output") != "stdout":
        fail("official docs adoption_review_policy review_queue_output must be stdout")
    if "agent-dev-kit/" not in adoption_review_policy.get("required_target_evidence_prefixes", []):
        fail("official docs adoption_review_policy must require agent-dev-kit/ evidence")
    quality_gates = " ".join(adoption_review_policy.get("quality_gates", [])).lower()
    for marker in ("expired official sources", "targeting agent-dev-kit", "review queue"):
        if marker not in quality_gates:
            fail(f"official docs adoption_review_policy quality_gates missing marker: {marker}")
    sources = official.get("sources", [])
    if not sources:
        fail("official docs source list is empty")

    scopes = set()
    source_ids = set()
    source_domains = {}
    review_status_values = set(official.get("review_policy", {}).get("review_status_values", []))
    max_age_days = official.get("review_policy", {}).get("max_age_days")
    if not isinstance(max_age_days, int) or max_age_days < 1:
        fail("official docs review_policy max_age_days must be a positive integer")
    for source in sources:
        sid = source.get("id", "<missing-id>")
        require_keys(
            source,
            ["id", "title", "url", "retrieved_at", "expires_at", "review_status", "adoption_scope", "owner", "decision", "required_checks"],
            f"official source {sid}",
        )
        if sid in source_ids:
            fail(f"official source id is duplicated: {sid}")
        source_ids.add(sid)
        url = source.get("url", "")
        domain = urlparse(url).netloc
        source_domains[sid] = domain
        if domain not in allowed_domains:
            fail(f"official source {sid} uses non-official domain: {domain}")
        if source.get("review_status") not in review_status_values:
            fail(f"official source {sid} has invalid review_status: {source.get('review_status')}")
        scopes.add(source.get("adoption_scope"))
        expires_at = None
        retrieved_at = None
        try:
            expires_at = dt.date.fromisoformat(source.get("expires_at", ""))
            if expires_at < today:
                fail(f"official source {sid} expired at {expires_at.isoformat()}")
        except ValueError:
            fail(f"official source {sid} has invalid expires_at")
        try:
            retrieved_at = dt.date.fromisoformat(source.get("retrieved_at", ""))
            if retrieved_at > today:
                fail(f"official source {sid} has future retrieved_at: {retrieved_at.isoformat()}")
        except ValueError:
            fail(f"official source {sid} has invalid retrieved_at")
        if expires_at is not None and retrieved_at is not None:
            age_days = (expires_at - retrieved_at).days
            if age_days < 0:
                fail(f"official source {sid} expires before it was retrieved")
            elif isinstance(max_age_days, int) and age_days > max_age_days:
                fail(f"official source {sid} freshness window {age_days} exceeds {max_age_days} days")

    provider_requirements = official.get("provider_requirements", {})
    if set(provider_requirements) != {"anthropic", "openai"}:
        fail("official docs provider_requirements must define exactly anthropic and openai")
    claimed_domains = {}
    for provider, requirement in provider_requirements.items():
        provider_domains = requirement.get("allowed_domains", [])
        minimum_sources = requirement.get("minimum_sources")
        required_source_ids = requirement.get("required_source_ids", [])
        if not provider_domains:
            fail(f"official docs provider {provider} has no allowed_domains")
        if not isinstance(minimum_sources, int) or minimum_sources < 1:
            fail(f"official docs provider {provider} minimum_sources must be a positive integer")
        if not required_source_ids:
            fail(f"official docs provider {provider} has no required_source_ids")
        for domain in provider_domains:
            if domain not in allowed_domains:
                fail(f"official docs provider {provider} domain is not globally allowed: {domain}")
            if domain in claimed_domains:
                fail(f"official docs provider domain {domain} is claimed by both {claimed_domains[domain]} and {provider}")
            claimed_domains[domain] = provider
        provider_source_ids = {
            sid for sid, domain in source_domains.items() if domain in provider_domains
        }
        if isinstance(minimum_sources, int) and len(provider_source_ids) < minimum_sources:
            fail(
                f"official docs provider {provider} has {len(provider_source_ids)} sources; "
                f"minimum is {minimum_sources}"
            )
        for required_sid in required_source_ids:
            if required_sid not in provider_source_ids:
                fail(f"official docs provider {provider} missing required source: {required_sid}")
    unclaimed_domains = allowed_domains - set(claimed_domains)
    if unclaimed_domains:
        fail(f"official docs allowed domains lack provider ownership: {sorted(unclaimed_domains)}")

    for scope in ("P0", "P1", "P2"):
        if scope not in scopes:
            fail(f"official docs adoption scope missing: {scope}")
    locals_copy = locals()
    context.bindings.update({name: locals_copy[name] for name in ["adk_runner","automation_worktree","codex_surface_terms","context_state","data_retention","date_basis_summary","doc","docs_mcp_tooling","evals","hooks","improvement_loop","mcp","model_selection","plugins","pr_review","prompt_cache","rules","runtime_api","runtime_policy","skill_repro","slash","source_ids","sources","structured_outputs","subagents","today","tool_search","trace"] if name in locals_copy})
