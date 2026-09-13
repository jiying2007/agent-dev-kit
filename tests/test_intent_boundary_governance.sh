#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if rg -n "adk-task-package-schema-v1" \
  "$ROOT_DIR/skills" \
  "$ROOT_DIR/optional-skills" \
  "$ROOT_DIR/agents" \
  "$ROOT_DIR/manifests" \
  "$ROOT_DIR/scripts" \
  "$ROOT_DIR/templates"; then
  echo "[FAIL] active asset still references adk-task-package-schema-v1" >&2
  exit 1
fi

for marker in base_ref history_window selected_hotspots first_order_dependencies broad_scan expansion_reason; do
  rg -q "$marker" "$ROOT_DIR/agents/architecture-planner/AGENTS.md" || {
    echo "[FAIL] architecture hotspot contract missing: $marker" >&2
    exit 1
  }
done

[[ -f "$ROOT_DIR/templates/artifacts/prototype-evidence-template.md" ]]
rg -q "adk-prototype-evidence-schema-v1" "$ROOT_DIR/templates/artifacts/prototype-evidence-template.md"

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import copy
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

import yaml

from agent_dev_kit.intent_boundary import (
    PROTOTYPE_EVIDENCE_SCHEMA,
    TASK_PACKAGE_SCHEMA,
    validate_prototype_evidence,
    validate_task_package,
)
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.targets import TargetUsageError, _render_main, load_target_contract

root = Path(sys.argv[1]).resolve()

research = {
    "structured_output_schema": TASK_PACKAGE_SCHEMA,
    "strict_schema_decision": True,
    "refusal_handling": "blocked or replan",
    "goal": "Resolve one source question",
    "context": "Pinned source snapshot",
    "constraints": ["read-only"],
    "done_when": ["evidence reviewed"],
    "primary_action": "research",
    "action_mode": "read-only",
    "verification": ["source citation exists"],
    "artifacts": ["research-note.md"],
    "blockers": ["source unavailable"],
    "work_item_kind": "research",
    "question_to_resolve": "What changed?",
    "evidence_required": ["commit diff"],
    "implementation_permission": "forbidden",
    "exit_gate": "evidence-reviewed",
    "handoff_target": "planning",
    "retention_decision": "keep-final",
}
assert validate_task_package(research) == (), validate_task_package(research)

write_enabled_research = dict(research, implementation_permission="approved")
assert any("requires implementation_permission=forbidden" in item for item in validate_task_package(write_enabled_research))
assert any("evidence_required must be a non-empty array" in item for item in validate_task_package(dict(research, evidence_required=[])))

prototype_task = dict(
    research,
    work_item_kind="prototype",
    primary_action="prototype",
    exit_gate="prototype-reviewed",
    artifacts=["prototype_evidence:prototype-evidence.md"],
)
assert validate_task_package(prototype_task) == (), validate_task_package(prototype_task)
assert any(
    "prototype requires a prototype_evidence artifact" in item
    for item in validate_task_package(dict(prototype_task, artifacts=["prototype.bin"]))
)
assert any(
    "prototype requires a prototype_evidence artifact" in item
    for item in validate_task_package(dict(prototype_task, artifacts=["not_prototype_evidence:fake.md"]))
)

implementation = dict(
    research,
    work_item_kind="implementation",
    primary_action="implement",
    action_mode="workspace-write",
    implementation_permission="approved",
    exit_gate="implementation-verified",
)
assert validate_task_package(implementation) == (), validate_task_package(implementation)
assert validate_task_package(dict(research, structured_output_schema="adk-task-package-schema-v1"))

