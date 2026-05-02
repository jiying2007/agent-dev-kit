#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

EVIDENCE_FILE="$TMP_DIR/evidence.md"

"$ROOT_DIR/scripts/evidence_index.sh" append \
  --file "$EVIDENCE_FILE" \
  --command "bash tests/run_all.sh" \
  --exit-code 0 \
  --summary "all tests passed" \
  --evidence-path "$TMP_DIR/verify-report.md" \
  --layer Workflow \
  --artifact verify-report

grep -q "^## Evidence Index（命令级）" "$EVIDENCE_FILE" || { echo "[FAIL] missing evidence section" >&2; exit 1; }
grep -q "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |" "$EVIDENCE_FILE" || { echo "[FAIL] missing evidence header" >&2; exit 1; }
grep -q "| bash tests/run_all.sh | 0 | all tests passed |" "$EVIDENCE_FILE" || { echo "[FAIL] missing evidence row" >&2; exit 1; }

if "$ROOT_DIR/scripts/evidence_index.sh" append \
  --file "$EVIDENCE_FILE" \
  --command "bad" \
  --exit-code nope \
  --summary "bad" \
  --evidence-path "$TMP_DIR/bad.md" \
  --layer Workflow >/dev/null 2>&1; then
  echo "[FAIL] invalid exit-code should fail" >&2
  exit 1
fi

echo "[PASS] evidence index"
