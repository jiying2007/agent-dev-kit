#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/convert-assets.sh --target codex|claude-code|hermes-agent|opencode [options]

Options:
  --profile <profile name>
  --extra-profile <profile name>   # 可重复
  --with-optional-skill <skill>    # 可重复
  --codex-profile <profile name>   # 可重复；target=codex 时写入 ~/codex manifest 的 profile，默认 team-collab
  --list-optional-skills
  --out <output dir>               # 默认 dist
  --clean
  --dry-run
  --summary-json
  -h, --help

Example:
  ./scripts/convert-assets.sh --target claude-code --profile core --out dist
  ./scripts/convert-assets.sh --target codex --profile core --with-optional-skill adk-incident-rca-report
USAGE
}

TARGET=""
PROFILE=""
EXTRA_PROFILES=()
OPTIONAL_SKILLS=()
CODEX_PROFILES=()
OUT_DIR="$ROOT_DIR/dist"
CLEAN=0
DRY_RUN=0
LIST_OPTIONAL_SKILLS=0
SUMMARY_JSON=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET="$2"
      shift 2
      ;;
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
    --codex-profile)
      CODEX_PROFILES+=("$2")
      shift 2
      ;;
    --list-optional-skills)
      LIST_OPTIONAL_SKILLS=1
      shift
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --clean)
      CLEAN=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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
      echo "[FAIL] Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

resolve_destination() {
  local kind="$1"
  local name="$2"

  case "$TARGET" in
    codex)
      echo ""
      ;;
    claude-code)
      echo "$OUT_DIR/$TARGET/$kind/$name.md"
      ;;
    hermes-agent)
      if [[ "$kind" == "agent" ]]; then
        echo "$OUT_DIR/$TARGET/agents/$name/instructions.md"
      else
        echo "$OUT_DIR/$TARGET/skills/$name/SKILL.md"
      fi
      ;;
    opencode)
      echo "$OUT_DIR/$TARGET/prompts/$kind/$name.md"
      ;;
    *)
      echo ""
      ;;
  esac
}

json_string() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\t'/\\t}"
  printf '"%s"' "$value"
}

json_array() {
  local first=1
  local item
  printf '['
  for item in "$@"; do
    if [[ "$first" -eq 0 ]]; then
      printf ', '
    fi
    json_string "$item"
    first=0
  done
  printf ']'
}

frontmatter_value() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '
    NR == 1 && $0 == "---" {in_fm=1; next}
    in_fm && $0 == "---" {exit}
    in_fm && $0 ~ "^" key ":" {
      value=$0
      sub("^" key ":[ ]*", "", value)
      gsub(/^"|"$/, "", value)
      print value
      exit
    }
  ' "$file"
}

copy_tree_contents() {
  local src_dir="$1"
  local dst_dir="$2"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] copy codex source tree: $src_dir -> $dst_dir"
    return
  fi

  mkdir -p "$dst_dir"
  cp -a "$src_dir"/. "$dst_dir"/
}

yaml_single_quote() {
  local value="$1"
  value="${value//\'/\'\'}"
  printf "'%s'" "$value"
}

ensure_codex_skill_support_files() {
  local dst_dir="$1"
  local skill_md="$2"
  local name="$3"
  local source_path="$4"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] ensure codex skill support files: $dst_dir"
    return
  fi

  local description version
  description="$(frontmatter_value "$skill_md" "description")"
  version="$(frontmatter_value "$skill_md" "version")"
  [[ -n "$description" ]] || description="$name"
  [[ -n "$version" ]] || version="$MANIFEST_VERSION"

  if [[ ! -f "$dst_dir/README.md" ]]; then
    cat > "$dst_dir/README.md" <<EOF
# $name

$description

- Version: $version
- Source: llm_agent/agent-dev-kit/$source_path
- Target: ~/codex vendor skill handoff
EOF
  fi

  if [[ ! -f "$dst_dir/LICENSE" && ! -f "$dst_dir/LICENSE.txt" ]]; then
    if [[ -f "$ROOT_DIR/LICENSE" ]]; then
      cp "$ROOT_DIR/LICENSE" "$dst_dir/LICENSE"
    else
      printf 'See llm_agent/agent-dev-kit source repository license.\n' > "$dst_dir/LICENSE"
    fi
  fi

  if [[ ! -f "$dst_dir/agents/openai.yaml" ]]; then
    mkdir -p "$dst_dir/agents"
    {
      printf 'display_name: '
      yaml_single_quote "$name"
      printf '\nshort_description: '
      yaml_single_quote "$description"
      printf '\n'
    } > "$dst_dir/agents/openai.yaml"
  fi
}

