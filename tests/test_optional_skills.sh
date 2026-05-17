#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

LIST_OUTPUT="$("$ROOT_DIR/scripts/install-assets.sh" --list-optional-skills)"
echo "$LIST_OUTPUT" | grep -Fxq "adk-incident-rca-report" || {
  echo "[FAIL] optional skill list missing adk-incident-rca-report" >&2
  exit 1
}
if echo "$LIST_OUTPUT" | grep -Fxq "adk-artifact-gated-lite"; then
  echo "[FAIL] removed optional skill still listed: adk-artifact-gated-lite" >&2
  exit 1
fi

TARGET="$TMP_DIR/.codex"
"$ROOT_DIR/scripts/install-assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --with-optional-skill adk-test-flakiness-triage \
  --with-optional-skill adk-incident-rca-report

[[ -d "$TARGET/skills/adk-test-flakiness-triage" ]] || {
  echo "[FAIL] missing installed optional skill adk-test-flakiness-triage" >&2
  exit 1
}
[[ -d "$TARGET/skills/adk-incident-rca-report" ]] || {
  echo "[FAIL] missing installed optional skill adk-incident-rca-report" >&2
  exit 1
}
echo "[PASS] optional skills"
