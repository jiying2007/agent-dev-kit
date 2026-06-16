#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

"$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" >/dev/null
"$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --summary-json | rg -q '"status":"pass"'
"$ROOT_DIR/scripts/devkit.sh" openai-runtime-capabilities --summary-json | rg -q '"failures":0'

for fixture in "$ROOT_DIR"/fixtures/openai-runtime-capabilities/pass/*.json; do
  "$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --fixture "$fixture" >/dev/null
  "$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --summary-json --fixture "$fixture" | rg -q '"status":"pass"'
done

for fixture in "$ROOT_DIR"/fixtures/openai-runtime-capabilities/fail/*.json; do
  if "$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --fixture "$fixture" >/dev/null 2>&1; then
    echo "[FAIL] negative fixture passed unexpectedly: $fixture" >&2
    exit 1
  fi
  summary="$("$ROOT_DIR/scripts/check-openai-runtime-capabilities.sh" --summary-json --fixture "$fixture" 2>/dev/null || true)"
  printf '%s\n' "$summary" | rg -q '"status":"fail"'
done

echo "[PASS] OpenAI runtime capability gates test"