CODEX_AGENT_ENTRIES=()
CODEX_SKILL_ENTRIES=()
CODEX_WORKFLOW_ENTRIES=()
CODEX_MCP_ENTRIES=()
CODEX_CHANGE_SET_ENTRIES=()

add_codex_agent_entry() {
  local name="$1"
  local version="$2"
  local vendor_rel="$3"
  local target_rel="$4"
  local source_path="$5"
  local description="$6"
  local imported_at="$7"

  local j_name j_version j_vendor_rel j_target_rel j_profiles j_source_path j_description j_imported_at
  j_name="$(json_string "$name")"
  j_version="$(json_string "$version")"
  j_vendor_rel="$(json_string "$vendor_rel")"
  j_target_rel="$(json_string "$target_rel")"
  j_profiles="$(json_array "${CODEX_PROFILES[@]}")"
  j_source_path="$(json_string "$source_path")"
  j_description="$(json_string "$description")"
  j_imported_at="$(json_string "$imported_at")"

  CODEX_AGENT_ENTRIES+=("{\"name\": ${j_name}, \"enabled\": true, \"source_kind\": \"vendor\", \"version\": ${j_version}, \"vendor_rel\": ${j_vendor_rel}, \"target_rel\": ${j_target_rel}, \"profiles\": ${j_profiles}, \"description\": ${j_description}, \"source_repo\": \"llm_agent/agent-dev-kit\", \"source_ref\": ${j_version}, \"source_path\": ${j_source_path}, \"imported_at\": ${j_imported_at}, \"review_status\": \"accepted\"}")
}

add_codex_skill_entry() {
  local name="$1"
  local version="$2"
  local vendor_rel="$3"
  local target_rel="$4"
  local source_path="$5"
  local imported_at="$6"
  local quality_tier="$7"

  local j_name j_version j_vendor_rel j_target_rel j_profiles j_source_path j_imported_at j_quality_tier j_manifest_version
  j_name="$(json_string "$name")"
  j_version="$(json_string "$version")"
  j_vendor_rel="$(json_string "$vendor_rel")"
  j_target_rel="$(json_string "$target_rel")"
  j_profiles="$(json_array "${CODEX_PROFILES[@]}")"
  j_source_path="$(json_string "$source_path")"
  j_imported_at="$(json_string "$imported_at")"
  j_quality_tier="$(json_string "$quality_tier")"
  j_manifest_version="$(json_string "$MANIFEST_VERSION")"

  CODEX_SKILL_ENTRIES+=("{\"name\": ${j_name}, \"enabled\": true, \"source_kind\": \"vendor\", \"version\": ${j_version}, \"vendor_rel\": ${j_vendor_rel}, \"target_rel\": ${j_target_rel}, \"profiles\": ${j_profiles}, \"tags\": [\"agent-dev-kit\", \"adk\", ${j_quality_tier}], \"owner\": \"agent-dev-kit\", \"source_repo\": \"llm_agent/agent-dev-kit\", \"source_ref\": ${j_manifest_version}, \"source_path\": ${j_source_path}, \"imported_at\": ${j_imported_at}, \"review_status\": \"accepted\"}")
}

add_codex_workflow_entry() {
  local name="$1"
  local description="$2"
  local imported_at="$3"
  local triggers=()
  local skills=()
  local agents=()
  local commands=()
  local verification=()

  mapfile -t triggers < <(adk_get_manifest_item_list "workflows" "$name" "triggers")
  mapfile -t skills < <(adk_get_manifest_item_list "workflows" "$name" "skills")
  mapfile -t agents < <(adk_get_manifest_item_list "workflows" "$name" "agents")
  mapfile -t commands < <(adk_get_manifest_item_list "workflows" "$name" "commands")
  mapfile -t verification < <(adk_get_manifest_item_list "workflows" "$name" "verification")

  CODEX_WORKFLOW_ENTRIES+=("{\"name\": $(json_string "$name"), \"enabled\": true, \"profiles\": $(json_array "${CODEX_PROFILES[@]}"), \"triggers\": $(json_array "${triggers[@]}"), \"skills\": $(json_array "${skills[@]}"), \"agents\": $(json_array "${agents[@]}"), \"commands\": $(json_array "${commands[@]}"), \"verification\": $(json_array "${verification[@]}"), \"description\": $(json_string "$description"), \"source_repo\": \"llm_agent/agent-dev-kit\", \"source_ref\": $(json_string "$MANIFEST_VERSION"), \"imported_at\": $(json_string "$imported_at")}")
}

