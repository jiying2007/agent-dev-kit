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
routing = next(item for item in registry["contracts"] if item["id"] == "routing-intent")
assert routing["producer"] == "agent_dev_kit.matcher_vnext", routing

phase = next(item for item in registry["contracts"] if item["id"] == "phase-context")
assert phase["version"] == "2", phase
assert phase["schema_path"] == "schemas/phase-context-contract-v2.schema.json", phase
assert phase["surface_path"] == "manifests/phase_context_contract_v2.json", phase
assert phase["compatibility"] == "hard-cut", phase

relationships = next(item for item in registry["contracts"] if item["id"] == "skill-relationships")
assert relationships["version"] == "2", relationships
assert relationships["schema_path"] == "schemas/skill-relationship-contract-v2.schema.json", relationships
assert relationships["surface_path"] == "manifests/skill_relationship_contracts_v2.json", relationships
assert relationships["compatibility"] == "hard-cut", relationships

runtime = next(item for item in registry["contracts"] if item["id"] == "runtime-control-decision")
assert runtime["producer"] == "agent_dev_kit.execution_policy", runtime

project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
scripts = project["project"]["scripts"]
assert scripts == {"adk": "agent_dev_kit.cli:main"}, scripts

schema = json.loads((root / "schemas" / "contract-registry-v1.schema.json").read_text(encoding="utf-8"))
invalid = {
    "schema": "adk-contract-registry/v1",
    "contracts": [{
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
    }],
}
assert list(Draft202012Validator(schema).iter_errors(invalid))
PY

python3 -m unittest tests.test_phase_context tests.test_skill_relationships -v

"$ROOT/scripts/devkit.sh" phase-context --domain general --phase review --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["schema"]=="adk-phase-context-resolution/v2"; rows={x["name"]:x for x in d["skills"]}; assert rows["adk-code-review-loop"]["runtime_role"]=="primary" and rows["adk-chinese-code-review"]["runtime_role"]=="supporting", d'

"$ROOT/scripts/devkit.sh" phase-context --lifecycle --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["schema"]=="adk-delivery-lifecycle-resolution/v2"; assert [x["stage"] for x in d["steps"]]==["review","completion","commit-pr","closeout"], d'

"$ROOT/scripts/devkit.sh" skill-relationships --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["schema"]=="adk-skill-relationship-resolution/v2"; assert d["relationship_count"]==len(d["typed_relationships"]) and any(x["type"]=="context-prerequisite" for x in d["typed_relationships"]), d'

match_out="$("$ROOT/scripts/devkit.sh" match --text "代码审查")"
[[ "$match_out" == *"skill=adk-code-review-loop"* ]]
[[ "$match_out" == *"selection_group=code-review"* ]]

echo '[PASS] v2 semantic contracts + single canonical ADK CLI are fail-closed'
