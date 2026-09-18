#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python3 - "$ROOT" <<'PY'
import json
import sys
import tomllib
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_dev_kit.contracts.registry import validate_contract_registry

root = Path(sys.argv[1])
result = validate_contract_registry(root)
assert result["status"] == "pass", result
assert result["contract_count"] >= 11, result
assert result["failures"] == [], result

registry = json.loads((root / "manifests" / "contract_registry.json").read_text(encoding="utf-8"))
phase = next(item for item in registry["contracts"] if item["id"] == "phase-context")
assert phase["producer"] == "agent_dev_kit.phase_context", phase
assert phase["schema_path"] == "schemas/phase-context-contract-v1.schema.json", phase
assert phase["surface_path"] == "manifests/phase_context_contract.json", phase
assert "phase-context" in next(item for item in registry["contracts"] if item["id"] == "skill-content")["consumers"]
relationships = next(item for item in registry["contracts"] if item["id"] == "skill-relationships")
assert relationships["producer"] == "agent_dev_kit.skill_relationships", relationships
assert relationships["schema_path"] == "schemas/skill-relationship-contract-v1.schema.json", relationships
assert relationships["surface_path"] == "manifests/skill_relationship_contracts_v1.json", relationships
skill_content = next(item for item in registry["contracts"] if item["id"] == "skill-content")
assert "skill-relationships" in skill_content["consumers"], skill_content

project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
assert project["project"]["scripts"]["adk-phase-context"] == "agent_dev_kit.phase_context:main", project["project"]["scripts"]
assert project["project"]["scripts"]["adk-skill-relationships"] == "agent_dev_kit.skill_relationships:main", project["project"]["scripts"]

schema = json.loads((root / "schemas" / "contract-registry-v1.schema.json").read_text(encoding="utf-8"))
invalid = {
    "schema": "adk-contract-registry/v1",
    "contracts": [
        {
            "id": "invalid-null-surface",
            "version": "v1",
            "owner": "test",
            "producer": "test",
            "consumers": ["test"],
            "stability": "experimental",
            "compatibility": "strict",
            "schema_path": None,
            "surface_path": None,
            "evidence_class": "source",
        }
    ],
}
errors = list(Draft202012Validator(schema).iter_errors(invalid))
assert errors, "null-only contract surface unexpectedly passed JSON Schema"
PY

python3 -m unittest tests.test_phase_context tests.test_skill_relationships -v

"$ROOT/scripts/devkit.sh" phase-context --domain general --phase review --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["legacy_manifest_context_paths_authoritative"] is False; rows={x["name"]:x for x in d["skills"]}; assert rows["adk-code-review-loop"]["runtime_role"]=="primary" and rows["adk-chinese-code-review"]["runtime_role"]=="supporting", d'

"$ROOT/scripts/devkit.sh" phase-context --lifecycle --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["legacy_manifest_dependencies_authoritative"] is False; assert [x["stage"] for x in d["steps"]]==["review","completion","commit-pr","closeout"], d'

"$ROOT/scripts/devkit.sh" skill-relationships --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["legacy_depends_on_authoritative_for_delivery_sequencing"] is False; assert any(x["type"]=="delivery-precedence" for x in d["typed_relationships"]), d'

echo '[PASS] versioned contract registry + semantic phase/lifecycle resolution are fail-closed'
