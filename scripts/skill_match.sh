#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib_manifest.sh
source "$SCRIPT_DIR/lib_manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/skill_match.sh --skill <name> --text <input> [options]

Options:
  --scope auto|skill|optional-skill      # 默认 auto
  -h, --help

Examples:
  ./scripts/skill_match.sh --skill requirements-triage --text "收到模糊需求"
  ./scripts/skill_match.sh --skill incident-rca-report --scope optional-skill --text "出现线上故障且需要复盘闭环"
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

to_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

contains_phrase() {
  local text="$1"
  local phrase="$2"
  [[ "$(to_lower "$text")" == *"$(to_lower "$phrase")"* ]]
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
      print value
      next
    }
    in_list && $0 ~ "^[a-z_]+:" {in_list=0}
  ' "$file"
}

resolve_skill_file() {
  local name="$1"
  local scope="$2"
  local path=""

  case "$scope" in
    skill)
      echo "$ROOT_DIR/skills/$name/SKILL.md"
      ;;
    optional-skill)
      path="$(gdk_get_optional_skill_path "$name")"
      [[ -n "$path" ]] || {
        echo ""
        return 0
      }
      echo "$ROOT_DIR/$path"
      ;;
    auto)
      if [[ -f "$ROOT_DIR/skills/$name/SKILL.md" ]]; then
        echo "$ROOT_DIR/skills/$name/SKILL.md"
        return 0
      fi
      path="$(gdk_get_optional_skill_path "$name")"
      [[ -n "$path" ]] || {
        echo ""
        return 0
      }
      echo "$ROOT_DIR/$path"
      ;;
    *)
      echo "[FAIL] unsupported --scope: $scope" >&2
      exit 1
      ;;
  esac
}

gdk_require_manifest

[[ -n "$SKILL" ]] || { echo "[FAIL] --skill is required" >&2; exit 1; }
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