add_codex_mcp_entry() {
  local name="$1"
  local imported_at="$2"
  local command transport description risk_level
  local args=()

  command="$(adk_get_manifest_item_value "mcp_servers" "$name" "command")"
  transport="$(adk_get_manifest_item_value "mcp_servers" "$name" "transport")"
  description="$(adk_get_manifest_item_value "mcp_servers" "$name" "description")"
  risk_level="$(adk_get_manifest_item_value "mcp_servers" "$name" "risk_level")"
  mapfile -t args < <(adk_get_manifest_item_list "mcp_servers" "$name" "args")

  CODEX_MCP_ENTRIES+=("{\"name\": $(json_string "$name"), \"enabled\": false, \"transport\": $(json_string "$transport"), \"command\": $(json_string "$command"), \"args\": $(json_array "${args[@]}"), \"description\": $(json_string "$description"), \"risk_level\": $(json_string "$risk_level"), \"source_repo\": \"llm_agent/agent-dev-kit\", \"source_ref\": $(json_string "$MANIFEST_VERSION"), \"imported_at\": $(json_string "$imported_at"), \"review_status\": \"requires-codex-approval\"}")
}

add_codex_change_set_entry() {
  local name="$1"
  local imported_at="$2"
  local description root archive_root
  local commands=()
  local required_files=()

  description="$(adk_get_manifest_item_value "change_sets" "$name" "description")"
  root="$(adk_get_manifest_item_value "change_sets" "$name" "root")"
  archive_root="$(adk_get_manifest_item_value "change_sets" "$name" "archive_root")"
  mapfile -t commands < <(adk_get_manifest_item_list "change_sets" "$name" "commands")
  mapfile -t required_files < <(adk_get_manifest_item_list "change_sets" "$name" "required_files")

  CODEX_CHANGE_SET_ENTRIES+=("{\"name\": $(json_string "$name"), \"enabled\": true, \"profiles\": $(json_array "${CODEX_PROFILES[@]}"), \"root\": $(json_string "$root"), \"archive_root\": $(json_string "$archive_root"), \"commands\": $(json_array "${commands[@]}"), \"required_files\": $(json_array "${required_files[@]}"), \"description\": $(json_string "$description"), \"source_repo\": \"llm_agent/agent-dev-kit\", \"source_ref\": $(json_string "$MANIFEST_VERSION"), \"imported_at\": $(json_string "$imported_at")}")
}

write_codex_fragment() {
  local output="$1"
  local key="$2"
  shift 2
  local entries=("$@")

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] write codex manifest fragment: $output"
    return
  fi

  mkdir -p "$(dirname "$output")"
  {
    echo "{"
    echo '  "schema_version": 2,'
    echo "  \"${key}\": ["
    local i
    for i in "${!entries[@]}"; do
      printf '    %s' "${entries[$i]}"
      if [[ "$i" -lt "$((${#entries[@]} - 1))" ]]; then
        printf ','
      fi
      printf '\n'
    done
    echo "  ]"
    echo "}"
  } > "$output"
}

write_codex_handoff_doc() {
  local output="$TARGET_DIR/CODEX_HANDOFF.md"

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] write codex handoff doc: $output"
    return
  fi

  cat > "$output" <<EOF
# agent-dev-kit Codex Handoff

