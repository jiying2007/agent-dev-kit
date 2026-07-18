#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_CONTEXT="$ROOT_DIR/tools/local-ci"

PYTHON_SELECTION="all"
MODE="full"
PREPARE=0
DRY_RUN=0

usage() {
  cat <<'USAGE'
Usage:
  scripts/run-local-ci-parity.sh [--python 3.11|3.12|all] [--mode quick|full] [--prepare] [--dry-run]

Runs a local Docker parity matrix for the declared GitHub CI Python versions.

Security and authority boundary:
  - source is mounted read-only and copied into an isolated tmpfs
  - host credentials, SSH state, Docker socket, and HOME are not mounted
  - containers run as a fixed non-root UID, drop Linux capabilities, and use no-new-privileges
  - gate containers use no network; bridge is limited to image preparation and dependency audit
  - this command never publishes, tags, pushes, attests, or certifies Software M5

Use --prepare to build the pinned local tool images. Without --prepare, the
images must already exist. --dry-run prints the complete boundary without
contacting Docker.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_SELECTION="${2:-}"
      shift 2
      ;;
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --prepare)
      PREPARE=1
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
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$PYTHON_SELECTION" in
  3.11|3.12|all) ;;
  *)
    echo "[FAIL] --python must be 3.11, 3.12, or all" >&2
    exit 2
    ;;
esac
case "$MODE" in
  quick|full) ;;
  *)
    echo "[FAIL] --mode must be quick or full" >&2
    exit 2
    ;;
esac

base_image_for() {
  case "$1" in
    3.11) printf '%s\n' 'python:3.11-slim@sha256:db3ff2e1800a8581e2c48a27c3995339d47bdf046da21c7627accd3d51053a93' ;;
    3.12) printf '%s\n' 'python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de' ;;
  esac
}

tool_image_for() {
  printf 'agent-dev-kit-local-ci:python-%s\n' "$1"
}

versions=("$PYTHON_SELECTION")
if [[ "$PYTHON_SELECTION" == "all" ]]; then
  versions=(3.11 3.12)
fi

echo "transport=docker"
echo "source_mount=read-only"
echo "work_copy=isolated-tmpfs"
echo "network=gates-none,audit-bridge,prepare-build-network"
echo "credentials=not-mounted"
echo "release_authority=none"
echo "file_mode_inventory=git-index-bound"
echo "container_user=65532:65532"
echo "mode=$MODE"
for version in "${versions[@]}"; do
  echo "python=$version base_image=$(base_image_for "$version") tool_image=$(tool_image_for "$version")"
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  exit 0
fi

command -v docker >/dev/null 2>&1 || {
  echo "[FAIL] docker is required for local CI parity" >&2
  exit 2
}

definition_sha256="$(
  sha256sum "$DOCKER_CONTEXT/Dockerfile" "$DOCKER_CONTEXT/entrypoint.sh" \
    | awk '{print $1}' \
    | tr -d '\n' \
    | sha256sum \
    | awk '{print $1}'
)"
echo "local_ci_definition_sha256=$definition_sha256"

SNAPSHOT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/adk-local-ci.XXXXXX")"
cleanup() {
  if [[ -n "$SNAPSHOT_DIR" && -d "$SNAPSHOT_DIR" ]]; then
    rm -rf -- "$SNAPSHOT_DIR"
  fi
}
trap cleanup EXIT

SNAPSHOT_TAR="$SNAPSHOT_DIR/source.tar"
SNAPSHOT_SOURCE="$SNAPSHOT_DIR/source"
INVENTORY_DIR="$SNAPSHOT_DIR/inventory"
MODE_INVENTORY="$INVENTORY_DIR/file-modes.z"
mkdir -p "$SNAPSHOT_SOURCE" "$INVENTORY_DIR"
git -C "$ROOT_DIR" ls-files -z -s >"$MODE_INVENTORY"
if [[ ! -s "$MODE_INVENTORY" ]]; then
  echo "[FAIL] cannot export Git index mode inventory" >&2
  exit 2
fi
tar \
  --directory "$ROOT_DIR" \
  --exclude=.git \
  --exclude=.ruff_cache \
  --exclude=build \
  --exclude=dist \
  --exclude='*.egg-info' \
  --exclude='__pycache__' \
  --create \
  --file "$SNAPSHOT_TAR" \
  .
