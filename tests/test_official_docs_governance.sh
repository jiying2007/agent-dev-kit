#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-official-docs-governance.sh" >/dev/null
"$ROOT_DIR/scripts/check-official-docs-governance.sh" --summary-json | rg -q '"status":"pass"'
"$ROOT_DIR/scripts/validate-assets.sh" --strict >/dev/null

echo "[PASS] official docs governance test"
