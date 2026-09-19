#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-official-docs-governance.sh" >/dev/null
"$ROOT_DIR/scripts/check-official-docs-governance.sh" --summary-json | rg -q '"status":"pass"'
bash "$ROOT_DIR/scripts/devkit.sh" validate --strict >/dev/null

python3 - "$ROOT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
data = json.loads((root / "manifests/official_docs_freshness_gates.json").read_text(encoding="utf-8"))
providers = data["provider_requirements"]
assert set(providers) == {"anthropic", "openai"}
assert providers["anthropic"]["minimum_sources"] >= 5
assert len(providers["anthropic"]["required_source_ids"]) >= 5
assert "code.claude.com" in providers["anthropic"]["allowed_domains"]
assert "www.anthropic.com" in providers["anthropic"]["allowed_domains"]
assert providers["openai"]["minimum_sources"] >= 64
PY

echo "[PASS] official docs governance test"
