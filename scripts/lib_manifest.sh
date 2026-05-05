#!/usr/bin/env bash
set -euo pipefail

# shellcheck disable=SC2034
GDK_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC2034
GDK_ROOT_DIR="$(cd "$GDK_LIB_DIR/.." && pwd)"
# shellcheck disable=SC2034
GDK_MANIFEST="$GDK_ROOT_DIR/manifest.yaml"

gdk_require_manifest() {
  [[ -f "$GDK_MANIFEST" ]] || {
    echo "[FAIL] manifest.yaml not found: $GDK_MANIFEST" >&2
    return 1
  }
}

gdk_section_block() {
  local section="$1"
  awk -v section="$section" '
    $0 ~ "^" section ":" {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section {print}
  ' "$GDK_MANIFEST"
}

gdk_list_tool_names() {
  gdk_section_block "tool_targets" | awk '
    $0 ~ /^  [a-z0-9-]+:$/ {
      name=$1
      sub(":", "", name)
      print name
    }
  '
}

gdk_tool_exists() {
  local tool="$1"
  gdk_list_tool_names | grep -Fxq "$tool"
}

gdk_get_tool_value() {
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
  ' "$GDK_MANIFEST"
}

gdk_get_tool_list() {
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
  ' "$GDK_MANIFEST"
}

gdk_list_profile_names() {
  gdk_section_block "profiles" | awk '
    $0 ~ /^  [a-z0-9-]+:$/ {
      name=$1
      sub(":", "", name)
      print name
    }
  '
}

gdk_profile_exists() {
  local profile="$1"
  gdk_list_profile_names | grep -Fxq "$profile"
}

gdk_get_profile_value() {
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
  ' "$GDK_MANIFEST"
}

gdk_get_profile_list() {
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
  ' "$GDK_MANIFEST"
}

gdk_collect_profile_items() {
  local profile="$1"
  local key="$2"
  local visited="${3:-}"

  if [[ " $visited " == *" $profile "* ]]; then
    return 0
  fi

  visited="$visited $profile"

  local parent
  while IFS= read -r parent; do
    [[ -z "$parent" ]] && continue
    gdk_collect_profile_items "$parent" "$key" "$visited"
  done < <(gdk_get_profile_list "$profile" "extends")

  gdk_get_profile_list "$profile" "$key"
}

gdk_resolve_profile_items() {
  local profile="$1"
  local key="$2"
  gdk_collect_profile_items "$profile" "$key" "" | awk 'NF' | sort -u
}

gdk_list_manifest_names() {
  local section="$1"
  gdk_section_block "$section" | awk '
    $0 ~ /^  - name:/ {print $3}
  '
}

gdk_list_manifest_paths() {
  local section="$1"
  gdk_section_block "$section" | awk '
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

gdk_get_manifest_item_value() {
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
  ' "$GDK_MANIFEST"
}

gdk_list_optional_skill_names() {
  gdk_list_manifest_names "optional_skills"
}

gdk_optional_skill_exists() {
  local skill="$1"
  gdk_list_optional_skill_names | grep -Fxq "$skill"
}

gdk_get_optional_skill_path() {
  local skill="$1"
  gdk_get_manifest_item_value "optional_skills" "$skill" "path"
}

# --- Routing table functions ---

gdk_list_routing_intents() {
  # Output: intent_zh<TAB>primary_skill for each routing entry
  awk '
    $0 ~ /^routing:/ {in_routing=1; next}
    in_routing && $0 ~ /^[^ ]/ {in_routing=0}
    in_routing && $0 ~ /^  - intent:/ {has_intent=1; next}
    in_routing {
      if ($0 ~ /^    intent_zh:/) {
        val=$0; sub(/^    intent_zh: */, "", val); gsub(/^"|"$/, "", val)
        intent_zh=val
      }
      if ($0 ~ /^    primary_skill:/) {
        val=$0; sub(/^    primary_skill: */, "", val)
        primary=val
        if (intent_zh != "" && primary != "") {
          print intent_zh "\t" primary
          intent_zh=""; primary=""
        }
      }
    }
  ' "$GDK_MANIFEST"
}
