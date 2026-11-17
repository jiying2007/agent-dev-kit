"""Probe catalog coverage and distinguish human worker envelopes from typed v2."""

from __future__ import annotations

import json
from pathlib import Path
import re

from agent_dev_kit.catalog_contract import find_rows
from agent_dev_kit.intent_boundary import TASK_PACKAGE_SCHEMA, validate_task_package
from agent_dev_kit.model import Manifest


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
AUDIT = Path("/workspace/scratch/fe8de3b42084/skill-usability-audit/context-optional")
manifest = Manifest.load(ROOT)

catalogs = {kind: find_rows(manifest, kind, "adk")
            for kind in ("skill", "optional-skill", "all")}
for kind, rows in catalogs.items():
    (AUDIT / f"catalog-{kind}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

source = ROOT / "skills/adk-parallel-agent-governance/references/parallel-worktree-task-package.md"
text = source.read_text(encoding="utf-8")
block = re.search(r"(?ms)^```md\n(.*?)^```", text).group(1)
fields = re.findall(r"(?m)^([a-z_]+):", block)

canonical = {
    "structured_output_schema": TASK_PACKAGE_SCHEMA,
    "strict_schema_decision": True,
    "refusal_handling": "BLOCKED if source is unavailable or scope would expand",
    "goal": "Review one immutable source snapshot",
    "context": "Task T1; owner reviewer; primary_skill adk-security-supply-chain; source SHA pinned",
    "constraints": [
        "scope_read: selected source files",
        "scope_write: no repository writes",
        "must_not_touch: runtime credentials and unrelated work",
        "global_constraints: read-only; no remote execution",
        "interfaces: no shared contract changes",
    ],
    "done_when": ["Report evidence and cannot-verify limits; ready_to_handoff only after review"],
    "primary_action": "Review trusted source evidence",
    "action_mode": "read-only",
    "verification": ["Check report paths against the frozen source"],
    "artifacts": ["report.md"],
    "blockers": [],
    "work_item_kind": "research",
    "question_to_resolve": "Is the source compatible with the bounded request?",
    "evidence_required": ["source paths and immutable SHA"],
    "implementation_permission": "forbidden",
    "exit_gate": "evidence-reviewed",
    "handoff_target": "parent reviewer",
    "retention_decision": "keep-final",
}
canonical_errors = validate_task_package(canonical)
if canonical_errors:
    raise RuntimeError(canonical_errors)

filled_envelope = {field: f"example {field}" for field in fields}
for field in set(filled_envelope).intersection(canonical):
    filled_envelope[field] = canonical[field]
filled_envelope.update(
    id="T1", owner="reviewer", scope_read=["selected source files"],
    scope_write=[], must_not_touch=["runtime credentials"],
    global_constraints=["read-only"], interfaces=[], dependencies=[],
    verification_commands=canonical["verification"], ready_to_handoff=False,
)

extra_fields = {
    field: validate_task_package({**canonical, field: value})
    for field, value in {
        "scope_read": ["selected source files"],
        "scope_write": [],
        "global_constraints": ["read-only"],
        "interfaces": [],
        "ready_to_handoff": False,
    }.items()
}

core_names = {line.split("\t")[1] for line in catalogs["skill"][1:]}
optional_names = {line.split("\t")[1] for line in catalogs["optional-skill"][1:]}
expected = {row["name"] for section in ("skills", "optional_skills") for row in manifest.data[section]}
result = {
    "baseline": "78c3be7f6f9b5ee2e557de54156532fb3169198d",
    "catalog": {
        "published_core_query_count": len(core_names),
        "optional_query_count": len(optional_names),
        "omitted_by_published_core_query": sorted(expected - core_names),
        "two_query_union_matches_manifest": core_names | optional_names == expected,
    },
    "task_package": {
        "source": str(source.relative_to(ROOT)),
        "template_is_markdown_human_envelope": True,
        "template_declares_structured_output_schema": "structured_output_schema" in fields,
        "template_fields": fields,
        "direct_field_conversion_errors": validate_task_package(filled_envelope),
        "canonical_control_errors": canonical_errors,
        "extra_top_level_field_errors": extra_fields,
        "canonical_mapping_control": canonical,
        "interpretation": (
            "Direct conversion is incompatible. The reference is Markdown and does not claim "
            "to be a typed JSON payload. This probe alone does not establish a runtime defect; "
            "an explicit mapping note would prevent confusion when a host requires v2."
        ),
    },
}
(AUDIT / "contract-edge-results.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"catalog": result["catalog"],
                  "task_template_fields": len(fields),
                  "direct_v2_errors": result["task_package"]["direct_field_conversion_errors"],
                  "mapped_v2_errors": canonical_errors}, ensure_ascii=False))
