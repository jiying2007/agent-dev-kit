#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Canonical repository launcher for the typed JSON asset-taxonomy contract.
# The Python domain model owns validation; this shell entry point adds only the
# repository root and no compatibility behavior.
exec python3 -m agent_dev_kit.asset_taxonomy_contract --root "$ROOT_DIR" "$@"
