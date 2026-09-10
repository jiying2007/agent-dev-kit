#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
PYTHON_BIN="${ADK_PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/check-profile-coherence.sh [--summary-json]

Validates profile inheritance, references, default-skill closure and the
platform-neutral core boundary from canonical manifest.json.
USAGE
}

ARGS=(--root "$ROOT_DIR")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      ARGS+=(--summary-json)
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unexpected argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

exec "$PYTHON_BIN" -m agent_dev_kit.profile_coherence_contract "${ARGS[@]}"
