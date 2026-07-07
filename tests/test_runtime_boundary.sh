#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-runtime-boundary.sh"

summary="$("$ROOT_DIR/scripts/check-runtime-boundary.sh" --summary-json)"
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] runtime boundary summary did not pass" >&2
  exit 1
}
echo "$summary" | grep -q '"runtime_scope":"generic-adk"' || {
  echo "[FAIL] runtime boundary summary missing generic scope" >&2
  exit 1
}
echo "$summary" | grep -q '"direct_tool_targets":3' || {
  echo "[FAIL] runtime boundary summary missing direct tool target count" >&2
  exit 1
}
echo "$summary" | grep -q '"external_handoff_targets":1' || {
  echo "[FAIL] runtime boundary summary missing external handoff target count" >&2
  exit 1
}
echo "$summary" | grep -q '"codex_direct_tool_target":false' || {
  echo "[FAIL] runtime boundary summary must keep Codex out of direct tool targets" >&2
  exit 1
}
echo "$summary" | grep -q '"codex_handoff_mode":"source-to-live"' || {
  echo "[FAIL] runtime boundary summary missing Codex source-to-live handoff mode" >&2
  exit 1
}

echo "[PASS] runtime boundary"
