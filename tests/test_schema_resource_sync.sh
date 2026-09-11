#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import shutil
import sys
import tempfile
from pathlib import Path

from agent_dev_kit.contracts.schema_loader import sync_packaged_schemas, validate_packaged_schema_sync

root = Path(sys.argv[1])
result = validate_packaged_schema_sync(root)
assert result["status"] == "pass", result
assert result["count"] >= 6, result
assert result["changed"] == [], result
assert result["failures"] == [], result

with tempfile.TemporaryDirectory() as temp:
    fixture = Path(temp)
    shutil.copytree(root / "schemas", fixture / "schemas")
    shutil.copytree(
        root / "src" / "agent_dev_kit" / "schema_resources",
        fixture / "src" / "agent_dev_kit" / "schema_resources",
    )
    mirror = fixture / "src" / "agent_dev_kit" / "schema_resources" / "evidence-envelope-v1.schema.json"
    canonical = fixture / "schemas" / "evidence-envelope-v1.schema.json"
    mirror.write_text(mirror.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    drift = validate_packaged_schema_sync(fixture)
    assert drift["status"] == "fail", drift
    assert any("packaged schema drift" in item for item in drift["failures"]), drift

    repaired = sync_packaged_schemas(fixture, write=True)
    assert repaired["status"] == "pass", repaired
    assert repaired["changed"] == ["evidence-envelope-v1.schema.json"], repaired
    assert mirror.read_bytes() == canonical.read_bytes()
    assert validate_packaged_schema_sync(fixture)["status"] == "pass"
PY

python3 -m agent_dev_kit.contracts.schema_sync --root "$ROOT" --check --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["mode"]=="check", d'

echo '[PASS] packaged schemas are generated/checkable mirrors of canonical root schemas'
