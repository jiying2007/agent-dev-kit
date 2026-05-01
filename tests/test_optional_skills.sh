#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LIST_OUTPUT="$("$ROOT_DIR/scripts/install_assets.sh" --list-optional-skills)"
echo "$LIST_OUTPUT" | grep -Fxq "incident-rca-report" || {
  echo "[FAIL] optional skill list missing incident-rca-report" >&2
  exit 1
}

TARGET="$TMP_DIR/.codex"
"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --with-optional-skill test-flakiness-triage \
  --with-optional-skill incident-rca-report

[[ -d "$TARGET/skills/test-flakiness-triage" ]] || {
  echo "[FAIL] missing installed optional skill test-flakiness-triage" >&2
  exit 1
}
[[ -d "$TARGET/skills/incident-rca-report" ]] || {
  echo "[FAIL] missing installed optional skill incident-rca-report" >&2
  exit 1
}

echo "[PASS] optional skills"
