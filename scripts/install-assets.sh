#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=./lib-manifest.sh
source "$SCRIPT_DIR/lib-manifest.sh"

usage() {
  cat <<USAGE
Usage:
  ./scripts/install-assets.sh [options]

Compatibility wrapper for the unified transactional installer.

Options:
  --tool auto|claude-code|hermes-agent|opencode
  --mode copy                    # symlink is intentionally unsupported in 3.1
  --target <tool root path>
  --profile <profile name>
  --extra-profile <profile>      # repeatable
  --with-optional-skill <skill>  # repeatable
  --asset-kind agent|skill
  --backup                       # accepted; v3 apply always creates a rollback anchor
  --backup-dir <path>            # rejected; backup root is transaction-owned
  --install-report <path>
  --lock-version <version>
  --list-tools
  --list-profiles
  --list-optional-skills
  --dry-run                      # create/print plan, do not apply
  --summary-json
  -h, --help
USAGE
}

TOOL="auto"
MODE="copy"
TARGET=""
PROFILE=""
EXTRA_PROFILES=()
OPTIONAL_SKILLS=()
ASSET_KIND=""
BACKUP_DIR=""
INSTALL_REPORT=""
LOCK_VERSION=""
DRY_RUN=0
SUMMARY_JSON=0
LIST_TOOLS=0
LIST_PROFILES=0
LIST_OPTIONAL_SKILLS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tool) TOOL="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    --extra-profile) EXTRA_PROFILES+=("$2"); shift 2 ;;
    --with-optional-skill) OPTIONAL_SKILLS+=("$2"); shift 2 ;;
    --asset-kind) ASSET_KIND="$2"; shift 2 ;;
    --backup) shift ;;
    --backup-dir) BACKUP_DIR="$2"; shift 2 ;;
    --install-report) INSTALL_REPORT="$2"; shift 2 ;;
    --lock-version) LOCK_VERSION="$2"; shift 2 ;;
    --list-tools) LIST_TOOLS=1; shift ;;
    --list-profiles) LIST_PROFILES=1; shift ;;
    --list-optional-skills) LIST_OPTIONAL_SKILLS=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --summary-json) SUMMARY_JSON=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "[FAIL] Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

adk_require_manifest

if [[ "$LIST_TOOLS" -eq 1 ]]; then
  adk_list_tool_names
  exit 0
fi
if [[ "$LIST_PROFILES" -eq 1 ]]; then
  adk_list_profile_names
  exit 0
fi
if [[ "$LIST_OPTIONAL_SKILLS" -eq 1 ]]; then
  adk_list_optional_skill_names
  exit 0
fi
if [[ -n "$BACKUP_DIR" ]]; then
  echo "[USAGE] unsupported_backup_dir: transactional installer owns <target>/.adk-backups" >&2
  exit 2
fi

MANIFEST_VERSION="$(awk '/^version:/ {print $2; exit}' "$ADK_MANIFEST")"
if [[ -n "$LOCK_VERSION" && "$LOCK_VERSION" != "$MANIFEST_VERSION" ]]; then
  echo "[FAIL] manifest version mismatch: expected $LOCK_VERSION, got $MANIFEST_VERSION" >&2
  exit 1
fi

detect_tool_auto() {
  local tool marker probe
  while IFS= read -r tool; do
    [[ -n "$tool" ]] || continue
    while IFS= read -r marker; do
      [[ -n "$marker" ]] || continue
      probe="${marker/#\~/$HOME}"
      if [[ -e "$probe" ]]; then
        printf '%s\n' "$tool"
        return 0
      fi
    done < <(adk_get_tool_list "$tool" detect)
  done < <(adk_list_tool_names)
  printf '%s\n' "claude-code"
}

if [[ "$TOOL" == "auto" ]]; then
  TOOL="$(detect_tool_auto)"
fi
if ! adk_tool_exists "$TOOL"; then
  echo "[FAIL] unknown tool: $TOOL" >&2
  exit 1
fi
if [[ -z "$PROFILE" ]]; then
  PROFILE="$(awk '/^default_profile:/ {print $2; exit}' "$ADK_MANIFEST")"
fi
if [[ -z "$TARGET" ]]; then
  TARGET="$(adk_get_tool_value "$TOOL" default_root)"
fi

PLAN_PATH="$(mktemp "${TMPDIR:-/tmp}/adk-install-plan.XXXXXX.json")"
cleanup() {
  rm -f "$PLAN_PATH"
}
trap cleanup EXIT

PLAN_ARGS=(
  install plan
  --tool "$TOOL"
  --target "$TARGET"
  --profile "$PROFILE"
  --mode "$MODE"
  --output "$PLAN_PATH"
  --summary-json
)
for profile in "${EXTRA_PROFILES[@]}"; do
  PLAN_ARGS+=(--extra-profile "$profile")
done
for skill in "${OPTIONAL_SKILLS[@]}"; do
  PLAN_ARGS+=(--with-optional-skill "$skill")
done
if [[ -n "$ASSET_KIND" ]]; then
  PLAN_ARGS+=(--asset-kind "$ASSET_KIND")
fi

PLAN_OUTPUT="$(bash "$ROOT_DIR/scripts/devkit.sh" "${PLAN_ARGS[@]}")"
if [[ "$DRY_RUN" -eq 1 ]]; then
  printf '%s\n' "$PLAN_OUTPUT"
  exit 0
fi

APPLY_OUTPUT="$(bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$PLAN_PATH" --summary-json)"
if [[ -n "$INSTALL_REPORT" ]]; then
  mkdir -p "$(dirname "$INSTALL_REPORT")"
  {
    printf '# agent-dev-kit install report\n\n'
    printf -- '- manifest_version: %s\n' "$MANIFEST_VERSION"
    printf -- '- tool: %s\n' "$TOOL"
    printf -- '- mode: copy\n'
    printf -- '- target: %s\n' "$TARGET"
    printf -- '- profile: %s\n' "$PROFILE"
    printf -- '- asset_kind: %s\n' "${ASSET_KIND:-all}"
    printf -- '- receipt: %s/.adk-install-receipt.json\n' "$TARGET"
  } >"$INSTALL_REPORT"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '%s\n' "$APPLY_OUTPUT"
else
  echo "Install completed"
  echo "  manifest_version=$MANIFEST_VERSION"
  echo "  tool=$TOOL"
  echo "  mode=copy"
  echo "  target=$TARGET"
  echo "  receipt=$TARGET/.adk-install-receipt.json"
  [[ -z "$INSTALL_REPORT" ]] || echo "  install_report=$INSTALL_REPORT"
fi
