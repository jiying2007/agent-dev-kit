#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
from agent_dev_kit.contracts.schema_loader import validate_packaged_schema_sync

result = validate_packaged_schema_sync(Path(sys.argv[1]))
assert result["status"] == "pass", result
assert result["count"] >= 6, result
assert result["failures"] == [], result
PY

echo '[PASS] packaged schemas are byte-identical to canonical root schemas'