本目录是给 \`~/codex\` 使用的交接产物，不是 \`~/.codex\` 运行目录。

## 目录契约

- \`src/codex-home/vendor/skills/<name>/<version>/\`：符合 \`~/codex\` skill vendor 源资产路径。
- \`src/codex-home/vendor/agents/agent-dev-kit/<adk-version>/<name>/AGENTS.md\`：符合 \`~/codex\` agent vendor 源资产路径。
- \`manifest-fragments/skills.json\`：可合并进 \`~/codex/manifests/skills.json\` 的 skill 条目。
- \`manifest-fragments/agents.json\`：可合并进 \`~/codex/manifests/agents.json\` 的 agent 条目。
- \`manifest-fragments/workflows.json\`：可合并进 \`~/codex/manifests/workflows.json\` 的 workflow 条目。
- \`manifest-fragments/mcp_servers.json\`：可合并进 \`~/codex/manifests/mcp_servers.json\` 的 MCP 声明；当前为空表示 adk 不隐式安装 MCP。
- \`manifest-fragments/change_sets.json\`：可合并进 \`~/codex/manifests/change_sets.json\` 的变更工件治理条目。

## 交接纪律

不要把本目录直接复制到 \`~/.codex\`。应先把源资产和 manifest fragment 合并到 \`~/codex\`，再运行：

\`\`\`bash
rtk bash scripts/build.sh --profile team-collab
rtk bash scripts/doctor.sh --scope repo
rtk bash scripts/doctor.sh --scope build
rtk bash scripts/apply.sh --profile team-collab --dry-run
\`\`\`

生成参数：

- adk profiles: ${ALL_PROFILES[*]}
- codex profiles: ${CODEX_PROFILES[*]}
- agents: ${#AGENTS_TO_EXPORT[@]}
- skills: ${#SKILLS_TO_EXPORT[@]}
- optional skills: ${#OPTIONAL_SKILLS[@]}
- workflows: ${#CODEX_WORKFLOW_ENTRIES[@]}
- mcp servers: ${#CODEX_MCP_ENTRIES[@]}
- change sets: ${#CODEX_CHANGE_SET_ENTRIES[@]}
EOF
}

export_codex_agent() {
  local name="$1"
  local src="$ROOT_DIR/agents/$name/AGENTS.md"
  local source_dir
  source_dir="$(dirname "$src")"
  local source_path
  source_path="$(adk_get_manifest_item_value "agents" "$name" "path")"
  [[ -n "$source_path" ]] || source_path="agents/$name/AGENTS.md"
  local description
  description="$(adk_get_manifest_item_value "agents" "$name" "description")"
  [[ -n "$description" ]] || description="$name"
  local vendor_dir="vendor/agents/agent-dev-kit/$MANIFEST_VERSION/$name"
  local vendor_rel="$vendor_dir/AGENTS.md"
  local target_rel="agents/$name/AGENTS.md"

  copy_tree_contents "$source_dir" "$TARGET_DIR/src/codex-home/$vendor_dir"
  add_codex_agent_entry "$name" "$MANIFEST_VERSION" "$vendor_rel" "$target_rel" "$source_path" "$description" "$IMPORTED_AT"
}

export_codex_skill() {
  local section="$1"
  local name="$2"
  local source_path="$3"
  local src="$ROOT_DIR/$source_path"
  local source_dir
  source_dir="$(dirname "$src")"
  local version
  version="$(frontmatter_value "$src" "version")"
  [[ -n "$version" ]] || version="$MANIFEST_VERSION"
  local quality_tier
  quality_tier="$(adk_get_manifest_item_value "$section" "$name" "quality_tier")"
  [[ -n "$quality_tier" ]] || quality_tier="adk"
  local vendor_dir="vendor/skills/$name/$version"
  local target_rel="skills/$name"

  copy_tree_contents "$source_dir" "$TARGET_DIR/src/codex-home/$vendor_dir"
  ensure_codex_skill_support_files "$TARGET_DIR/src/codex-home/$vendor_dir" "$src" "$name" "$source_path"
  add_codex_skill_entry "$name" "$version" "$vendor_dir" "$target_rel" "$source_path" "$IMPORTED_AT" "$quality_tier"
}

export_codex_handoff() {
  if [[ "${#CODEX_PROFILES[@]}" -eq 0 ]]; then
    CODEX_PROFILES=("team-collab")
  fi

  "$ROOT_DIR/scripts/check-workflow-closure.sh" --profile "$PROFILE" \
    "${EXTRA_PROFILE_CLOSURE_ARGS[@]}" \
    "${OPTIONAL_SKILL_CLOSURE_ARGS[@]}" >/dev/null

  local name
  for name in "${AGENTS_TO_EXPORT[@]}"; do
    export_codex_agent "$name"
  done

  for name in "${SKILLS_TO_EXPORT[@]}"; do
    local source_path
    source_path="$(adk_get_manifest_item_value "skills" "$name" "path")"
    [[ -n "$source_path" ]] || { echo "[FAIL] skill path missing: $name" >&2; exit 1; }
    export_codex_skill "skills" "$name" "$source_path"
  done

  for name in "${OPTIONAL_SKILLS[@]}"; do
    local optional_path
    optional_path="$(adk_get_optional_skill_path "$name")"
    [[ -n "$optional_path" ]] || { echo "[FAIL] optional skill path missing: $name" >&2; exit 1; }
    export_codex_skill "optional_skills" "$name" "$optional_path"
  done

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    local description
    description="$(adk_get_manifest_item_value "workflows" "$name" "description")"
    [[ -n "$description" ]] || description="$name"
    add_codex_workflow_entry "$name" "$description" "$IMPORTED_AT"
  done < <(adk_list_manifest_names "workflows")

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    add_codex_mcp_entry "$name" "$IMPORTED_AT"
  done < <(adk_list_manifest_names "mcp_servers")

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    add_codex_change_set_entry "$name" "$IMPORTED_AT"
  done < <(adk_list_manifest_names "change_sets")

  write_codex_fragment "$TARGET_DIR/manifest-fragments/agents.json" "agents" "${CODEX_AGENT_ENTRIES[@]}"
  write_codex_fragment "$TARGET_DIR/manifest-fragments/skills.json" "skills" "${CODEX_SKILL_ENTRIES[@]}"
  write_codex_fragment "$TARGET_DIR/manifest-fragments/workflows.json" "workflows" "${CODEX_WORKFLOW_ENTRIES[@]}"
  write_codex_fragment "$TARGET_DIR/manifest-fragments/mcp_servers.json" "mcp_servers" "${CODEX_MCP_ENTRIES[@]}"
  write_codex_fragment "$TARGET_DIR/manifest-fragments/change_sets.json" "change_sets" "${CODEX_CHANGE_SET_ENTRIES[@]}"
  write_codex_handoff_doc
}

write_with_metadata() {
  local src="$1"
  local dst="$2"
  local kind="$3"
  local name="$4"

  if [[ "$TARGET" == "codex" ]]; then
    adk_run_cmd cp -a "$src" "$dst"
    return
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] write converted file: $dst"
    return
  fi

  {
    echo "---"
    echo "name: $name"
    echo "kind: $kind"
    echo "target: $TARGET"
    echo "source: ${src#$ROOT_DIR/}"
    echo "converted_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "---"
    echo
    awk '
      NR==1 && $0=="---" {in_frontmatter=1; next}
      in_frontmatter && $0=="---" {in_frontmatter=0; next}
      in_frontmatter {next}
      {print}
    ' "$src"
  } > "$dst"
}

adk_require_manifest

if [[ "$LIST_OPTIONAL_SKILLS" -eq 1 ]]; then
  adk_list_optional_skill_names
  exit 0
fi

if [[ -z "$TARGET" ]]; then
  echo "[FAIL] --target is required" >&2
  exit 1
fi

case "$TARGET" in
  codex|claude-code|hermes-agent|opencode)
    ;;
  *)
    echo "[FAIL] unsupported target: $TARGET" >&2
    exit 1
    ;;
esac

if [[ -z "$PROFILE" ]]; then
  PROFILE="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
  [[ -n "$PROFILE" ]] || PROFILE="embedded-fullstack"
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
EXTRA_PROFILE_CLOSURE_ARGS=()
OPTIONAL_SKILL_CLOSURE_ARGS=()
for profile in "${EXTRA_PROFILES[@]}"; do
  EXTRA_PROFILE_CLOSURE_ARGS+=(--extra-profile "$profile")
done
for skill in "${OPTIONAL_SKILLS[@]}"; do
  OPTIONAL_SKILL_CLOSURE_ARGS+=(--with-optional-skill "$skill")
done
MANIFEST_VERSION="$(awk '/^version:/ {print $2; exit}' "$ADK_MANIFEST")"
[[ -n "$MANIFEST_VERSION" ]] || MANIFEST_VERSION="0.0.0"
IMPORTED_AT="$(date -u +%F)"
mapfile -t AGENTS_TO_EXPORT < <(adk_resolve_profile_items_all "include_agents" "${ALL_PROFILES[@]}")
mapfile -t SKILLS_TO_EXPORT < <(adk_resolve_profile_items_all "include_skills" "${ALL_PROFILES[@]}")

TARGET_DIR="$OUT_DIR/$TARGET"
if [[ "$CLEAN" -eq 1 ]]; then
  adk_run_cmd rm -rf "$TARGET_DIR"
fi

if [[ "$TARGET" == "codex" ]]; then
  export_codex_handoff
  if [[ "$SUMMARY_JSON" -eq 1 ]]; then
    printf '{"schema_version":1,"status":"pass","target":"%s","out":%s,"profiles":%s,"codex_profiles":%s,"agents":%s,"skills":%s,"optional_skills":%s,"workflows":%s,"mcp_servers":%s,"change_sets":%s}\n' \
      "$TARGET" \
      "$(json_string "$TARGET_DIR")" \
      "$(json_array "${ALL_PROFILES[@]}")" \
      "$(json_array "${CODEX_PROFILES[@]}")" \
      "${#AGENTS_TO_EXPORT[@]}" \
      "${#SKILLS_TO_EXPORT[@]}" \
      "${#OPTIONAL_SKILLS[@]}" \
      "${#CODEX_WORKFLOW_ENTRIES[@]}" \
      "${#CODEX_MCP_ENTRIES[@]}" \
      "${#CODEX_CHANGE_SET_ENTRIES[@]}"
  else
    echo "Convert completed"
    echo "  target=$TARGET"
    echo "  out=$TARGET_DIR"
    echo "  profiles=${ALL_PROFILES[*]}"
    echo "  codex_profiles=${CODEX_PROFILES[*]}"
    echo "  agents=${#AGENTS_TO_EXPORT[@]} skills=${#SKILLS_TO_EXPORT[@]} optional_skills=${#OPTIONAL_SKILLS[@]}"
    echo "  workflows=${#CODEX_WORKFLOW_ENTRIES[@]} mcp_servers=${#CODEX_MCP_ENTRIES[@]} change_sets=${#CODEX_CHANGE_SET_ENTRIES[@]}"
  fi
  exit 0
fi

for name in "${AGENTS_TO_EXPORT[@]}"; do
  src="$ROOT_DIR/agents/$name/AGENTS.md"
  dst="$(resolve_destination "agent" "$name")"
  [[ -n "$dst" ]] || { echo "[FAIL] failed to resolve destination for agent: $name" >&2; exit 1; }
  adk_run_cmd mkdir -p "$(dirname "$dst")"
  write_with_metadata "$src" "$dst" "agent" "$name"
done

for name in "${SKILLS_TO_EXPORT[@]}"; do
  src="$ROOT_DIR/skills/$name/SKILL.md"
  dst="$(resolve_destination "skill" "$name")"
  [[ -n "$dst" ]] || { echo "[FAIL] failed to resolve destination for skill: $name" >&2; exit 1; }
  adk_run_cmd mkdir -p "$(dirname "$dst")"
  write_with_metadata "$src" "$dst" "skill" "$name"
done

for name in "${OPTIONAL_SKILLS[@]}"; do
  optional_path="$(adk_get_optional_skill_path "$name")"
  [[ -n "$optional_path" ]] || { echo "[FAIL] optional skill path missing: $name" >&2; exit 1; }
  src="$ROOT_DIR/$optional_path"
  dst="$(resolve_destination "skill" "$name")"
  [[ -n "$dst" ]] || { echo "[FAIL] failed to resolve destination for optional skill: $name" >&2; exit 1; }
  adk_run_cmd mkdir -p "$(dirname "$dst")"
  write_with_metadata "$src" "$dst" "skill" "$name"
done

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"schema_version":1,"status":"pass","target":"%s","out":%s,"profiles":%s,"agents":%s,"skills":%s,"optional_skills":%s}\n' \
    "$TARGET" \
    "$(json_string "$TARGET_DIR")" \
    "$(json_array "${ALL_PROFILES[@]}")" \
    "${#AGENTS_TO_EXPORT[@]}" \
    "${#SKILLS_TO_EXPORT[@]}" \
    "${#OPTIONAL_SKILLS[@]}"
else
  echo "Convert completed"
  echo "  target=$TARGET"
  echo "  out=$TARGET_DIR"
  echo "  profiles=${ALL_PROFILES[*]}"
  echo "  agents=${#AGENTS_TO_EXPORT[@]} skills=${#SKILLS_TO_EXPORT[@]} optional_skills=${#OPTIONAL_SKILLS[@]}"
fi
