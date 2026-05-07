#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TARGET="$TMP_DIR/.codex"
REPORT="$TMP_DIR/install-report.md"

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core

[[ -d "$TARGET/agents/requirements-analyst" ]] || { echo "[FAIL] missing core agent" >&2; exit 1; }
[[ -d "$TARGET/skills/adk-requirements-triage" ]] || { echo "[FAIL] missing core skill" >&2; exit 1; }
[[ ! -d "$TARGET/agents/driver-engineer" ]] || { echo "[FAIL] unexpected non-core agent" >&2; exit 1; }
[[ ! -d "$TARGET/skills/adk-incident-rca-report" ]] || { echo "[FAIL] unexpected optional skill without request" >&2; exit 1; }

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --extra-profile release-hardening \
  --backup \
  --install-report "$REPORT" \
  --lock-version "$(awk '/^version:/ {print $2; exit}' "$ROOT_DIR/manifest.yaml")"

[[ -d "$TARGET/agents/security-compliance-reviewer" ]] || { echo "[FAIL] missing extra-profile agent" >&2; exit 1; }
[[ -d "$TARGET/.adk-backups" ]] || { echo "[FAIL] missing install backup" >&2; exit 1; }
[[ -f "$REPORT" ]] || { echo "[FAIL] missing install report" >&2; exit 1; }
grep -q "manifest_version" "$REPORT" || { echo "[FAIL] install report missing version" >&2; exit 1; }

"$ROOT_DIR/scripts/install_assets.sh" \
  --tool codex \
  --mode symlink \
  --target "$TARGET" \
  --profile core \
  --dry-run

echo "[PASS] install"
