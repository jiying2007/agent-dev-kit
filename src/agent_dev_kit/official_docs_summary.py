"""Official documentation summary checks; read-only owned audit stage."""
from __future__ import annotations

import json
import sys

from .official_docs_context import AuditContext


def check(context: AuditContext) -> None:
    adk_runner_contracts = context.bindings["adk_runner_contracts"]
    automation_contracts = context.bindings["automation_contracts"]
    context_contracts = context.bindings["context_contracts"]
    data_retention_contracts = context.bindings["data_retention_contracts"]
    date_basis_summary = context.bindings["date_basis_summary"]
    docs_tool_targets = context.bindings["docs_tool_targets"]
    evals = context.bindings["evals"]
    failures = context.bindings["failures"]
    hook_events = context.bindings["hook_events"]
    improvement_loops = context.bindings["improvement_loops"]
    marketplace_contracts = context.bindings["marketplace_contracts"]
    mcp = context.bindings["mcp"]
    model_records = context.bindings["model_records"]
    plugin_contracts = context.bindings["plugin_contracts"]
    pr_review_contracts = context.bindings["pr_review_contracts"]
    prompt_cache_contracts = context.bindings["prompt_cache_contracts"]
    rule_contracts = context.bindings["rule_contracts"]
    runtime_api_groups = context.bindings["runtime_api_groups"]
    runtime_layers = context.bindings["runtime_layers"]
    sandbox_presets = context.bindings["sandbox_presets"]
    skill_repro_contracts = context.bindings["skill_repro_contracts"]
    slash = context.bindings["slash"]
    sources = context.bindings["sources"]
    structured_contracts = context.bindings["structured_contracts"]
    subagents = context.bindings["subagents"]
    summary_json = context.bindings["summary_json"]
    surface_terms = context.bindings["surface_terms"]
    today = context.bindings["today"]
    tool_search_contracts = context.bindings["tool_search_contracts"]
    trace_contracts = context.bindings["trace_contracts"]
    worktree_contracts = context.bindings["worktree_contracts"]
    status = "pass" if not failures else "fail"
    if summary_json:
        print(json.dumps({
            "status": status,
            "evaluated_at": today.isoformat(),
            "date_basis": date_basis_summary,
            "official_sources": len(sources),
            "eval_suites": len(evals.get("suites", [])),
            "trace_contracts": len(trace_contracts),
            "mcp_dependencies": len(mcp.get("dependencies", [])),
            "slash_audits": len(slash.get("audits", [])),
            "subagent_contracts": len(subagents.get("contracts", [])),
            "runtime_policy_layers": len(runtime_layers),
            "rules_contracts": len(rule_contracts),
            "runtime_api_groups": len(runtime_api_groups),
            "context_state_contracts": len(context_contracts),
            "docs_mcp_tooling_targets": len(docs_tool_targets),
            "sandbox_presets": len(sandbox_presets),
            "hook_events": len(hook_events),
            "adk_runner_contracts": len(adk_runner_contracts),
            "plugin_contracts": len(plugin_contracts),
            "marketplace_contracts": len(marketplace_contracts),
            "structured_output_contracts": len(structured_contracts),
            "tool_search_contracts": len(tool_search_contracts),
            "automation_contracts": len(automation_contracts),
            "worktree_contracts": len(worktree_contracts),
            "agent_improvement_loops": len(improvement_loops),
            "pr_review_contracts": len(pr_review_contracts),
            "skill_reproducibility_contracts": len(skill_repro_contracts),
            "model_selection_records": len(model_records),
            "data_retention_contracts": len(data_retention_contracts),
            "prompt_cache_contracts": len(prompt_cache_contracts),
            "codex_surface_terms": len(surface_terms),
            "failures": len(failures),
        }, ensure_ascii=False, separators=(",", ":")))
    elif failures:
        for item in failures:
            print(f"[FAIL] {item}", file=sys.stderr)
    else:
        print("[PASS] official docs governance")

    if failures:
        sys.exit(1)
