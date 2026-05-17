#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CODEX_ROOT="$HOME/codex"
OUT_DIR=""
KEEP_TMP=0
ADK_PROFILE="personal-core"
EXTRA_PROFILES=("release-hardening")
OPTIONAL_SKILLS=(
  "adk-planning-execution-loop"
  "adk-skill-composition-governance"
  "adk-security-supply-chain"
  "adk-cross-team-handoff"
)
CODEX_PROFILES=("team-collab")

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-codex-handoff.sh [options]

Options:
  --codex-root <path>              # 默认 ~/codex
  --out <path>                     # 保留 handoff 输出目录；默认使用临时目录
  --profile <adk-profile>          # 默认 personal-core
  --extra-profile <adk-profile>    # 可重复；默认 release-hardening
  --with-optional-skill <skill>    # 可重复；默认生产推荐四类 optional skills
  --codex-profile <profile>        # 可重复；默认 team-collab
  --keep-tmp
  -h, --help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-root)
      CODEX_ROOT="$2"
      shift 2
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --profile)
      ADK_PROFILE="$2"
      shift 2
      ;;
    --extra-profile)
      if [[ "${#EXTRA_PROFILES[@]}" -eq 1 && "${EXTRA_PROFILES[0]}" == "release-hardening" ]]; then
        EXTRA_PROFILES=()
      fi
      EXTRA_PROFILES+=("$2")
      shift 2
      ;;
    --with-optional-skill)
      if [[ "${#OPTIONAL_SKILLS[@]}" -eq 4 && "${OPTIONAL_SKILLS[0]}" == "adk-planning-execution-loop" ]]; then
        OPTIONAL_SKILLS=()
      fi
      OPTIONAL_SKILLS+=("$2")
      shift 2
      ;;
    --codex-profile)
      if [[ "${#CODEX_PROFILES[@]}" -eq 1 && "${CODEX_PROFILES[0]}" == "team-collab" ]]; then
        CODEX_PROFILES=()
      fi
      CODEX_PROFILES+=("$2")
      shift 2
      ;;
    --keep-tmp)
      KEEP_TMP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown arg: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -d "$CODEX_ROOT" ]]; then
  echo "[FAIL] codex declaration repo missing: $CODEX_ROOT" >&2
  exit 1
fi
CODEX_ROOT="$(cd "$CODEX_ROOT" && pwd)"

TMP_ROOT="$(mktemp -d)"
if [[ "$KEEP_TMP" -eq 0 ]]; then
  trap 'rm -rf "$TMP_ROOT"' EXIT
else
  echo "[INFO] keep tmp root: $TMP_ROOT"
fi

if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="$TMP_ROOT/handoff"
fi

CONVERT_ARGS=(
  --target codex
  --profile "$ADK_PROFILE"
  --out "$OUT_DIR"
  --clean
)

for profile in "${EXTRA_PROFILES[@]}"; do
  CONVERT_ARGS+=(--extra-profile "$profile")
done

for skill in "${OPTIONAL_SKILLS[@]}"; do
  CONVERT_ARGS+=(--with-optional-skill "$skill")
done

for profile in "${CODEX_PROFILES[@]}"; do
  CONVERT_ARGS+=(--codex-profile "$profile")
done

echo "[INFO] generate codex handoff"
rtk bash "$ROOT_DIR/scripts/convert-assets.sh" "${CONVERT_ARGS[@]}"

HANDOFF_DIR="$OUT_DIR/codex"
if [[ ! -f "$HANDOFF_DIR/manifest-fragments/skills.json" ]]; then
  echo "[FAIL] handoff missing skill manifest fragment" >&2
  exit 1
fi
if [[ ! -f "$HANDOFF_DIR/manifest-fragments/agents.json" ]]; then
  echo "[FAIL] handoff missing agent manifest fragment" >&2
  exit 1
fi
if [[ ! -f "$HANDOFF_DIR/manifest-fragments/workflows.json" ]]; then
  echo "[FAIL] handoff missing workflow manifest fragment" >&2
  exit 1
fi
if [[ ! -f "$HANDOFF_DIR/manifest-fragments/mcp_servers.json" ]]; then
  echo "[FAIL] handoff missing MCP manifest fragment" >&2
  exit 1
fi

WORK_CODEX="$TMP_ROOT/codex"
mkdir -p "$WORK_CODEX"
cp -a "$CODEX_ROOT"/. "$WORK_CODEX"/

echo "[INFO] merge handoff into temp codex repo: $WORK_CODEX"
rtk python3 - "$WORK_CODEX" "$HANDOFF_DIR" <<'PY'
import json
import pathlib
import shutil
import sys

repo = pathlib.Path(sys.argv[1])
handoff = pathlib.Path(sys.argv[2])

src = handoff / "src/codex-home"
dst = repo / "src/codex-home"
if not src.is_dir():
    raise SystemExit(f"handoff source tree missing: {src}")
shutil.copytree(src, dst, dirs_exist_ok=True)

def merge_manifest(filename: str, key: str) -> None:
    base_path = repo / "manifests" / filename
    fragment_path = handoff / "manifest-fragments" / filename
    base_path.parent.mkdir(parents=True, exist_ok=True)
    if base_path.exists():
        base = json.loads(base_path.read_text(encoding="utf-8"))
    else:
        base = {"schema_version": 2, key: []}
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
    items = {item["name"]: item for item in base.get(key, [])}
    for item in fragment.get(key, []):
        items[item["name"]] = item
    base[key] = [items[name] for name in sorted(items)]
    base_path.write_text(json.dumps(base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

merge_manifest("skills.json", "skills")
merge_manifest("agents.json", "agents")
merge_manifest("workflows.json", "workflows")
merge_manifest("mcp_servers.json", "mcp_servers")
PY

BUILD_PROFILE="${CODEX_PROFILES[0]:-team-collab}"

echo "[INFO] run ~/codex-compatible build checks profile=$BUILD_PROFILE"
(
  cd "$WORK_CODEX"
  rtk bash scripts/build.sh --profile "$BUILD_PROFILE"
  rtk bash scripts/doctor.sh --scope governance
  rtk bash scripts/doctor.sh --scope repo
  rtk bash scripts/doctor.sh --scope build
  rtk bash scripts/check-skills.sh
)

echo "[PASS] codex handoff conforms to ~/codex source and manifest contract"
