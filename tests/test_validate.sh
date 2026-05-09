#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/validate-assets.sh" --strict
"$ROOT_DIR/scripts/validate-assets.sh" --quick

echo "[PASS] validate"
