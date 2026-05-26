#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-runtime-boundary.sh [--summary-json]

Checks:
  - generic ADK does not declare a Codex-specific tool target
  - generic ADK scripts and tests do not expose Codex-specific commands
  - legacy Codex handoff scripts are removed
USAGE
}

SUMMARY_JSON=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

failures=()

record_failure() {
  failures+=("$1")
}

if adk_tool_exists "codex"; then
  record_failure "manifest tool_targets must not include codex"
fi

for stale in \
  "$ROOT_DIR/scripts/check-codex-handoff.sh" \
  "$ROOT_DIR/scripts/sync-codex-assets.sh" \
  "$ROOT_DIR/tests/test_convert_codex_handoff.sh"; do
  if [[ -e "$stale" ]]; then
    record_failure "stale Codex-bound file must be removed: ${stale#$ROOT_DIR/}"
  fi
done

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  record_failure "Codex-bound residue in active runtime surface: $hit"
done < <(
  rg -n 'codex|Codex|\.codex|~/codex' \
    "$ROOT_DIR/manifest.yaml" \
    "$ROOT_DIR/scripts" \
    "$ROOT_DIR/tests" \
    -g '!check-runtime-boundary.sh' \
    -g '!check-openai-developers-governance.sh' || true
)

if [[ "${#failures[@]}" -gt 0 ]]; then
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    printf '{"schema_version":1,"status":"fail","failures":%s}\n' "${#failures[@]}"
  else
    echo "[FAIL] runtime boundary check failed" >&2
    printf '  - %s\n' "${failures[@]}" >&2
  fi
  exit 1
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"pass","failures":0,"runtime_scope":"generic-adk"}\n'
else
  echo "[PASS] runtime boundary check"
fi
