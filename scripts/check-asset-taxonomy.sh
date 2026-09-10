#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Compatibility shim: the taxonomy contract is owned by the typed JSON domain
# model. Legacy callers keep this stable shell entry point while manifest.yaml
# consumers are retired incrementally.
exec python3 -m agent_dev_kit.asset_taxonomy_contract --root "$ROOT_DIR" "$@"
