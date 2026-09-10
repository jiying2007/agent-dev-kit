#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

[[ $# -gt 0 ]] || {
  echo "Usage: ./scripts/catalog-assets.sh <build|find> [options]" >&2
  exit 1
}

exec python3 -m agent_dev_kit.catalog_contract "$1" --root "$ROOT_DIR" "${@:2}"
