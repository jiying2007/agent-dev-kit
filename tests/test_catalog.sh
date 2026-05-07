#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CATALOG_OUT="$TMP_DIR/catalog.md"
"$ROOT_DIR/scripts/catalog_assets.sh" build --out "$CATALOG_OUT"

[[ -f "$CATALOG_OUT" ]] || {
  echo "[FAIL] catalog file not generated" >&2
  exit 1
}

grep -q '^# Agent and Skill Catalog$' "$CATALOG_OUT" || {
  echo "[FAIL] catalog header missing" >&2
  exit 1
}

grep -q '`requirements-analyst`' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing known agent" >&2
  exit 1
}

grep -q '`gdk-incident-rca-report`' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing optional skill" >&2
  exit 1
}

FIND_OUTPUT="$("$ROOT_DIR/scripts/catalog_assets.sh" find --type skill --keyword bring-up)"
echo "$FIND_OUTPUT" | grep -q 'gdk-driver-bringup-checklist' || {
  echo "[FAIL] find command missing expected skill" >&2
  exit 1
}

echo "[PASS] catalog"
