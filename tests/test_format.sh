#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-format.sh"

if rg -q --fixed-strings 'manifest.yaml' "$ROOT_DIR/scripts/check-format.sh"; then
  echo "[FAIL] format gate references retired manifest.yaml" >&2
  exit 1
fi
rg -q --fixed-strings 'manifest.json' "$ROOT_DIR/scripts/check-format.sh" || {
  echo "[FAIL] format gate is not bound to manifest.json" >&2
  exit 1
}

echo "[PASS] format"
