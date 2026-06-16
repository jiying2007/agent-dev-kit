#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" >/dev/null
"$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --summary-json | rg -q '"status":"pass"'
"$ROOT_DIR/scripts/devkit.sh" openai-runtime-capabilities --summary-json | rg -q '"failures":0'

echo "[PASS] OpenAI runtime capability gates test"
