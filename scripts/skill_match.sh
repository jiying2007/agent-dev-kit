#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./lib_manifest.sh
source "$SCRIPT_DIR/lib_manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/skill_match.sh --text <input> [--skill <name>] [--scope auto|skill|optional-skill]

Options:
  --text <input>                   # 用户输入文本（必填）
  --skill <name>                   # 指定 skill 名称（可选，不指定则自动匹配）
  --scope auto|skill|optional-skill  # 默认 auto
  -h, --help

Examples:
  # 自动匹配（推荐）: 扫描 routing 表，再扫描 skill triggers
  ./scripts/skill_match.sh --text "需求不清楚"
  ./scripts/skill_match.sh --text "我要写驱动"

  # 指定 skill 匹配（向后兼容）
  ./scripts/skill_match.sh --skill gdk-requirements-triage --text "收到模糊需求"
USAGE
}

SKILL=""
TEXT=""
SCOPE="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      SKILL="$2"
      shift 2
      ;;
    --text)
      TEXT="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
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

contains_phrase() {
  local text="$1"
  local phrase="$2"
  local lower_text
  lower_text="$(gdk_to_lower "$text")"
  # Split on "/" and match any sub-phrase
  IFS='/' read -ra parts <<< "$phrase"
  for part in "${parts[@]}"; do
    [[ -z "$part" ]] && continue
    if [[ "$lower_text" == *"$(gdk_to_lower "$part")"* ]]; then
      return 0
    fi
  done
  return 1
}

extract_frontmatter_list() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    NR==1 && $0=="---" {in_fm=1; next}
    in_fm && $0=="---" {exit}
    in_fm && $0 ~ "^" key ":" {in_list=1; next}
    in_list && $0 ~ "^  - " {
      value=$0
      sub("^  - ", "", value)
      gsub(/^"|"$/, "", value)
      print value
      next
    }
    in_list && $0 ~ "^[a-z_]+:" {in_list=0}
  ' "$file"
}

resolve_skill_file() {
  local name="$1"
  local scope="$2"

  case "$scope" in
    skill)
      echo "$GDK_ROOT_DIR/skills/$name/SKILL.md"
      ;;
    optional-skill)
      local path
      path="$(gdk_get_optional_skill_path "$name")"
      [[ -n "$path" ]] || { echo ""; return 0; }
      echo "$GDK_ROOT_DIR/$path"
      ;;
    auto)
      if [[ -f "$GDK_ROOT_DIR/skills/$name/SKILL.md" ]]; then
        echo "$GDK_ROOT_DIR/skills/$name/SKILL.md"
        return 0
      fi
      local path
      path="$(gdk_get_optional_skill_path "$name")"
      [[ -n "$path" ]] || { echo ""; return 0; }
      echo "$GDK_ROOT_DIR/$path"
      ;;
    *)
      echo "[FAIL] unsupported --scope: $scope" >&2
      exit 1
      ;;
  esac
}

# --- Mode 1: Auto-match (no --skill) ---
# Scan routing table first, then all skill triggers

if [[ -z "$SKILL" ]]; then
  [[ -n "$TEXT" ]] || { echo "[FAIL] --text is required" >&2; exit 1; }

  # Phase 1: Scan routing table intent_zh
  while IFS=$'\t' read -r intent_zh primary_skill; do
    [[ -z "$intent_zh" ]] && continue
    if contains_phrase "$TEXT" "$intent_zh"; then
      # Get supporting skills if any
      supporting=""
      while IFS= read -r s; do
        [[ -z "$s" ]] && continue
        [[ -n "$supporting" ]] && supporting="$supporting,$s"
        [[ -z "$supporting" ]] && supporting="$s"
      done < <(awk -v skill="$primary_skill" '
        $0 ~ /^routing:/ {in_r=1; next}
        in_r && $0 ~ /^[^ ]/ {in_r=0}
        in_r && $0 ~ "primary_skill: " skill {found=1; next}
        found && $0 ~ /supporting_skills:/ {in_sup=1; next}
        in_sup && $0 ~ /^      - / {item=$0; sub(/^      - /, "", item); print item; next}
        in_sup && $0 ~ /^    [a-z]/ {found=0; in_sup=0}
      ' "$GDK_MANIFEST")
      echo "match=true source=routing skill=$primary_skill intent_zh=\"$intent_zh\"${supporting:+ supporting_skills=$supporting}"
      exit 0
    fi
  done < <(gdk_list_routing_intents)

  # Phase 2: Scan all core skill triggers
  while IFS=' ' read -r name path; do
    [[ -z "$name" || -z "$path" ]] && continue
    local_file="$GDK_ROOT_DIR/$path"
    [[ -f "$local_file" ]] || continue
    mapfile -t triggers < <(extract_frontmatter_list "$local_file" "triggers")
    for phrase in "${triggers[@]}"; do
      [[ -z "$phrase" ]] && continue
      if contains_phrase "$TEXT" "$phrase"; then
        echo "match=true source=skill_trigger skill=$name trigger=\"$phrase\""
        exit 0
      fi
    done
  done < <(gdk_list_manifest_paths "skills")

  # Phase 3: Scan optional skill triggers
  while IFS=' ' read -r name path; do
    [[ -z "$name" || -z "$path" ]] && continue
    local_file="$GDK_ROOT_DIR/$path"
    [[ -f "$local_file" ]] || continue
    mapfile -t triggers < <(extract_frontmatter_list "$local_file" "triggers")
    for phrase in "${triggers[@]}"; do
      [[ -z "$phrase" ]] && continue
      if contains_phrase "$TEXT" "$phrase"; then
        echo "match=true source=optional_skill_trigger skill=$name trigger=\"$phrase\""
        exit 0
      fi
    done
  done < <(gdk_list_manifest_paths "optional_skills")

  echo "match=false reason=no_match_found"
  exit 1
fi

# --- Mode 2: Specific skill match (--skill provided) ---

[[ -n "$TEXT" ]] || { echo "[FAIL] --text is required" >&2; exit 1; }

SKILL_FILE="$(resolve_skill_file "$SKILL" "$SCOPE")"
[[ -n "$SKILL_FILE" && -f "$SKILL_FILE" ]] || {
  echo "match=false skill=$SKILL reason=skill_not_found"
  exit 1
}

mapfile -t NON_TRIGGERS < <(extract_frontmatter_list "$SKILL_FILE" "non_triggers")
for phrase in "${NON_TRIGGERS[@]}"; do
  [[ -z "$phrase" ]] && continue
  if contains_phrase "$TEXT" "$phrase"; then
    echo "match=false skill=$SKILL reason=matched_non_trigger phrase=$phrase"
    exit 1
  fi
done

mapfile -t TRIGGERS < <(extract_frontmatter_list "$SKILL_FILE" "triggers")
for phrase in "${TRIGGERS[@]}"; do
  [[ -z "$phrase" ]] && continue
  if contains_phrase "$TEXT" "$phrase"; then
    echo "match=true skill=$SKILL reason=matched_trigger phrase=$phrase"
    exit 0
  fi
done

echo "match=false skill=$SKILL reason=no_trigger_matched"
exit 1
