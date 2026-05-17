#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC2034
ADK_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC2034
ADK_ROOT_DIR="$(cd "$ADK_LIB_DIR/.." && pwd)"
# shellcheck disable=SC2034
ADK_MANIFEST="$ADK_ROOT_DIR/manifest.yaml"

adk_require_manifest() {
  [[ -f "$ADK_MANIFEST" ]] || {
    echo "[FAIL] manifest.yaml not found: $ADK_MANIFEST" >&2
    return 1
  }
}

adk_section_block() {
  local section="$1"
  awk -v section="$section" '
    $0 ~ "^" section ":" {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section {print}
  ' "$ADK_MANIFEST"
}

adk_list_tool_names() {
  adk_section_block "tool_targets" | awk '
    $0 ~ /^  [a-z0-9-]+:$/ {
      name=$1
      sub(":", "", name)
      print name
    }
  '
}

adk_tool_exists() {
  local tool="$1"
  adk_list_tool_names | grep -Fxq "$tool"
}

adk_get_tool_value() {
  local tool="$1"
  local key="$2"
  awk -v tool="$tool" -v key="$key" '
    $0 ~ /^tool_targets:/ {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ "^  " tool ":" {in_tool=1; next}
    in_tool {
      if ($0 ~ /^  [a-z0-9-]+:/) {exit}
      if ($0 ~ "^    " key ":") {
        value=$0
        sub("^    " key ":[ ]*", "", value)
        gsub(/^"|"$/, "", value)
        print value
        exit
      }
    }
  ' "$ADK_MANIFEST"
}

adk_get_tool_list() {
  local tool="$1"
  local key="$2"
  awk -v tool="$tool" -v key="$key" '
    $0 ~ /^tool_targets:/ {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ "^  " tool ":" {in_tool=1; next}
    in_tool {
      if ($0 ~ /^  [a-z0-9-]+:/) {exit}
      if ($0 ~ "^    " key ":") {in_list=1; next}
      if (in_list) {
        if ($0 ~ /^      - /) {
          item=$0
          sub(/^      - /, "", item)
          print item
          next
        }
        if ($0 ~ /^    [a-z0-9_-]+:/) {
          in_list=0
        }
      }
    }
  ' "$ADK_MANIFEST"
}

adk_list_profile_names() {
  adk_section_block "profiles" | awk '
    $0 ~ /^  [a-z0-9-]+:$/ {
      name=$1
      sub(":", "", name)
      print name
    }
  '
}

adk_profile_exists() {
  local profile="$1"
  adk_list_profile_names | grep -Fxq "$profile"
}

adk_get_profile_value() {
  local profile="$1"
  local key="$2"
  awk -v profile="$profile" -v key="$key" '
    $0 ~ /^profiles:/ {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ "^  " profile ":" {in_profile=1; next}
    in_profile {
      if ($0 ~ /^  [a-z0-9-]+:/) {exit}
      if ($0 ~ "^    " key ":") {
        value=$0
        sub("^    " key ":[ ]*", "", value)
        gsub(/^"|"$/, "", value)
        print value
        exit
      }
    }
  ' "$ADK_MANIFEST"
}

adk_get_profile_list() {
  local profile="$1"
  local key="$2"
  awk -v profile="$profile" -v key="$key" '
    $0 ~ /^profiles:/ {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ "^  " profile ":" {in_profile=1; next}
    in_profile {
      if ($0 ~ /^  [a-z0-9-]+:/) {exit}
      if ($0 ~ "^    " key ":") {in_list=1; next}
      if (in_list) {
        if ($0 ~ /^      - /) {
          item=$0
          sub(/^      - /, "", item)
          print item
          next
        }
        if ($0 ~ /^    [a-z0-9_-]+:/) {
          in_list=0
        }
      }
    }
  ' "$ADK_MANIFEST"
}

adk_collect_profile_items() {
  local profile="$1"
  local key="$2"
  local visited="${3:-}"

  if [[ " $visited " == *" $profile "* ]]; then
    return 0
  fi

  visited="$visited $profile"

  local parent
  parent="$(adk_get_profile_value "$profile" "extends")"
  if [[ -n "$parent" ]]; then
    adk_collect_profile_items "$parent" "$key" "$visited"
  fi

  while IFS= read -r parent; do
    [[ -z "$parent" ]] && continue
    adk_collect_profile_items "$parent" "$key" "$visited"
  done < <(adk_get_profile_list "$profile" "extends")

  adk_get_profile_list "$profile" "$key"
}

adk_resolve_profile_items() {
  local profile="$1"
  local key="$2"
  adk_collect_profile_items "$profile" "$key" "" | awk 'NF' | sort -u
}

adk_list_manifest_names() {
  local section="$1"
  adk_section_block "$section" | awk '
    $0 ~ /^  - name:/ {print $3}
  '
}

adk_list_manifest_paths() {
  local section="$1"
  adk_section_block "$section" | awk '
    $0 ~ /^  - name:/ {
      name=$3
      next
    }
    $0 ~ /^    path:/ {
      path=$2
      print name " " path
    }
  '
}

adk_get_manifest_item_value() {
  local section="$1"
  local name="$2"
  local key="$3"
  awk -v section="$section" -v name="$name" -v key="$key" '
    $0 ~ "^" section ":" {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ /^  - name:/ {
      current=$3
      next
    }
    in_section && current == name && $0 ~ "^    " key ":" {
      value=$0
      sub("^    " key ":[ ]*", "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$ADK_MANIFEST"
}

adk_get_manifest_item_list() {
  local section="$1"
  local name="$2"
  local key="$3"

  awk -v section="$section" -v name="$name" -v key="$key" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      gsub(/^"|"$/, "", value)
      return value
    }
    function emit_inline(value, items, i, item) {
      gsub(/[\[\]]/, "", value)
      split(value, items, ",")
      for (i in items) {
        item=trim(items[i])
        if (item != "") {
          print item
        }
      }
    }
    $0 ~ "^" section ":" {in_section=1; current=""; next}
    in_section && $0 ~ "^[^ ]" {exit}
    in_section && $0 ~ /^  - name:/ {
      if (current == name) {exit}
      current=$3
      in_list=0
      next
    }
    in_section && current == name {
      if ($0 ~ "^    " key ":[[:space:]]*\\[") {
        value=$0
        sub("^    " key ":[[:space:]]*", "", value)
        emit_inline(value)
        next
      }
      if ($0 ~ "^    " key ":") {in_list=1; next}
      if (in_list && $0 ~ /^      - /) {
        item=$0
        sub(/^      - /, "", item)
        print trim(item)
        next
      }
      if (in_list && $0 ~ /^    [a-zA-Z0-9_-]+:/) {exit}
    }
  ' "$ADK_MANIFEST"
}

adk_list_optional_skill_names() {
  adk_list_manifest_names "optional_skills"
}

adk_optional_skill_exists() {
  local skill="$1"
  adk_list_optional_skill_names | grep -Fxq "$skill"
}

adk_get_optional_skill_path() {
  local skill="$1"
  adk_get_manifest_item_value "optional_skills" "$skill" "path"
}

# --- Common utility functions ---

adk_to_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# Requires caller to set DRY_RUN (0 or 1).
adk_run_cmd() {
  if [[ "${DRY_RUN:-0}" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

# Resolve items from multiple profiles at once.
# Usage: adk_resolve_profile_items_all <key> <profile1> [profile2 ...]
adk_resolve_profile_items_all() {
  local key="$1"
  shift
  local profiles=("$@")
  local profile
  for profile in "${profiles[@]}"; do
    adk_resolve_profile_items "$profile" "$key"
  done | awk 'NF' | sort -u
}

# --- Routing table functions ---

adk_list_routing_intents() {
  # Output: intent_zh<TAB>primary_skill for each routing entry
  awk '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      gsub(/^"|"$/, "", value)
      return value
    }
    $0 ~ /^routing:/ {in_routing=1; intent_zh=""; primary=""; next}
    in_routing && $0 ~ /^[^ ]/ {in_routing=0}
    in_routing && $0 ~ /^[[:space:]]+-[[:space:]]+intent:/ {
      intent_zh=""
      primary=""
      next
    }
    in_routing {
      if ($0 ~ /^[[:space:]]+intent_zh:/) {
        val=$0
        sub(/^[[:space:]]+intent_zh:[[:space:]]*/, "", val)
        intent_zh=trim(val)
      }
      if ($0 ~ /^[[:space:]]+primary_skill:/) {
        val=$0
        sub(/^[[:space:]]+primary_skill:[[:space:]]*/, "", val)
        primary=trim(val)
        if (intent_zh != "" && primary != "") {
          print intent_zh "\t" primary
          intent_zh=""; primary=""
        }
      }
    }
  ' "$ADK_MANIFEST"
}

adk_get_routing_supporting_skills() {
  local primary_skill="$1"
  awk -v skill="$primary_skill" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      gsub(/^"|"$/, "", value)
      return value
    }
    function indent(line) {
      match(line, /[^ ]/)
      return RSTART ? RSTART - 1 : 0
    }
    function emit_inline(value, items, i, item) {
      gsub(/[\[\]]/, "", value)
      split(value, items, ",")
      for (i in items) {
        item=trim(items[i])
        if (item != "") {
          print item
        }
      }
    }
    $0 ~ /^routing:/ {in_routing=1; found=0; in_supporting=0; supporting_indent=0; next}
    in_routing && $0 ~ /^[^ ]/ {exit}
    !in_routing {next}
    in_routing && $0 ~ /^[[:space:]]+-[[:space:]]+intent:/ {
      if (found) {
        exit
      }
      found=0
      in_supporting=0
      next
    }
    in_routing && $0 ~ /^[[:space:]]+primary_skill:/ {
      val=$0
      sub(/^[[:space:]]+primary_skill:[[:space:]]*/, "", val)
      found=(trim(val) == skill)
      next
    }
    found && $0 ~ /^[[:space:]]+supporting_skills:[[:space:]]*\[/ {
      val=$0
      sub(/^[[:space:]]+supporting_skills:[[:space:]]*/, "", val)
      emit_inline(val)
      next
    }
    found && $0 ~ /^[[:space:]]+supporting_skills:/ {
      in_supporting=1
      supporting_indent=indent($0)
      next
    }
    in_supporting && indent($0) <= supporting_indent && $0 ~ /^[[:space:]]+[a-zA-Z_-]+:/ {
      exit
    }
    in_supporting && indent($0) > supporting_indent && $0 ~ /^[[:space:]]+-[[:space:]]+/ {
      item=$0
      sub(/^[[:space:]]+-[[:space:]]*/, "", item)
      print trim(item)
      next
    }
  ' "$ADK_MANIFEST"
}
