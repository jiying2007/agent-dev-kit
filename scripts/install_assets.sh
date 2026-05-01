#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib_manifest.sh
source "$SCRIPT_DIR/lib_manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/install_assets.sh [options]

Options:
  --tool auto|codex|claude-code|hermes-agent|opencode
  --mode copy|symlink
  --target <tool root path>
  --profile <profile name>
  --extra-profile <profile name>   # 可重复
  --with-optional-skill <skill>    # 可重复
  --list-tools
  --list-profiles
  --list-optional-skills
  --dry-run
  -h, --help

Examples:
  ./scripts/install_assets.sh --tool auto --mode symlink --profile embedded-fullstack
  ./scripts/install_assets.sh --tool codex --target ~/.codex --profile core --extra-profile release-hardening
  ./scripts/install_assets.sh --tool codex --profile core --with-optional-skill test-flakiness-triage
USAGE
}

TOOL="auto"
MODE="symlink"
TARGET=""
PROFILE=""
EXTRA_PROFILES=()
OPTIONAL_SKILLS=()
DRY_RUN=0
LIST_TOOLS=0
LIST_PROFILES=0
LIST_OPTIONAL_SKILLS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool)
      TOOL="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
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
    --list-tools)
      LIST_TOOLS=1
      shift
      ;;
    --list-profiles)
      LIST_PROFILES=1
      shift
      ;;
    --list-optional-skills)
      LIST_OPTIONAL_SKILLS=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
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

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    "$@"
  fi
}

expand_path() {
  local raw="$1"
  local expanded="$raw"
  expanded="${expanded/#\~/$HOME}"
  # 仅展开受信任 manifest 中定义的环境变量占位
  eval "printf '%s' \"$expanded\""
}

detect_tool_auto() {
  local tool
  while IFS= read -r tool; do
    [[ -z "$tool" ]] && continue
    local marker
    while IFS= read -r marker; do
      [[ -z "$marker" ]] && continue
      local probe
      probe="$(expand_path "$marker")"
      if [[ -n "$probe" && -e "$probe" ]]; then
        echo "$tool"
        return 0
      fi
    done < <(gdk_get_tool_list "$tool" "detect")
  done < <(gdk_list_tool_names)

  echo "codex"
}

resolve_profile_items() {
  local key="$1"
  shift
  local profiles=("$@")
  local profile
  for profile in "${profiles[@]}"; do
    gdk_resolve_profile_items "$profile" "$key"
  done | awk 'NF' | sort -u
}

install_item() {
  local src="$1"
  local dst="$2"

  if [[ ! -e "$src" ]]; then
    echo "[FAIL] source not found: $src" >&2
    exit 1
  fi

  run_cmd rm -rf "$dst"
  if [[ "$MODE" == "copy" ]]; then
    run_cmd cp -a "$src" "$dst"
  else
    run_cmd ln -s "$src" "$dst"
  fi
}

gdk_require_manifest

if [[ "$LIST_TOOLS" -eq 1 ]]; then
  gdk_list_tool_names
  exit 0
fi

if [[ "$LIST_PROFILES" -eq 1 ]]; then
  gdk_list_profile_names
  exit 0
fi

if [[ "$LIST_OPTIONAL_SKILLS" -eq 1 ]]; then
  gdk_list_optional_skill_names
  exit 0
fi

if [[ "$MODE" != "copy" && "$MODE" != "symlink" ]]; then
  echo "[FAIL] --mode must be copy or symlink" >&2
  exit 1
fi

if [[ -z "$PROFILE" ]]; then
  PROFILE="$(awk '/^default_profile:/ {print $2; exit}' "$GDK_MANIFEST")"
  [[ -n "$PROFILE" ]] || PROFILE="embedded-fullstack"
fi

if ! gdk_profile_exists "$PROFILE"; then
  echo "[FAIL] unknown profile: $PROFILE" >&2
  exit 1
fi

for profile in "${EXTRA_PROFILES[@]}"; do
  if ! gdk_profile_exists "$profile"; then
    echo "[FAIL] unknown extra profile: $profile" >&2
    exit 1
  fi
done

for skill in "${OPTIONAL_SKILLS[@]}"; do
  if ! gdk_optional_skill_exists "$skill"; then
    echo "[FAIL] unknown optional skill: $skill" >&2
    exit 1
  fi
done

if [[ "$TOOL" == "auto" ]]; then
  TOOL="$(detect_tool_auto)"
  echo "[INFO] auto-detected tool: $TOOL"
fi

if ! gdk_tool_exists "$TOOL"; then
  echo "[FAIL] unknown tool: $TOOL" >&2
  exit 1
fi

if [[ -z "$TARGET" ]]; then
  TARGET="$(gdk_get_tool_value "$TOOL" "default_root")"
fi

AGENTS_DIR_NAME="$(gdk_get_tool_value "$TOOL" "agents_dir")"
SKILLS_DIR_NAME="$(gdk_get_tool_value "$TOOL" "skills_dir")"

if [[ -z "$TARGET" || -z "$AGENTS_DIR_NAME" || -z "$SKILLS_DIR_NAME" ]]; then
  echo "[FAIL] tool target config incomplete for: $TOOL" >&2
  exit 1
fi

TARGET="$(expand_path "$TARGET")"
AGENT_DST="$TARGET/$AGENTS_DIR_NAME"
SKILL_DST="$TARGET/$SKILLS_DIR_NAME"

ALL_PROFILES=("$PROFILE" "${EXTRA_PROFILES[@]}")

mapfile -t AGENTS_TO_INSTALL < <(resolve_profile_items "include_agents" "${ALL_PROFILES[@]}")
mapfile -t SKILLS_TO_INSTALL < <(resolve_profile_items "include_skills" "${ALL_PROFILES[@]}")

if [[ ${#AGENTS_TO_INSTALL[@]} -eq 0 ]]; then
  echo "[FAIL] no agents resolved from profiles: ${ALL_PROFILES[*]}" >&2
  exit 1
fi

if [[ ${#SKILLS_TO_INSTALL[@]} -eq 0 ]]; then
  echo "[FAIL] no skills resolved from profiles: ${ALL_PROFILES[*]}" >&2
  exit 1
fi

run_cmd mkdir -p "$AGENT_DST" "$SKILL_DST"

for agent in "${AGENTS_TO_INSTALL[@]}"; do
  install_item "$ROOT_DIR/agents/$agent" "$AGENT_DST/$agent"
done

for skill in "${SKILLS_TO_INSTALL[@]}"; do
  install_item "$ROOT_DIR/skills/$skill" "$SKILL_DST/$skill"
done

for skill in "${OPTIONAL_SKILLS[@]}"; do
  optional_path="$(gdk_get_optional_skill_path "$skill")"
  [[ -n "$optional_path" ]] || { echo "[FAIL] optional skill path missing: $skill" >&2; exit 1; }
  optional_dir="$ROOT_DIR/${optional_path%/SKILL.md}"
  install_item "$optional_dir" "$SKILL_DST/$skill"
done

echo "Install completed"
echo "  tool=$TOOL"
echo "  mode=$MODE"
echo "  target=$TARGET"
echo "  profiles=${ALL_PROFILES[*]}"
echo "  agents=${#AGENTS_TO_INSTALL[@]} skills=${#SKILLS_TO_INSTALL[@]} optional_skills=${#OPTIONAL_SKILLS[@]}"
