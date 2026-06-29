#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST="$ROOT_DIR/manifests/adk_capability_health_contracts.json"
GOAL_MANIFEST="$ROOT_DIR/manifests/adk_goal_contracts.json"
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-capability-health.sh [--summary-json]

Checks ADK capability health:
  - capability JSON is valid
  - referenced goals exist in adk_goal_contracts.json
  - referenced agents, skills, workflows, scripts, tests, and docs resolve
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
    record_failure "capability health missing ${label}: ${pattern}"
  fi
}

extract_values() {
  local key="$1"
  rg -o "\"${key}\": \"[^\"]+\"" "$MANIFEST" | sed "s/.*\"${key}\": \"//; s/\"$//" | sort -u
}

require_file "manifests/adk_capability_health_contracts.json"
require_file "manifests/adk_goal_contracts.json"

if [[ -f "$MANIFEST" ]]; then
  checked=$((checked + 1))
  if ! python3 -m json.tool "$MANIFEST" >/dev/null; then
    record_failure "invalid json: manifests/adk_capability_health_contracts.json"
  fi
fi
if [[ -f "$GOAL_MANIFEST" ]]; then
  checked=$((checked + 1))
  if ! python3 -m json.tool "$GOAL_MANIFEST" >/dev/null; then
    record_failure "invalid json: manifests/adk_goal_contracts.json"
  fi
fi

for token in \
  scope_model \
  goal-to-capability-health \
  required_capability_fields \
  capability_id \
  goal_id \
  agent \
  skill \
  workflow \
  script \
  test \
  doc; do
  require_text "$token" "required token"
done

capability_count="$(rg -c '"capability_id":' "$MANIFEST" || true)"
checked=$((checked + 1))
if [[ "$capability_count" -lt 6 ]]; then
  record_failure "expected at least 6 capabilities, got $capability_count"
fi

for goal_id in $(extract_values goal_id); do
  checked=$((checked + 1))
  if ! rg -q "\"goal_id\": \"${goal_id}\"" "$GOAL_MANIFEST"; then
    record_failure "capability references unknown goal_id: $goal_id"
  fi
done

for agent in $(extract_values agent); do
  checked=$((checked + 1))
  adk_list_manifest_names agents | grep -Fxq "$agent" || record_failure "unknown agent: $agent"
done

for skill in $(extract_values skill); do
  checked=$((checked + 1))
  if ! adk_list_manifest_names skills | grep -Fxq "$skill" && ! adk_list_optional_skill_names | grep -Fxq "$skill"; then
    record_failure "unknown skill: $skill"
  fi
done

for workflow in $(extract_values workflow); do
  checked=$((checked + 1))
  adk_list_manifest_names workflows | grep -Fxq "$workflow" || record_failure "unknown workflow: $workflow"
done

while IFS= read -r script; do
  [[ -n "$script" ]] || continue
  require_file "$script"
done < <(extract_values script)

while IFS= read -r test_path; do
  [[ -n "$test_path" ]] || continue
  require_file "$test_path"
done < <(extract_values test)

while IFS= read -r doc; do
  [[ -n "$doc" ]] || continue
  require_file "$doc"
done < <(extract_values doc)

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"%s","capabilities":%s,"checked":%s,"failures":%s}\n' \
    "$status" "$capability_count" "$checked" "${#failures[@]}"
else
  if [[ "$status" == "pass" ]]; then
    echo "[PASS] ADK capability health capabilities=$capability_count"
  else
    for failure in "${failures[@]}"; do
      echo "[FAIL] $failure" >&2
    done
  fi
fi

if [[ "$status" != "pass" ]]; then
  exit 1
fi
