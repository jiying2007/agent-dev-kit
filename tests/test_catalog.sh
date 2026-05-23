#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CATALOG_OUT="$TMP_DIR/catalog.md"
"$ROOT_DIR/scripts/catalog-assets.sh" build --out "$CATALOG_OUT"

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

grep -q '| `adk-hardware-debugger` | 硬件问题调试、oops 分析 | `agents/adk-hardware-debugger/AGENTS.md` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing agent description" >&2
  exit 1
}

grep -q '`adk-incident-rca-report`' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing optional skill" >&2
  exit 1
}

FIND_AGENT_OUTPUT="$("$ROOT_DIR/scripts/catalog-assets.sh" find --type agent --keyword 硬件)"
echo "$FIND_AGENT_OUTPUT" | grep -q 'adk-hardware-debugger' || {
  echo "[FAIL] find command missing expected agent" >&2
  exit 1
}

FIND_OUTPUT="$("$ROOT_DIR/scripts/catalog-assets.sh" find --type skill --keyword bring-up)"
echo "$FIND_OUTPUT" | grep -q 'adk-driver-bringup-checklist' || {
  echo "[FAIL] find command missing expected skill" >&2
  exit 1
}

echo "[PASS] catalog"
