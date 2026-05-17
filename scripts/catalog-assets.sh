#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/catalog-assets.sh <build|find> [options]

Commands:
  build  生成 Agent/Skill/Profile 索引文档
  find   按关键词检索 Agent/Skill/Profile

Options:
  --out <path>                                # build 输出文件，默认 docs/agent-skill-catalog.md
  --keyword <text>                            # find 必填
  --type all|agent|skill|optional-skill|profile
  -h, --help

Examples:
  ./scripts/catalog-assets.sh build
  ./scripts/catalog-assets.sh find --type skill --keyword bring-up
USAGE
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

ACTION="$1"
shift

OUT_PATH="$ROOT_DIR/docs/agent-skill-catalog.md"
KEYWORD=""
TYPE="all"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out)
      OUT_PATH="$2"
      shift 2
      ;;
    --keyword)
      KEYWORD="$2"
      shift 2
      ;;
    --type)
      TYPE="$2"
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

frontmatter_value() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    NR==1 && $0=="---" {in_fm=1; next}
    in_fm && $0=="---" {exit}
    in_fm && $0 ~ "^" key ":" {
      value=$0
      sub("^" key ":[ ]*", "", value)
      print value
      exit
    }
  ' "$file"
}

frontmatter_first_list_item() {
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
      exit
    }
    in_list && $0 ~ "^[a-z_]+:" {in_list=0}
  ' "$file"
}

match_keyword() {
  local text="$1"
  local needle="$2"
  [[ "$(adk_to_lower "$text")" == *"$(adk_to_lower "$needle")"* ]]
}

emit_agents_table() {
  echo "## Agents"
  echo
  echo "| Name | Role | Path |"
  echo "|---|---|---|"
  local name role path
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    role="$(adk_get_manifest_item_value "agents" "$name" "role")"
    path="$(adk_get_manifest_item_value "agents" "$name" "path")"
    echo "| \`$name\` | $role | \`$path\` |"
  done < <(adk_list_manifest_names "agents")
  echo
}

emit_skills_table() {
  local section="$1"
  local title="$2"

  echo "## $title"
  echo
  echo "| Name | Description | First Trigger | Path |"
  echo "|---|---|---|---|"

  local name path file desc trigger
  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    path="$(adk_get_manifest_item_value "$section" "$name" "path")"
    file="$ROOT_DIR/$path"
    desc="$(frontmatter_value "$file" "description")"
    trigger="$(frontmatter_first_list_item "$file" "triggers")"
    echo "| \`$name\` | $desc | $trigger | \`$path\` |"
  done < <(adk_list_manifest_names "$section")
  echo
}

emit_profiles_table() {
  echo "## Profiles"
  echo
  echo "| Name | Description | Optional | Extends |"
  echo "|---|---|---|---|"
  local profile desc optional extends
  while IFS= read -r profile; do
    [[ -z "$profile" ]] && continue
    desc="$(adk_get_profile_value "$profile" "description")"
    optional="$(adk_get_profile_value "$profile" "optional")"
    [[ -n "$optional" ]] || optional="false"
    extends="$(adk_get_profile_value "$profile" "extends")"
    if [[ -z "$extends" ]]; then
      extends="$(adk_get_profile_list "$profile" "extends" | paste -sd ',' -)"
    fi
    [[ -n "$extends" ]] || extends="-"
    echo "| \`$profile\` | $desc | $optional | $extends |"
  done < <(adk_list_profile_names)
  echo
}

build_catalog() {
  mkdir -p "$(dirname "$OUT_PATH")"
  {
    echo "# Agent and Skill Catalog"
    echo
    echo "- generated_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "- source: manifest.yaml"
    echo
    emit_agents_table
    emit_skills_table "skills" "Skills"
    emit_skills_table "optional_skills" "Optional Skills"
    emit_profiles_table
  } > "$OUT_PATH"
  echo "[OK] catalog generated: $OUT_PATH"
}

emit_find_row() {
  local kind="$1"
  local name="$2"
  local desc="$3"
  local path="$4"
  printf '%s\t%s\t%s\t%s\n' "$kind" "$name" "$desc" "$path"
}

find_items() {
  [[ -n "$KEYWORD" ]] || {
    echo "[FAIL] --keyword is required for find" >&2
    exit 1
  }

  echo -e "type\tname\tdescription\tpath"

  if [[ "$TYPE" == "all" || "$TYPE" == "agent" ]]; then
    local name role path
    while IFS= read -r name; do
      role="$(adk_get_manifest_item_value "agents" "$name" "role")"
      path="$(adk_get_manifest_item_value "agents" "$name" "path")"
      if match_keyword "$name $role" "$KEYWORD"; then
        emit_find_row "agent" "$name" "$role" "$path"
      fi
    done < <(adk_list_manifest_names "agents")
  fi

  if [[ "$TYPE" == "all" || "$TYPE" == "skill" ]]; then
    local name path file desc
    while IFS= read -r name; do
      path="$(adk_get_manifest_item_value "skills" "$name" "path")"
      file="$ROOT_DIR/$path"
      desc="$(frontmatter_value "$file" "description")"
      if match_keyword "$name $desc" "$KEYWORD"; then
        emit_find_row "skill" "$name" "$desc" "$path"
      fi
    done < <(adk_list_manifest_names "skills")
  fi

  if [[ "$TYPE" == "all" || "$TYPE" == "optional-skill" ]]; then
    local name path file desc
    while IFS= read -r name; do
      path="$(adk_get_manifest_item_value "optional_skills" "$name" "path")"
      file="$ROOT_DIR/$path"
      desc="$(frontmatter_value "$file" "description")"
      if match_keyword "$name $desc" "$KEYWORD"; then
        emit_find_row "optional-skill" "$name" "$desc" "$path"
      fi
    done < <(adk_list_manifest_names "optional_skills")
  fi

  if [[ "$TYPE" == "all" || "$TYPE" == "profile" ]]; then
    local profile desc
    while IFS= read -r profile; do
      desc="$(adk_get_profile_value "$profile" "description")"
      if match_keyword "$profile $desc" "$KEYWORD"; then
        emit_find_row "profile" "$profile" "$desc" "manifest.yaml"
      fi
    done < <(adk_list_profile_names)
  fi
}

adk_require_manifest

case "$ACTION" in
  build)
    build_catalog
    ;;
  find)
    case "$TYPE" in
      all|agent|skill|optional-skill|profile)
        ;;
      *)
        echo "[FAIL] unsupported --type: $TYPE" >&2
        exit 1
        ;;
    esac
    find_items
    ;;
  *)
    echo "[FAIL] unsupported action: $ACTION" >&2
    usage
    exit 1
    ;;
esac
