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
  - Codex support is declared only as an external source-to-live handoff
  - reference sources cannot imply runtime enablement
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

mapfile -t external_targets < <(adk_list_external_handoff_target_names)
for external_target in "${external_targets[@]}"; do
  if adk_tool_exists "$external_target"; then
    record_failure "external_handoff_targets must not duplicate direct tool target: $external_target"
  fi

  external_runtime="$(adk_get_external_handoff_target_value "$external_target" "runtime")"
  if [[ -n "$external_runtime" ]] && adk_tool_exists "$external_runtime"; then
    record_failure "external handoff runtime must not duplicate direct tool target: $external_target -> $external_runtime"
  fi

  direct_flag="$(adk_get_external_handoff_target_value "$external_target" "direct_tool_target")"
  if [[ "$direct_flag" != "false" ]]; then
    record_failure "external handoff target must declare direct_tool_target: false: $external_target"
  fi
done

if ! adk_external_handoff_target_exists "codex"; then
  record_failure "manifest external_handoff_targets must declare codex as non-direct source-to-live target"
else
  codex_mode="$(adk_get_external_handoff_target_value "codex" "handoff_mode")"
  codex_direct="$(adk_get_external_handoff_target_value "codex" "direct_tool_target")"
  codex_chain="$(adk_get_external_handoff_target_value "codex" "handoff_chain")"

  [[ "$codex_mode" == "source-to-live" ]] || record_failure "codex external handoff must use source-to-live mode"
  [[ "$codex_direct" == "false" ]] || record_failure "codex external handoff must not be a direct tool target"
  [[ "$codex_chain" == *"~/codex"* && "$codex_chain" == *"~/.codex"* ]] || record_failure "codex external handoff must document ~/codex -> ~/.codex chain"

  for guard in direct-write-live-home direct-convert-target implicit-tool-target; do
    if ! adk_get_external_handoff_target_list "codex" "must_not" | grep -Fxq "$guard"; then
      record_failure "codex external handoff missing must_not guard: $guard"
    fi
  done
fi

mapfile -t reference_sources < <(adk_list_reference_source_names)
for source in "${reference_sources[@]}"; do
  runtime_enablement="$(adk_get_reference_source_value "$source" "runtime_enablement")"
  if [[ "$runtime_enablement" != "false" ]]; then
    record_failure "reference source must not enable runtime behavior: $source"
  fi
done

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
    "$ROOT_DIR/scripts" \
    "$ROOT_DIR/tests" \
    -g '!check-runtime-boundary.sh' \
    -g '!check-openai-developers-governance.sh' \
    -g '!check-openai-runtime-capabilities.sh' \
    -g '!validate-assets.sh' \
    -g '!test_runtime_boundary.sh' || true
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
  printf '{"schema_version":1,"status":"pass","failures":0,"runtime_scope":"generic-adk","direct_tool_targets":%s,"external_handoff_targets":%s,"codex_direct_tool_target":false,"codex_handoff_mode":"source-to-live"}\n' \
    "$(adk_list_tool_names | awk 'END {print NR+0}')" \
    "$(adk_list_external_handoff_target_names | awk 'END {print NR+0}')"
else
  echo "[PASS] runtime boundary check"
fi
