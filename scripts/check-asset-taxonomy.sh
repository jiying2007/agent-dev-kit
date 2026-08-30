#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

contains_word() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [[ "$item" == "$needle" ]] && return 0
  done
  return 1
}

is_numeric() {
  [[ "$1" =~ ^[0-9]+$ ]]
}

SKILL_CATEGORIES=(
  routing intake planning design implementation debugging verification
  review_quality release_closure governance
)
SKILL_PATTERNS=(
  tool-wrapper generator reviewer inversion pipeline playbook governance
)
ACTIVATION_MODES=(primary supporting fallback governance)
WORKFLOW_TYPES=(
  feature-delivery bugfix-delivery refactor-delivery
  embedded-bringup-delivery diagnostic-delivery release-hardening
  incident-response research-intake skill-curation-delivery
  archive-memory-governance adk-governance
)

skill_ref_exists() {
  local skill="$1"
  adk_list_manifest_names "skills" | grep -Fxq "$skill" && return 0
  adk_list_manifest_names "optional_skills" | grep -Fxq "$skill" && return 0
  return 1
}

skill_is_optional() {
  local skill="$1"
  adk_list_manifest_names "optional_skills" | grep -Fxq "$skill"
}

skill_activation_mode() {
  local skill="$1"
  local mode
  mode="$(adk_get_manifest_item_value "skills" "$skill" "activation_mode")"
  if [[ -z "$mode" ]]; then
    mode="$(adk_get_manifest_item_value "optional_skills" "$skill" "activation_mode")"
  fi
  printf '%s\n' "$mode"
}

require_primary_skill_ready() {
  local context="$1"
  local skill="$2"
  local availability="${3:-}"
  local mode

  skill_ref_exists "$skill" || fail "$context primary skill unknown: $skill"
  mode="$(skill_activation_mode "$skill")"
  [[ "$mode" == "primary" ]] || fail "$context primary skill '$skill' activation_mode must be primary, got: ${mode:-missing}"

  if skill_is_optional "$skill"; then
    [[ "$availability" == "optional-skill-required" ]] || fail "$context primary optional skill '$skill' requires availability: optional-skill-required"
  fi
}

workflow_ref_exists() {
  local workflow="$1"
  [[ "$workflow" == "-" || "$workflow" == "none" ]] && return 0
  adk_list_manifest_names "workflows" | grep -Fxq "$workflow"
}

skill_order() {
  local skill="$1"
  local order
  order="$(adk_get_manifest_item_value "skills" "$skill" "lifecycle_order")"
  if [[ -z "$order" ]]; then
    order="$(adk_get_manifest_item_value "optional_skills" "$skill" "lifecycle_order")"
  fi
  printf '%s\n' "$order"
}

skill_stage_order() {
  local skill="$1"
  local stage
  stage="$(adk_get_manifest_item_value "skills" "$skill" "stage_order")"
  if [[ -z "$stage" ]]; then
    stage="$(adk_get_manifest_item_value "optional_skills" "$skill" "stage_order")"
  fi
  printf '%s\n' "$stage"
}

skill_sort_order() {
  local skill="$1"
  local order stage
  order="$(skill_order "$skill")"
  stage="$(skill_stage_order "$skill")"
  [[ -n "$order" ]] || return 1
  [[ -n "$stage" ]] || return 1
  printf '%d\n' $((order * 1000 + stage))
}

check_asset_taxonomy_header() {
  grep -q '^asset_taxonomy:' "$ADK_MANIFEST" || fail "manifest missing asset_taxonomy"
  grep -q '^skill_routing_matrix:' "$ADK_MANIFEST" || fail "manifest missing skill_routing_matrix"
}

check_skill_section() {
  local section="$1"
  local label="$2"
  local name category order stage activation pattern

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    category="$(adk_get_manifest_item_value "$section" "$name" "category")"
    order="$(adk_get_manifest_item_value "$section" "$name" "lifecycle_order")"
    stage="$(adk_get_manifest_item_value "$section" "$name" "stage_order")"
    activation="$(adk_get_manifest_item_value "$section" "$name" "activation_mode")"
    pattern="$(adk_get_manifest_item_value "$section" "$name" "pattern")"

    [[ -n "$category" ]] || fail "$label '$name' missing category"
    contains_word "$category" "${SKILL_CATEGORIES[@]}" || fail "$label '$name' has invalid category: $category"
    [[ -n "$order" ]] || fail "$label '$name' missing lifecycle_order"
    is_numeric "$order" || fail "$label '$name' lifecycle_order must be numeric: $order"
    [[ -n "$stage" ]] || fail "$label '$name' missing stage_order"
    is_numeric "$stage" || fail "$label '$name' stage_order must be numeric: $stage"
    [[ -n "$activation" ]] || fail "$label '$name' missing activation_mode"
    contains_word "$activation" "${ACTIVATION_MODES[@]}" || fail "$label '$name' has invalid activation_mode: $activation"
    [[ -n "$pattern" ]] || fail "$label '$name' missing pattern"
    contains_word "$pattern" "${SKILL_PATTERNS[@]}" || fail "$label '$name' has invalid pattern: $pattern"
  done < <(adk_list_manifest_names "$section")
}

