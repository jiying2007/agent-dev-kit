#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/convert_assets.sh" \
  --target claude-code \
  --profile core \
  --with-optional-skill incident-rca-report \
  --out "$TMP_DIR" \
  --clean

[[ -f "$TMP_DIR/claude-code/agent/requirements-analyst.md" ]] || { echo "[FAIL] missing converted agent" >&2; exit 1; }
[[ -f "$TMP_DIR/claude-code/skill/requirements-triage.md" ]] || { echo "[FAIL] missing converted skill" >&2; exit 1; }
[[ -f "$TMP_DIR/claude-code/skill/incident-rca-report.md" ]] || { echo "[FAIL] missing converted optional skill" >&2; exit 1; }

grep -q '^target: claude-code$' "$TMP_DIR/claude-code/agent/requirements-analyst.md" || {
  echo "[FAIL] converted metadata missing" >&2
  exit 1
}

echo "[PASS] convert"
