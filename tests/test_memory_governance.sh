#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-memory-governance.sh" >/dev/null
"$ROOT_DIR/scripts/validate-assets.sh" --strict >/dev/null

echo "[PASS] memory governance test"
