#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT_DIR/manifests/adk_goal_contracts.json"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-goal-contracts.sh [--summary-json]

Checks ADK goal contracts:
  - contract JSON is valid and platform-neutral
  - each profile and workflow reference resolves through manifest.yaml
  - each required evidence path exists
  - each goal declares success criteria, non-goals, evidence, workflows, budget, and owner
USAGE
}

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
      usage >&2
      exit 1
      ;;
  esac
done

# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"
adk_require_manifest

failures=()
checked=0

record_failure() {
  failures+=("$1")
}

require_file() {
  local rel="$1"
  checked=$((checked + 1))
  [[ -f "$ROOT_DIR/$rel" ]] || record_failure "missing file: $rel"
}

require_text() {
  local pattern="$1"
  local label="$2"
  checked=$((checked + 1))
  if ! rg -q -- "$pattern" "$MANIFEST"; then
    record_failure "goal contract missing ${label}: ${pattern}"
  fi
}

extract_values() {
  local key="$1"
  rg -o "\"${key}\": \"[^\"]+\"" "$MANIFEST" | sed "s/.*\"${key}\": \"//; s/\"$//" | sort -u
}

require_file "manifests/adk_goal_contracts.json"
if [[ -f "$MANIFEST" ]]; then
  checked=$((checked + 1))
  if ! python3 -m json.tool "$MANIFEST" >/dev/null; then
    record_failure "invalid json: manifests/adk_goal_contracts.json"
  fi
fi

for token in \
  scope_model \
  platform-neutral-adk-goals \
  required_goal_fields \
  goal_id \
  success_criteria \
  non_goals \
  required_evidence \
  primary_workflows \
  performance_budget \
  maintenance_owner; do
  require_text "$token" "required token"
done

goal_count="$(rg -c '"goal_id":' "$MANIFEST" || true)"
checked=$((checked + 1))
if [[ "$goal_count" -lt 4 ]]; then
  record_failure "expected at least 4 goals, got $goal_count"
fi

for profile in $(extract_values profile); do
  checked=$((checked + 1))
  adk_profile_exists "$profile" || record_failure "unknown profile: $profile"
done

for workflow in $(extract_values workflow); do
  checked=$((checked + 1))
  adk_list_manifest_names workflows | grep -Fxq "$workflow" || record_failure "unknown workflow: $workflow"
done

while IFS= read -r path; do
  [[ -n "$path" ]] || continue
  require_file "$path"
done < <(extract_values path)

for forbidden in '/home/'; do
  checked=$((checked + 1))
  if rg -q -- "$forbidden" "$MANIFEST"; then
    record_failure "goal contract must not include live/private path: $forbidden"
  fi
done

checked=$((checked + 1))
if ! rg -q '"quick_gate_seconds": [1-9][0-9]*' "$MANIFEST" || ! rg -q '"full_gate_seconds": [1-9][0-9]*' "$MANIFEST"; then
  record_failure "performance budget seconds must be positive numbers"
fi

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"%s","goals":%s,"checked":%s,"failures":%s}\n' \
    "$status" "$goal_count" "$checked" "${#failures[@]}"
else
  if [[ "$status" == "pass" ]]; then
    echo "[PASS] ADK goal contracts goals=$goal_count"
  else
    for failure in "${failures[@]}"; do
      echo "[FAIL] $failure" >&2
    done
  fi
fi

if [[ "$status" != "pass" ]]; then
  exit 1
fi
