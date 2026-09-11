#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from agent_dev_kit.contracts.registry import validate_contract_registry

root = Path(sys.argv[1])
result = validate_contract_registry(root)
assert result["status"] == "pass", result
assert result["contract_count"] >= 9, result
assert result["failures"] == [], result

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

echo '[PASS] versioned contract registry requires a real schema or surface path'
