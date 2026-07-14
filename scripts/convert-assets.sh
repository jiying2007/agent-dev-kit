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

Compatibility wrapper for the unified v3 exporter.

Options are forwarded to:
  ./scripts/devkit.sh export

Common options include --profile, --extra-profile, --with-optional-skill,
--asset-kind, --out, --clean, --dry-run and --summary-json.

Additional compatibility option:
  --list-optional-skills

Direct target output is governed by manifests/target-contracts/*.json.
Hermes Agent is skill-only and therefore requires --asset-kind skill when a
profile also resolves Agents.
USAGE
}

if [[ "${1:-}" == "--list-optional-skills" ]]; then
  adk_require_manifest
  adk_list_optional_skill_names
  exit 0
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

cd "$ROOT_DIR"
exec bash "$ROOT_DIR/scripts/devkit.sh" export "$@"