check_workflows() {
  local name type order entry_count exit_count
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    type="$(adk_get_manifest_item_value "workflows" "$name" "workflow_type")"
    order="$(adk_get_manifest_item_value "workflows" "$name" "lifecycle_order")"
    [[ -n "$type" ]] || fail "workflow '$name' missing workflow_type"
    contains_word "$type" "${WORKFLOW_TYPES[@]}" || fail "workflow '$name' has invalid workflow_type: $type"
    [[ -n "$order" ]] || fail "workflow '$name' missing lifecycle_order"
    is_numeric "$order" || fail "workflow '$name' lifecycle_order must be numeric: $order"
    entry_count="$(adk_get_manifest_item_list "workflows" "$name" "entry_conditions" | awk 'END {print NR+0}')"
    exit_count="$(adk_get_manifest_item_list "workflows" "$name" "exit_evidence" | awk 'END {print NR+0}')"
    [[ "$entry_count" -gt 0 ]] || fail "workflow '$name' missing entry_conditions"
    [[ "$exit_count" -gt 0 ]] || fail "workflow '$name' missing exit_evidence"
  done < <(adk_list_manifest_names "workflows")
}

check_manifest_section_order() {
  local section="$1"
  local label="$2"
  local workflow="${3:-0}"
  local name order stage sort previous previous_name

  previous=-1
  previous_name=""
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    order="$(adk_get_manifest_item_value "$section" "$name" "lifecycle_order")"
    if [[ "$workflow" -eq 1 ]]; then
      stage=0
    else
      stage="$(adk_get_manifest_item_value "$section" "$name" "stage_order")"
    fi
    [[ -n "$order" ]] || fail "$label '$name' missing lifecycle_order"
    [[ -n "$stage" ]] || fail "$label '$name' missing stage_order"
    is_numeric "$order" || fail "$label '$name' lifecycle_order must be numeric: $order"
    is_numeric "$stage" || fail "$label '$name' stage_order must be numeric: $stage"
    sort=$((order * 1000 + stage))
    if [[ "$sort" -lt "$previous" ]]; then
      fail "$section manifest order drift: '$previous_name'($previous) before '$name'($sort)"
    fi
    previous="$sort"
    previous_name="$name"
  done < <(adk_list_manifest_names "$section")
}

check_skill_dependency_order() {
  local section label skill dependency skill_sort dependency_sort
  for section in skills optional_skills; do
    label="skill"
    [[ "$section" == "optional_skills" ]] && label="optional skill"
    while IFS= read -r skill; do
      [[ -z "$skill" ]] && continue
      skill_sort="$(skill_sort_order "$skill")" || fail "$label '$skill' has invalid sort order"
      while IFS= read -r dependency; do
        [[ -z "$dependency" ]] && continue
        skill_ref_exists "$dependency" || fail "$label '$skill' depends_on unknown skill: $dependency"
        dependency_sort="$(skill_sort_order "$dependency")" || fail "$label '$skill' dependency '$dependency' has invalid sort order"
        if [[ "$dependency_sort" -gt "$skill_sort" ]]; then
          fail "$label '$skill' depends_on later skill '$dependency' ($dependency_sort > $skill_sort)"
        fi
      done < <(adk_get_manifest_item_list "$section" "$skill" "depends_on")
    done < <(adk_list_manifest_names "$section")
  done
}

check_profile_skill_order() {
  local profile skill order stage sort previous previous_skill
  while IFS= read -r profile; do
    [[ -z "$profile" ]] && continue
    previous=-1
    previous_skill=""
    while IFS= read -r skill; do
      [[ -z "$skill" ]] && continue
      skill_ref_exists "$skill" || fail "profile '$profile' references unknown skill: $skill"
      order="$(skill_order "$skill")"
      stage="$(skill_stage_order "$skill")"
      [[ -n "$order" ]] || fail "profile '$profile' skill '$skill' missing lifecycle_order"
      [[ -n "$stage" ]] || fail "profile '$profile' skill '$skill' missing stage_order"
      sort="$(skill_sort_order "$skill")" || fail "profile '$profile' skill '$skill' has invalid sort order"
      if [[ "$sort" -lt "$previous" ]]; then
        fail "profile '$profile' include_skills order drift: '$previous_skill'($previous) before '$skill'($sort)"
      fi
      previous="$sort"
      previous_skill="$skill"
    done < <(adk_get_profile_list "$profile" "include_skills")
  done < <(adk_list_profile_names)
}

