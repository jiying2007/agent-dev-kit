#!/usr/bin/env bash
set -euo pipefail

# Canonical Manifest access for shell compatibility shims.  All structured
# reads go through manifest.json; manifest.yaml no longer exists.
# shellcheck disable=SC2034
ADK_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC2034
ADK_ROOT_DIR="$(cd "$ADK_LIB_DIR/.." && pwd)"
# shellcheck disable=SC2034
ADK_MANIFEST="$ADK_ROOT_DIR/manifest.json"

_adk_manifest_query() {
  PYTHONPATH="$ADK_ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m agent_dev_kit.manifest_query --root "$ADK_ROOT_DIR" "$@"
}

adk_require_manifest() {
  [[ -f "$ADK_MANIFEST" ]] || {
    echo "[FAIL] manifest.json not found: $ADK_MANIFEST" >&2
    return 1
  }
}

adk_list_tool_names() { _adk_manifest_query section-entry-names tool_targets; }
adk_tool_exists() { adk_list_tool_names | grep -Fxq "$1"; }
adk_list_section_entry_names() { _adk_manifest_query section-entry-names "$1"; }
adk_get_section_entry_value() { _adk_manifest_query section-entry-value "$1" "$2" "$3"; }
adk_get_section_entry_list() { _adk_manifest_query section-entry-list "$1" "$2" "$3"; }

adk_list_reference_source_names() { adk_list_section_entry_names reference_sources; }
adk_get_reference_source_value() { adk_get_section_entry_value reference_sources "$1" "$2"; }

adk_list_external_handoff_target_names() { adk_list_section_entry_names external_handoff_targets; }
adk_external_handoff_target_exists() { adk_list_external_handoff_target_names | grep -Fxq "$1"; }
adk_get_external_handoff_target_value() { adk_get_section_entry_value external_handoff_targets "$1" "$2"; }
adk_get_external_handoff_target_list() { adk_get_section_entry_list external_handoff_targets "$1" "$2"; }

adk_get_tool_value() { adk_get_section_entry_value tool_targets "$1" "$2"; }
adk_get_tool_list() { adk_get_section_entry_list tool_targets "$1" "$2"; }

adk_list_profile_names() { _adk_manifest_query profile-names; }
adk_profile_exists() { adk_list_profile_names | grep -Fxq "$1"; }
adk_get_profile_value() { _adk_manifest_query profile-value "$1" "$2"; }
adk_get_profile_list() { _adk_manifest_query profile-list "$1" "$2"; }

adk_collect_profile_items() {
  local profile="$1"
  local key="$2"
  local visited="${3:-}"

  if [[ " $visited " == *" $profile "* ]]; then
    return 0
  fi
  visited="$visited $profile"

  local parent
  parent="$(adk_get_profile_value "$profile" extends)"
  if [[ -n "$parent" ]]; then
    adk_collect_profile_items "$parent" "$key" "$visited"
  fi
  while IFS= read -r parent; do
    [[ -z "$parent" ]] && continue
    adk_collect_profile_items "$parent" "$key" "$visited"
  done < <(adk_get_profile_list "$profile" extends)

  adk_get_profile_list "$profile" "$key"
}

adk_resolve_profile_items() {
  adk_collect_profile_items "$1" "$2" "" | awk 'NF' | sort -u
}

adk_list_manifest_names() { _adk_manifest_query manifest-names "$1"; }
adk_list_manifest_paths() { _adk_manifest_query manifest-paths "$1"; }
adk_get_manifest_item_value() { _adk_manifest_query manifest-item-value "$1" "$2" "$3"; }
adk_get_manifest_item_list() { _adk_manifest_query manifest-item-list "$1" "$2" "$3"; }

adk_list_optional_skill_names() { adk_list_manifest_names optional_skills; }
adk_optional_skill_exists() { adk_list_optional_skill_names | grep -Fxq "$1"; }
adk_get_optional_skill_path() { adk_get_manifest_item_value optional_skills "$1" path; }

adk_to_lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

adk_run_cmd() {
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

adk_resolve_profile_items_all() {
  local key="$1"
  shift
  local profile
  for profile in "$@"; do
    adk_resolve_profile_items "$profile" "$key"
  done | awk 'NF' | sort -u
}

adk_list_routing_intent_names() { _adk_manifest_query routing-intent-names; }
adk_routing_intent_exists() { adk_list_routing_intent_names | grep -Fxq "$1"; }
adk_get_routing_intent_value() { _adk_manifest_query routing-intent-value "$1" "$2"; }
adk_get_routing_intent_list() { _adk_manifest_query routing-intent-list "$1" "$2"; }
adk_list_routing_intents() { _adk_manifest_query routing-intents; }
adk_get_routing_supporting_skills() { _adk_manifest_query routing-supporting-skills "$1"; }
