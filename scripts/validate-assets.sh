#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/validate-assets.sh [--strict] [--quick] [--summary-json]

Options:
  --strict   启用严格校验（名称一致性、描述必填等）
  --quick    快速预检（跳过 profile 解析关系）
  --summary-json  输出低 token JSON 摘要
  -h, --help
USAGE
}

STRICT=0
QUICK=0
SUMMARY_JSON=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT=1
      shift
      ;;
    --quick)
      QUICK=1
      shift
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

warn() {
  [[ "$SUMMARY_JSON" -eq 1 ]] && return 0
  echo "[WARN] $1" >&2
}

require_key() {
  local key="$1"
  grep -q "^$key:" "$ADK_MANIFEST" || fail "manifest missing top-level key: $key"
}

is_kebab_case() {
  local value="$1"
  [[ "$value" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

extract_frontmatter_scalar() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    NR==1 && $0=="---" {in_fm=1; next}
    in_fm && $0=="---" {exit}
    in_fm && $0 ~ "^" key ":" {
      value=$0
      sub("^" key ":[ ]*", "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$file"
}

validate_top_level_schema() {
  require_key "version"
  require_key "locale"
  require_key "platforms"
  require_key "tool_targets"
  require_key "quality_tiers"
  require_key "profiles"
  require_key "default_profile"
  require_key "agents"
  require_key "skills"
  require_key "workflows"
  require_key "mcp_servers"
  require_key "change_sets"
  require_key "optional_skills"
  require_key "install"
  require_key "dependencies"
}

list_quality_tier_names() {
  adk_section_block "quality_tiers" | awk '
    $0 ~ /^  [a-z0-9-]+:$/ {
      tier=$1
      sub(":", "", tier)
      print tier
    }
  '
}

quality_tier_exists() {
  local tier="$1"
  grep -Fxq "$tier" < <(list_quality_tier_names)
}

get_quality_tier_description() {
  local tier="$1"
  awk -v tier="$tier" '
    $0 ~ /^quality_tiers:/ {in_section=1; next}
    in_section && $0 ~ "^[^ ]" {in_section=0}
    in_section && $0 ~ "^  " tier ":" {in_tier=1; next}
    in_tier {
      if ($0 ~ /^  [a-z0-9-]+:/) {exit}
      if ($0 ~ /^    description:/) {
        value=$0
        sub("^    description:[ ]*", "", value)
        gsub(/^"|"$/, "", value)
        print value
        exit
      }
    }
  ' "$ADK_MANIFEST"
}

validate_quality_tiers() {
  mapfile -t tiers < <(list_quality_tier_names)
  [[ ${#tiers[@]} -gt 0 ]] || fail "manifest quality_tiers section is empty"

  local tier
  local desc
  for tier in "${tiers[@]}"; do
    is_kebab_case "$tier" || fail "invalid quality tier name: $tier"
    if [[ "$STRICT" -eq 1 ]]; then
      desc="$(get_quality_tier_description "$tier")"
      [[ -n "$desc" ]] || fail "quality tier '$tier' missing description in strict mode"
    fi
  done
}

validate_tool_targets() {
  mapfile -t tools < <(adk_list_tool_names)
  [[ ${#tools[@]} -gt 0 ]] || fail "manifest has no tool_targets"

  local tool
  for tool in "${tools[@]}"; do
    for key in display_name default_root agents_dir skills_dir; do
      value="$(adk_get_tool_value "$tool" "$key")"
      [[ -n "$value" ]] || fail "tool target '$tool' missing key: $key"
    done

    mapfile -t detect_markers < <(adk_get_tool_list "$tool" "detect")
    if [[ "$STRICT" -eq 1 && ${#detect_markers[@]} -eq 0 ]]; then
      fail "tool target '$tool' detect list is empty in strict mode"
    fi
  done

  if [[ "$(adk_get_tool_value "codex" "default_root")" != "~/codex" ]]; then
    fail "tool target 'codex' default_root must be ~/codex; direct ~/.codex install is forbidden"
  fi
  if adk_get_tool_list "codex" "detect" | grep -Fxq "~/.codex"; then
    fail "tool target 'codex' detect list must not use ~/.codex"
  fi
}

validate_agents_and_manifest_mapping() {
  mapfile -t dir_agents < <(find "$ROOT_DIR/agents" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
  [[ ${#dir_agents[@]} -gt 0 ]] || fail "no agents found in agents/"

  mapfile -t manifest_agents < <(adk_list_manifest_names "agents")
  [[ ${#manifest_agents[@]} -gt 0 ]] || fail "manifest agents section is empty"

  local name
  for name in "${dir_agents[@]}"; do
    is_kebab_case "$name" || fail "invalid agent dir name: $name"
    [[ -s "$ROOT_DIR/agents/$name/AGENTS.md" ]] || fail "missing or empty agent file: agents/$name/AGENTS.md"
    grep -Fxq "$name" <(printf '%s\n' "${manifest_agents[@]}") || fail "manifest missing agent: $name"
  done

  for name in "${manifest_agents[@]}"; do
    [[ -d "$ROOT_DIR/agents/$name" ]] || fail "manifest agent not found on disk: $name"
  done

  while IFS= read -r pair; do
    [[ -z "$pair" ]] && continue
    entry_name="${pair%% *}"
    entry_path="${pair#* }"
    [[ -f "$ROOT_DIR/$entry_path" ]] || fail "manifest agent path missing: $entry_name -> $entry_path"
  done < <(adk_list_manifest_paths "agents")
}

validate_skill_file() {
  local file="$1"
  local expected_name="$2"
  local section="$3"
  local frontmatter=""
  local declared_name=""
  local description=""

  [[ -s "$file" ]] || fail "missing or empty skill file: $file"

  frontmatter="$(awk '
    NR==1 && $0=="---" {flag=1; next}
    flag && $0=="---" {exit}
    flag {print}
  ' "$file")"
  [[ -n "$frontmatter" ]] || fail "missing frontmatter: $file"

  for key in name description triggers non_triggers inputs outputs constraints; do
    echo "$frontmatter" | grep -q "^$key:" || fail "frontmatter key '$key' missing: $file"
  done

  description="$(extract_frontmatter_scalar "$file" "description")"
  [[ -n "$description" ]] || fail "$section '$expected_name' description is empty: $file"
  if [[ "$STRICT" -eq 1 ]]; then
    [[ "${#description}" -ge 8 ]] || fail "$section '$expected_name' description too short for discovery: $description"
    if [[ "$description" =~ (TODO|TBD|FIXME|待补充|描述待定|示例技能|占位) ]]; then
      fail "$section '$expected_name' description contains placeholder text: $description"
    fi
    if [[ "$description" =~ ^(优化|改进|验证|测试|文档|流程|工具|助手)$ ]]; then
      fail "$section '$expected_name' description is too generic for discovery: $description"
    fi
  fi

  for key in triggers non_triggers inputs outputs constraints; do
    local count
    count="$(awk -v key="$key" '
      NR==1 && $0=="---" {in_fm=1; next}
      in_fm && $0=="---" {exit}
      in_fm && $0 ~ "^" key ":" {in_list=1; next}
      in_list && $0 ~ "^  - " {count++; next}
      in_list && $0 ~ "^[a-z_]+:" {in_list=0}
      END {print count+0}
    ' "$file")"
    [[ "$count" -gt 0 ]] || fail "$section '$expected_name' frontmatter list '$key' is empty: $file"
  done

  for heading in "## Goal" "## Workflow" "## Quality Gate"; do
    grep -q "^$heading$" "$file" || fail "$section '$expected_name' missing heading '$heading': $file"
  done

  if [[ "$STRICT" -eq 1 ]]; then
    declared_name="$(echo "$frontmatter" | awk '/^name:/ {print $2; exit}')"
    [[ "$declared_name" == "$expected_name" ]] || fail "$section '$expected_name' frontmatter name mismatch: $declared_name"
  fi
}

validate_skills_and_manifest_mapping() {
  mapfile -t dir_skills < <(find "$ROOT_DIR/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)
  [[ ${#dir_skills[@]} -gt 0 ]] || fail "no skills found in skills/"

  mapfile -t manifest_skills < <(adk_list_manifest_names "skills")
  [[ ${#manifest_skills[@]} -gt 0 ]] || fail "manifest skills section is empty"

  local name
  for name in "${dir_skills[@]}"; do
    is_kebab_case "$name" || fail "invalid skill dir name: $name"
    file="$ROOT_DIR/skills/$name/SKILL.md"
    validate_skill_file "$file" "$name" "skill"

    grep -Fxq "$name" <(printf '%s\n' "${manifest_skills[@]}") || fail "manifest missing skill: $name"
  done

  for name in "${manifest_skills[@]}"; do
    [[ -d "$ROOT_DIR/skills/$name" ]] || fail "manifest skill not found on disk: $name"
  done

  while IFS= read -r pair; do
    [[ -z "$pair" ]] && continue
    entry_name="${pair%% *}"
    entry_path="${pair#* }"
    [[ -f "$ROOT_DIR/$entry_path" ]] || fail "manifest skill path missing: $entry_name -> $entry_path"
  done < <(adk_list_manifest_paths "skills")
}

validate_optional_skills_mapping() {
  mapfile -t optional_names < <(adk_list_optional_skill_names)
  [[ ${#optional_names[@]} -gt 0 ]] || fail "manifest optional_skills section is empty"

  mapfile -t manifest_skills < <(adk_list_manifest_names "skills")

  local name
  for name in "${optional_names[@]}"; do
    is_kebab_case "$name" || fail "invalid optional skill name: $name"
    grep -Fxq "$name" <(printf '%s\n' "${manifest_skills[@]}") && fail "optional skill duplicates regular skill: $name"

    local path
    local file
    path="$(adk_get_optional_skill_path "$name")"
    [[ -n "$path" ]] || fail "optional skill '$name' missing path"
    file="$ROOT_DIR/$path"
    validate_skill_file "$file" "$name" "optional skill"
  done
}

validate_skill_description_uniqueness() {
  [[ "$STRICT" -eq 1 ]] || return 0

  declare -A seen_descriptions=()
  local file
  local desc
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    desc="$(extract_frontmatter_scalar "$file" "description")"
    [[ -n "$desc" ]] || continue
    if [[ -n "${seen_descriptions[$desc]:-}" ]]; then
      fail "duplicate skill description: '$desc' in ${seen_descriptions[$desc]#$ROOT_DIR/} and ${file#$ROOT_DIR/}"
    fi
    seen_descriptions[$desc]="$file"
  done < <(find "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" -name SKILL.md -type f | sort)
}

validate_manifest_quality_tiers() {
  local section="$1"
  local label="$2"

  mapfile -t names < <(adk_list_manifest_names "$section")
  [[ ${#names[@]} -gt 0 ]] || fail "manifest $section section is empty"

  local name
  local tier
  for name in "${names[@]}"; do
    tier="$(adk_get_manifest_item_value "$section" "$name" "quality_tier")"
    if [[ "$STRICT" -eq 1 ]]; then
      [[ -n "$tier" ]] || fail "$label '$name' missing quality_tier in strict mode"
    fi

    [[ -z "$tier" ]] && continue
    quality_tier_exists "$tier" || fail "$label '$name' has unknown quality_tier '$tier'"
  done
}

validate_existing_path() {
  local ref="$1"
  [[ -n "$ref" ]] || return 0

  case "$ref" in
    skills/*|docs/*|knowledge/*|rules/*|templates/*)
      [[ -e "$ROOT_DIR/$ref" ]] || fail "manifest references missing path: $ref"
      ;;
  esac
}

validate_context_layers() {
  [[ "$STRICT" -eq 1 ]] || return 0

  awk '
    /^context_layers:/ || /^embedded_context_layers:/ {in_section=1; next}
    in_section && /^[^ ]/ {in_section=0}
    in_section && /^[[:space:]]+- / {
      item=$0
      sub(/^[[:space:]]+- /, "", item)
      print item
    }
  ' "$ADK_MANIFEST" | while IFS= read -r ref; do
    validate_existing_path "$ref"
  done
}

validate_workflows() {
  [[ "$STRICT" -eq 1 ]] || return 0

  mapfile -t workflows < <(adk_list_manifest_names "workflows")
  [[ ${#workflows[@]} -gt 0 ]] || fail "manifest workflows section is empty"

  local name
  for name in "${workflows[@]}"; do
    is_kebab_case "$name" || fail "invalid workflow name: $name"

    local desc
    desc="$(adk_get_manifest_item_value "workflows" "$name" "description")"
    [[ -n "$desc" ]] || fail "workflow '$name' missing description"

    local item
    while IFS= read -r item; do
      [[ -z "$item" ]] && continue
      [[ -d "$ROOT_DIR/agents/$item" ]] || fail "workflow '$name' references unknown agent '$item'"
    done < <(adk_get_manifest_item_list "workflows" "$name" "agents")

    while IFS= read -r item; do
      [[ -z "$item" ]] && continue
      [[ -d "$ROOT_DIR/skills/$item" ]] || fail "workflow '$name' references unknown skill '$item'"
    done < <(adk_get_manifest_item_list "workflows" "$name" "skills")
  done
}

validate_mcp_servers() {
  [[ "$STRICT" -eq 1 ]] || return 0

  if grep -q '^mcp_servers:[[:space:]]*\[\][[:space:]]*$' "$ADK_MANIFEST"; then
    return 0
  fi

  mapfile -t servers < <(adk_list_manifest_names "mcp_servers")
  local name command transport risk_level
  for name in "${servers[@]}"; do
    is_kebab_case "$name" || fail "invalid MCP server name: $name"
    command="$(adk_get_manifest_item_value "mcp_servers" "$name" "command")"
    transport="$(adk_get_manifest_item_value "mcp_servers" "$name" "transport")"
    risk_level="$(adk_get_manifest_item_value "mcp_servers" "$name" "risk_level")"
    [[ -n "$command" ]] || fail "MCP server '$name' missing command"
    [[ -n "$transport" ]] || fail "MCP server '$name' missing transport"
    [[ "$transport" =~ ^(stdio|http|sse)$ ]] || fail "MCP server '$name' has invalid transport '$transport'"
    [[ "$risk_level" =~ ^(low|medium|high)$ ]] || fail "MCP server '$name' must declare risk_level low|medium|high"
  done
}

validate_change_sets() {
  [[ "$STRICT" -eq 1 ]] || return 0

  mapfile -t change_sets < <(adk_list_manifest_names "change_sets")
  [[ ${#change_sets[@]} -gt 0 ]] || fail "manifest change_sets section is empty"

  local name root archive_root
  for name in "${change_sets[@]}"; do
    is_kebab_case "$name" || fail "invalid change set name: $name"
    root="$(adk_get_manifest_item_value "change_sets" "$name" "root")"
    archive_root="$(adk_get_manifest_item_value "change_sets" "$name" "archive_root")"
    [[ -n "$root" ]] || fail "change set '$name' missing root"
    [[ -d "$ROOT_DIR/$root" ]] || fail "change set '$name' root missing: $root"
    [[ -n "$archive_root" ]] || fail "change set '$name' missing archive_root"
    [[ -d "$ROOT_DIR/$archive_root" ]] || fail "change set '$name' archive_root missing: $archive_root"

    local count
    count="$(adk_get_manifest_item_list "change_sets" "$name" "required_files" | awk 'END {print NR+0}')"
    [[ "$count" -gt 0 ]] || fail "change set '$name' required_files is empty"
  done
}

validate_skill_entry_size() {
  [[ "$STRICT" -eq 1 ]] || return 0

  local file
  local lines
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    lines="$(wc -l < "$file")"
    [[ "$lines" -le 140 ]] || fail "skill entry exceeds 140 lines: ${file#$ROOT_DIR/} (${lines})"
  done < <(find "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" -name SKILL.md -type f | sort)
}

validate_profiles() {
  mapfile -t profiles < <(adk_list_profile_names)
  [[ ${#profiles[@]} -gt 0 ]] || fail "manifest has no profiles"

  default_profile="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
  [[ -n "$default_profile" ]] || fail "default_profile is empty"
  adk_profile_exists "$default_profile" || fail "default_profile not found in profiles: $default_profile"

  local profile
  for profile in "${profiles[@]}"; do
    if [[ "$STRICT" -eq 1 ]]; then
      desc="$(adk_get_profile_value "$profile" "description")"
      [[ -n "$desc" ]] || fail "profile '$profile' missing description in strict mode"
    fi

    mapfile -t parents < <(adk_get_profile_list "$profile" "extends")
    for parent in "${parents[@]}"; do
      adk_profile_exists "$parent" || fail "profile '$profile' extends missing profile '$parent'"
    done

    mapfile -t agents < <(adk_resolve_profile_items "$profile" "include_agents")
    mapfile -t skills < <(adk_resolve_profile_items "$profile" "include_skills")

    [[ ${#agents[@]} -gt 0 ]] || fail "profile '$profile' resolves to zero agents"
    [[ ${#skills[@]} -gt 0 ]] || fail "profile '$profile' resolves to zero skills"

    for item in "${agents[@]}"; do
      [[ -d "$ROOT_DIR/agents/$item" ]] || fail "profile '$profile' references unknown agent '$item'"
    done

    for item in "${skills[@]}"; do
      [[ -d "$ROOT_DIR/skills/$item" ]] || fail "profile '$profile' references unknown skill '$item'"
    done
  done
}

validate_top_level_schema
validate_quality_tiers
validate_tool_targets
validate_agents_and_manifest_mapping
validate_skills_and_manifest_mapping
validate_optional_skills_mapping
validate_skill_description_uniqueness
validate_manifest_quality_tiers "agents" "agent"
validate_manifest_quality_tiers "skills" "skill"
validate_manifest_quality_tiers "optional_skills" "optional skill"
validate_context_layers
validate_workflows
validate_mcp_servers
validate_change_sets
validate_skill_entry_size
if [[ "$STRICT" -eq 1 ]]; then
  "$ROOT_DIR/scripts/check-runtime-boundary.sh" >/dev/null
  default_profile_for_workflow="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
  "$ROOT_DIR/scripts/check-workflow-closure.sh" --profile "$default_profile_for_workflow" >/dev/null
fi
if [[ "$QUICK" -eq 1 ]]; then
  warn "quick mode enabled: skipped profile dependency validation"
else
  validate_profiles
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"pass","strict":%s,"quick":%s,"agents":%s,"skills":%s,"optional_skills":%s,"profiles":%s,"workflows":%s,"change_sets":%s}\n' \
    "$STRICT" \
    "$QUICK" \
    "$(adk_list_manifest_names "agents" | awk 'END {print NR+0}')" \
    "$(adk_list_manifest_names "skills" | awk 'END {print NR+0}')" \
    "$(adk_list_manifest_names "optional_skills" | awk 'END {print NR+0}')" \
    "$(adk_list_profile_names | awk 'END {print NR+0}')" \
    "$(adk_list_manifest_names "workflows" | awk 'END {print NR+0}')" \
    "$(adk_list_manifest_names "change_sets" | awk 'END {print NR+0}')"
else
  echo "Validation passed. strict=$STRICT quick=$QUICK"
fi
