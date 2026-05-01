#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TARGET="$TMP_DIR/.codex"

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core

[[ -d "$TARGET/agents/requirements-analyst" ]] || { echo "[FAIL] missing core agent" >&2; exit 1; }
[[ -d "$TARGET/skills/requirements-triage" ]] || { echo "[FAIL] missing core skill" >&2; exit 1; }
[[ ! -d "$TARGET/agents/driver-engineer" ]] || { echo "[FAIL] unexpected non-core agent" >&2; exit 1; }
[[ ! -d "$TARGET/skills/incident-rca-report" ]] || { echo "[FAIL] unexpected optional skill without request" >&2; exit 1; }

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --extra-profile release-hardening

[[ -d "$TARGET/agents/security-compliance-reviewer" ]] || { echo "[FAIL] missing extra-profile agent" >&2; exit 1; }

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode symlink \
  --target "$TARGET" \
  --profile core \
  --dry-run

echo "[PASS] install"