check_skill_routing_matrix() {
  local scenario routing_intent primary workflow availability profiles_count positive_count negative_count ref
  local scenario_count=0
  while IFS= read -r scenario; do
    [[ -z "$scenario" ]] && continue
    scenario_count=$((scenario_count + 1))
    [[ "$scenario" =~ ^[a-z0-9_]+$ ]] || fail "routing scenario name must be snake_case: $scenario"
    routing_intent="$(adk_get_manifest_item_value "skill_routing_matrix" "$scenario" "routing_intent")"
    [[ -n "$routing_intent" ]] || fail "routing scenario '$scenario' missing routing_intent"
    adk_routing_intent_exists "$routing_intent" || fail "routing scenario '$scenario' references unknown routing intent: $routing_intent"
    primary="$(adk_get_routing_intent_value "$routing_intent" "primary_skill")"
    [[ -n "$primary" ]] || fail "routing intent '$routing_intent' missing primary_skill"
    availability="$(adk_get_routing_intent_value "$routing_intent" "availability")"
    require_primary_skill_ready "routing scenario '$scenario'" "$primary" "$availability"
    workflow="$(adk_get_manifest_item_value "skill_routing_matrix" "$scenario" "workflow")"
    [[ -n "$workflow" ]] || fail "routing scenario '$scenario' missing workflow"
    workflow_ref_exists "$workflow" || fail "routing scenario '$scenario' workflow unknown: $workflow"

    profiles_count="$(adk_get_manifest_item_list "skill_routing_matrix" "$scenario" "profiles" | awk 'END {print NR+0}')"
    positive_count="$(adk_get_manifest_item_list "skill_routing_matrix" "$scenario" "positive_examples" | awk 'END {print NR+0}')"
    negative_count="$(adk_get_manifest_item_list "skill_routing_matrix" "$scenario" "negative_examples" | awk 'END {print NR+0}')"
    [[ "$profiles_count" -gt 0 ]] || fail "routing scenario '$scenario' missing profiles"
    [[ "$positive_count" -gt 0 ]] || fail "routing scenario '$scenario' missing positive_examples"
    [[ "$negative_count" -gt 0 ]] || fail "routing scenario '$scenario' missing negative_examples"

    while IFS= read -r ref; do
      [[ -z "$ref" ]] && continue
      adk_profile_exists "$ref" || fail "routing scenario '$scenario' profile unknown: $ref"
    done < <(adk_get_manifest_item_list "skill_routing_matrix" "$scenario" "profiles")

    for key in supporting_skills fallback_skills mutually_exclusive; do
      while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        skill_ref_exists "$ref" || fail "routing scenario '$scenario' $key unknown skill: $ref"
      done < <(adk_get_routing_intent_list "$routing_intent" "$key")
    done
  done < <(adk_list_manifest_names "skill_routing_matrix")

  [[ "$scenario_count" -gt 0 ]] || fail "skill_routing_matrix has no scenarios"
}

check_routing_intents() {
  local intent primary availability ref key
  while IFS= read -r intent; do
    [[ -z "$intent" ]] && continue
    primary="$(adk_get_routing_intent_value "$intent" "primary_skill")"
    availability="$(adk_get_routing_intent_value "$intent" "availability")"
    [[ -n "$primary" ]] || fail "routing intent '$intent' missing primary_skill"
    require_primary_skill_ready "routing intent '$intent'" "$primary" "$availability"
    for key in supporting_skills fallback_skills mutually_exclusive; do
      while IFS= read -r ref; do
        [[ -z "$ref" ]] && continue
        skill_ref_exists "$ref" || fail "routing intent '$intent' $key unknown skill: $ref"
      done < <(adk_get_routing_intent_list "$intent" "$key")
    done
  done < <(adk_list_routing_intent_names)
}

adk_require_manifest
check_asset_taxonomy_header
check_skill_section "skills" "skill"
check_skill_section "optional_skills" "optional skill"
check_workflows
check_manifest_section_order "skills" "skill"
check_manifest_section_order "optional_skills" "optional skill"
check_manifest_section_order "workflows" "workflow" 1
check_skill_dependency_order
check_profile_skill_order
check_skill_routing_matrix
check_routing_intents

echo "[PASS] asset taxonomy checks passed"
