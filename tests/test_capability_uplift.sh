#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

bash "$ROOT_DIR/scripts/check-codify-governance.sh"
bash "$ROOT_DIR/scripts/check-knowledge-compile-model.sh"
bash "$ROOT_DIR/scripts/check-reuse-before-rebuild.sh"
bash "$ROOT_DIR/scripts/check-context-experience-patterns.sh"

echo "[PASS] capability uplift"