prototype_evidence = {
    "structured_output_schema": PROTOTYPE_EVIDENCE_SCHEMA,
    "question": "Does the interface preserve the invariant?",
    "base_commit": "9603c1cc8118d08bc1b3bf34cf714f62178dea3b",
    "scope": "isolated fixture",
    "artifact_path": "docs/changes/example/prototype.bin",
    "artifact_sha256": "a" * 64,
    "runtime_assumptions": "local deterministic fixture",
    "observed_result": "invariant preserved",
    "decision_supported": True,
    "verification_command": "run isolated fixture",
    "verification_exit_code": 0,
    "retention_decision": "expire",
    "expires_at": "2026-08-19",
    "cleanup_owner": "test-owner",
    "rollback_anchor": "delete isolated fixture",
    "active_references_absent": True,
}
assert validate_prototype_evidence(prototype_evidence, as_of=date(2026, 7, 19)) == ()
bad_evidence = dict(prototype_evidence, artifact_sha256="bad", expires_at="2026-07-18")
errors = validate_prototype_evidence(bad_evidence, as_of=date(2026, 7, 19))
assert any("artifact_sha256" in item for item in errors), errors
assert any("future expires_at" in item for item in errors), errors
path_errors = validate_prototype_evidence(dict(prototype_evidence, artifact_path="../prototype.bin"))
assert any("repository-relative" in item for item in path_errors), path_errors
commit_errors = validate_prototype_evidence(dict(prototype_evidence, base_commit="main"))
assert any("base_commit" in item for item in commit_errors), commit_errors
exit_errors = validate_prototype_evidence(dict(prototype_evidence, verification_exit_code=True))
assert any("verification_exit_code" in item for item in exit_errors), exit_errors
orphan_errors = validate_prototype_evidence(
    dict(prototype_evidence, retention_decision="delete-orphan", active_references_absent=False)
)
assert any("active_references_absent=true" in item for item in orphan_errors), orphan_errors

data = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
manifest = Manifest(root, data, root / "manifest.json")
skill = next(item for item in manifest.all_assets("skill") if item.name == "adk-requirements-triage")
assert manifest.skill_invocation_mode(skill) == "implicit"

bad_data = copy.deepcopy(data)
bad_data["skill_invocation"]["overrides"] = {"missing-skill": "explicit-only"}
bad_manifest = Manifest(root, bad_data, root / "manifest.json")
assert any("unknown skills" in item for item in bad_manifest.validate())

explicit_data = copy.deepcopy(data)
explicit_data["skill_invocation"]["overrides"] = {"adk-requirements-triage": "explicit-only"}
explicit_manifest = Manifest(root, explicit_data, root / "manifest.json")
explicit_skill = next(
    item for item in explicit_manifest.all_assets("skill") if item.name == "adk-requirements-triage"
)
claude_contract = load_target_contract(explicit_manifest, "claude-code")
rendered = _render_main(explicit_manifest, claude_contract, explicit_skill)
_, frontmatter, _ = rendered.content.decode("utf-8").split("---", 2)
metadata = yaml.safe_load(frontmatter)
assert metadata["disable-model-invocation"] is True, metadata

opencode_contract = load_target_contract(explicit_manifest, "opencode")
try:
    _render_main(explicit_manifest, opencode_contract, explicit_skill)
except TargetUsageError as exc:
    assert "unsupported_skill_invocation_mode" in str(exc), exc
else:
    raise AssertionError("OpenCode explicit-only mapping must fail closed")

with tempfile.TemporaryDirectory(prefix="adk-legacy-target-") as temp:
    legacy_root = Path(temp)
    contracts_dir = legacy_root / "manifests/target-contracts"
    contracts_dir.mkdir(parents=True)
    target_schema = json.loads((root / "manifests/target-contract.schema.json").read_text(encoding="utf-8"))
    target_schema["required"].remove("skill_invocation")
    target_schema["properties"].pop("skill_invocation")
    (legacy_root / "manifests/target-contract.schema.json").write_text(
        json.dumps(target_schema), encoding="utf-8"
    )
    legacy_contract = json.loads(
        (root / "manifests/target-contracts/claude-code.json").read_text(encoding="utf-8")
    )
    legacy_contract.pop("skill_invocation")
    (contracts_dir / "claude-code.json").write_text(json.dumps(legacy_contract), encoding="utf-8")
    legacy_manifest = Manifest(legacy_root, data, legacy_root / "manifest.json")
    try:
        load_target_contract(legacy_manifest, "claude-code")
    except ManifestError as exc:
        assert "target_contract_incompatible" in str(exc), exc
    else:
        raise AssertionError("legacy target contract did not fail with a governed migration error")

release_source = (root / "src/agent_dev_kit/release.py").read_text(encoding="utf-8")
release_artifacts_source = (
    root / "src/agent_dev_kit/distribution/release_artifacts.py"
).read_text(encoding="utf-8")
release_boundary_source = release_source + release_artifacts_source
assert "enforce_current_contract=False" in release_boundary_source
assert 'return "target-contract-hard-cut"' in release_boundary_source
assert "_previous_release_migration(exc)" in release_boundary_source
PY

"$ROOT_DIR/scripts/check-official-docs-governance.sh" >/dev/null
echo "[PASS] intent boundary governance"
