#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-runtime-boundary.sh [--summary-json]

Checks:
  - Codex declaration root is ~/codex, not ~/.codex.
  - scripts do not install, restore, rollback, copy, remove, or write directly into ~/.codex.
  - active docs/templates/skills do not recommend direct adk-to-~/.codex install commands.
  - read-only health/list references to ~/.codex remain allowed.
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

codex_root="$(adk_get_tool_value "codex" "default_root")"
if [[ "$codex_root" != "~/codex" ]]; then
  record_failure "manifest tool_targets.codex.default_root must be ~/codex, got ${codex_root:-empty}"
fi

if adk_get_tool_list "codex" "detect" | grep -Fxq "~/.codex"; then
  record_failure "manifest tool_targets.codex.detect must not include ~/.codex"
fi

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  record_failure "prohibited direct codex install: $hit"
done < <(
  rg -n 'install-assets\.sh|devkit\.sh install|sync-codex-assets\.sh' "$ROOT_DIR/scripts" \
    | rg -- '--target[ =][^#]*~/.codex|--tool[ =]codex' \
    | rg -v 'codex install is disabled|check-runtime-boundary\.sh' || true
)

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  record_failure "prohibited runtime restore/rollback: $hit"
done < <(
  rg -n 'backup-rollback\.sh[^\n]*(restore|rollback)[^\n]*--target[ =][^#]*~/.codex' "$ROOT_DIR/scripts" || true
)

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  record_failure "prohibited direct runtime mutation: $hit"
done < <(
  rg -n '(^|[[:space:]])(cp|mv|rm|mkdir|ln|rsync|tar)([[:space:]]|$)[^\n]*(~/.codex|\$HOME/\.codex)' "$ROOT_DIR/scripts" \
    | rg -v 'check-runtime-boundary\.sh|check-global-codex-health|codex mcp list|logs' || true
)

while IFS= read -r hit; do
  [[ -z "$hit" ]] && continue
  record_failure "prohibited active doc direct codex install: $hit"
done < <(
  rg -n --pcre2 \
    -g '!reports/archive/**' \
    'devkit\.sh install[^\n]*(--tool[ =]codex|--target[ =][^\n]*~/.codex)|install-assets\.sh[^\n]*--tool[ =]codex|sync-codex-assets\.sh' \
    "$ROOT_DIR/README.md" \
    "$ROOT_DIR/CONTEXT.md" \
    "$ROOT_DIR/docs" \
    "$ROOT_DIR/skills" \
    "$ROOT_DIR/optional-skills" \
    "$ROOT_DIR/templates" || true
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
  printf '{"schema_version":1,"status":"pass","failures":0,"codex_root":"~/codex"}\n'
else
  echo "[PASS] runtime boundary check"
fi
