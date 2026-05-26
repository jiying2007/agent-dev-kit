#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/convert-assets.sh --target claude-code|hermes-agent|opencode [options]

Options:
  --profile <profile name>
  --extra-profile <profile name>   # 可重复
  --with-optional-skill <skill>    # 可重复
  --list-optional-skills
  --out <output dir>               # 默认 dist
  --clean
  --dry-run
  --summary-json
  -h, --help

Examples:
  ./scripts/convert-assets.sh --target claude-code --profile core --out dist
  ./scripts/convert-assets.sh --target opencode --profile core --with-optional-skill adk-incident-rca-report
USAGE
}

TARGET=""
PROFILE=""
EXTRA_PROFILES=()
OPTIONAL_SKILLS=()
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

write_with_metadata() {
  local src="$1"
  local dst="$2"
  local kind="$3"
  local name="$4"

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
  claude-code|hermes-agent|opencode)
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
MANIFEST_VERSION="$(awk '/^version:/ {print $2; exit}' "$ADK_MANIFEST")"
[[ -n "$MANIFEST_VERSION" ]] || MANIFEST_VERSION="0.0.0"
mapfile -t AGENTS_TO_EXPORT < <(adk_resolve_profile_items_all "include_agents" "${ALL_PROFILES[@]}")
mapfile -t SKILLS_TO_EXPORT < <(adk_resolve_profile_items_all "include_skills" "${ALL_PROFILES[@]}")

TARGET_DIR="$OUT_DIR/$TARGET"
if [[ "$CLEAN" -eq 1 ]]; then
  adk_run_cmd rm -rf "$TARGET_DIR"
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
