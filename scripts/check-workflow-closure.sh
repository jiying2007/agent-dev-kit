#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-workflow-closure.sh [options]

Options:
  --profile <profile>              # 默认 manifest default_profile
  --extra-profile <profile>        # 可重复
  --with-optional-skill <skill>     # 可重复
  --summary-json
  -h, --help

Checks that every workflow exported for the selected profile set references
only agents and skills available in that profile closure.
USAGE
}

PROFILE=""
EXTRA_PROFILES=()
OPTIONAL_SKILLS=()
SUMMARY_JSON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --extra-profile)
      EXTRA_PROFILES+=("$2")
      shift 2
      ;;
    --with-optional-skill)
      OPTIONAL_SKILLS+=("$2")
      shift 2
      ;;
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
adk_require_manifest

if [[ -z "$PROFILE" ]]; then
  PROFILE="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
fi

adk_profile_exists "$PROFILE" || {
  echo "[FAIL] unknown profile: $PROFILE" >&2
  exit 1
}

for profile in "${EXTRA_PROFILES[@]}"; do
  adk_profile_exists "$profile" || {
    echo "[FAIL] unknown extra profile: $profile" >&2
    exit 1
  }
done

for skill in "${OPTIONAL_SKILLS[@]}"; do
  adk_optional_skill_exists "$skill" || {
    echo "[FAIL] unknown optional skill: $skill" >&2
    exit 1
  }
done

ALL_PROFILES=("$PROFILE" "${EXTRA_PROFILES[@]}")
mapfile -t available_agents < <(adk_resolve_profile_items_all "include_agents" "${ALL_PROFILES[@]}")
mapfile -t available_skills < <(
  {
    adk_resolve_profile_items_all "include_skills" "${ALL_PROFILES[@]}"
    printf '%s\n' "${OPTIONAL_SKILLS[@]}"
  } | awk 'NF' | sort -u
)

contains_item() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

workflow_applies_to_profiles() {
  local workflow="$1"
  local profile
  while IFS= read -r profile; do
    [[ -z "$profile" ]] && continue
    contains_item "$profile" "${ALL_PROFILES[@]}" && return 0
  done < <(adk_get_manifest_item_list "workflows" "$workflow" "profiles")
  return 1
}

failures=()
checked=0
exportable=0

while IFS= read -r workflow; do
  [[ -z "$workflow" ]] && continue
  workflow_applies_to_profiles "$workflow" || continue
  checked=$((checked + 1))
  workflow_ok=1

  while IFS= read -r agent; do
    [[ -z "$agent" ]] && continue
    if ! contains_item "$agent" "${available_agents[@]}"; then
      failures+=("workflow '$workflow' missing agent in selected profiles: $agent")
      workflow_ok=0
    fi
  done < <(adk_get_manifest_item_list "workflows" "$workflow" "agents")

  while IFS= read -r skill; do
    [[ -z "$skill" ]] && continue
    if ! contains_item "$skill" "${available_skills[@]}"; then
      failures+=("workflow '$workflow' missing skill in selected profiles: $skill")
      workflow_ok=0
    fi
  done < <(adk_get_manifest_item_list "workflows" "$workflow" "skills")

  if [[ "$workflow_ok" -eq 1 ]]; then
    exportable=$((exportable + 1))
  fi
done < <(adk_list_manifest_names "workflows")

if [[ "$checked" -eq 0 ]]; then
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    printf '{"schema_version":1,"status":"fail","profiles":"%s","checked":0,"exportable":0,"failures":1}\n' \
      "${ALL_PROFILES[*]}"
  else
    echo "[FAIL] workflow closure check found no workflows for profiles: ${ALL_PROFILES[*]}" >&2
  fi
  exit 1
fi

if [[ "${#failures[@]}" -gt 0 ]]; then
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    printf '{"schema_version":1,"status":"fail","profiles":"%s","checked":%s,"exportable":%s,"failures":%s}\n' \
      "${ALL_PROFILES[*]}" "$checked" "$exportable" "${#failures[@]}"
  else
    echo "[FAIL] workflow closure check failed for profiles: ${ALL_PROFILES[*]}" >&2
    printf '  - %s\n' "${failures[@]}" >&2
  fi
  exit 1
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"pass","profiles":"%s","checked":%s,"exportable":%s,"failures":0}\n' \
    "${ALL_PROFILES[*]}" "$checked" "$exportable"
else
  echo "[PASS] workflow closure check profiles=${ALL_PROFILES[*]} workflows=$checked"
fi
