#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
from agent_dev_kit.contracts.registry import validate_contract_registry

result = validate_contract_registry(Path(sys.argv[1]))
assert result["status"] == "pass", result
assert result["contract_count"] >= 9, result
assert result["failures"] == [], result
PY

echo '[PASS] versioned contract registry is valid and all registered surfaces exist'