tar --directory "$SNAPSHOT_SOURCE" --no-same-owner --extract --file "$SNAPSHOT_TAR"
chmod -R u=rwX,go=rX "$SNAPSHOT_SOURCE"
snapshot_sha256="$(sha256sum "$SNAPSHOT_TAR" | awk '{print $1}')"
mode_inventory_sha256="$(sha256sum "$MODE_INVENTORY" | awk '{print $1}')"
echo "source_snapshot_sha256=$snapshot_sha256"
echo "file_mode_inventory_sha256=$mode_inventory_sha256"

failures=0
for version in "${versions[@]}"; do
  base_image="$(base_image_for "$version")"
  tool_image="$(tool_image_for "$version")"

  if [[ "$PREPARE" -eq 1 ]]; then
    if ! docker build \
      --pull=false \
      --build-arg "BASE_IMAGE=$base_image" \
      --label "io.agent-dev-kit.local-ci.base-image=$base_image" \
      --label "io.agent-dev-kit.local-ci.definition-sha256=$definition_sha256" \
      --label "io.agent-dev-kit.local-ci.python=$version" \
      --tag "$tool_image" \
      "$DOCKER_CONTEXT"; then
      echo "[FAIL] local CI image build failed: python=$version" >&2
      failures=$((failures + 1))
      continue
    fi
  fi

  if ! docker image inspect "$tool_image" >/dev/null 2>&1; then
    echo "[FAIL] local CI image is missing: $tool_image; rerun with --prepare" >&2
    failures=$((failures + 1))
    continue
  fi

  image_id="$(docker image inspect --format '{{.Id}}' "$tool_image")"
  image_contract="$(docker image inspect --format '{{ index .Config.Labels "io.agent-dev-kit.local-ci.contract" }}' "$tool_image")"
  image_base="$(docker image inspect --format '{{ index .Config.Labels "io.agent-dev-kit.local-ci.base-image" }}' "$tool_image")"
  image_definition="$(docker image inspect --format '{{ index .Config.Labels "io.agent-dev-kit.local-ci.definition-sha256" }}' "$tool_image")"
  image_python="$(docker image inspect --format '{{ index .Config.Labels "io.agent-dev-kit.local-ci.python" }}' "$tool_image")"
  if [[ "$image_contract" != "v2" || "$image_base" != "$base_image" || "$image_definition" != "$definition_sha256" || "$image_python" != "$version" ]]; then
    echo "[FAIL] local CI image contract mismatch: $tool_image; rerun with --prepare" >&2
    failures=$((failures + 1))
    continue
  fi
  echo "tool_image_id[$version]=$image_id"

  echo "[INFO] local CI gates start: python=$version mode=$MODE image=$tool_image"
  if ! docker run --rm \
    --read-only \
    --network none \
    --user 65532:65532 \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --pids-limit 512 \
    --tmpfs /tmp:rw,nosuid,nodev,size=512m,mode=1777 \
    --tmpfs /work:rw,exec,nosuid,nodev,size=2g,mode=1777 \
    --mount "type=bind,src=$SNAPSHOT_SOURCE,dst=/source,readonly" \
    --mount "type=bind,src=$INVENTORY_DIR,dst=/inventory,readonly" \
    --env "ADK_LOCAL_CI_MODE=$MODE" \
    --env "ADK_LOCAL_CI_PHASE=gates" \
    --env "ADK_FILE_MODE_INVENTORY=/inventory/file-modes.z" \
    "$tool_image"; then
    echo "[FAIL] local CI gates failed: python=$version mode=$MODE" >&2
    failures=$((failures + 1))
    continue
  fi

  echo "[INFO] local CI dependency audit start: python=$version image=$tool_image"
  if ! docker run --rm \
    --read-only \
    --network bridge \
    --user 65532:65532 \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --pids-limit 512 \
    --tmpfs /tmp:rw,nosuid,nodev,size=512m,mode=1777 \
    --tmpfs /work:rw,exec,nosuid,nodev,size=2g,mode=1777 \
    --mount "type=bind,src=$SNAPSHOT_SOURCE,dst=/source,readonly" \
    --env "ADK_LOCAL_CI_MODE=$MODE" \
    --env "ADK_LOCAL_CI_PHASE=audit" \
    "$tool_image"; then
    echo "[FAIL] local CI dependency audit failed: python=$version" >&2
    failures=$((failures + 1))
  fi
done

if [[ "$failures" -gt 0 ]]; then
  echo "[FAIL] local CI parity failures=$failures" >&2
  exit 1
fi

echo "[PASS] local CI parity matrix versions=${#versions[@]} mode=$MODE"
