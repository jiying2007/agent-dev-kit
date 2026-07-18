#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<USAGE
Usage:
  ./scripts/quality-gates.sh <change_dir>

Deprecated compatibility entrypoint. New callers should use:
  ./scripts/check-change-governance.sh <change_dir>
USAGE
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 1
fi

echo "[DEPRECATED] scripts/quality-gates.sh now delegates to check-change-governance.sh" >&2
exec bash "$SCRIPT_DIR/check-change-governance.sh" "$1"
