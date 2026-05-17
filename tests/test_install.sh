#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TARGET="$TMP_DIR/.claude"
REPORT="$TMP_DIR/install-report.md"

"$ROOT_DIR/scripts/install-assets.sh" \
  --tool claude-code \
  --mode copy \
  --target "$TARGET" \
  --profile core

[[ -d "$TARGET/agents/requirements-analyst" ]] || { echo "[FAIL] missing core agent" >&2; exit 1; }
[[ -d "$TARGET/agents/driver-engineer" ]] || { echo "[FAIL] missing core agent driver-engineer" >&2; exit 1; }
[[ -d "$TARGET/skills/adk-requirements-triage" ]] || { echo "[FAIL] missing core skill" >&2; exit 1; }
[[ ! -d "$TARGET/agents/application-engineer" ]] || { echo "[FAIL] unexpected non-core agent" >&2; exit 1; }
[[ ! -d "$TARGET/skills/adk-incident-rca-report" ]] || { echo "[FAIL] unexpected optional skill without request" >&2; exit 1; }

"$ROOT_DIR/scripts/install-assets.sh" \
  --tool claude-code \
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

"$ROOT_DIR/scripts/install-assets.sh" \
  --tool claude-code \
  --mode symlink \
  --target "$TARGET" \
  --profile core \
  --dry-run

CODEX_INSTALL_OUT="$TMP_DIR/codex-install.out"
if "$ROOT_DIR/scripts/install-assets.sh" --tool codex --target "$TMP_DIR/codex" --profile core >"$CODEX_INSTALL_OUT" 2>&1; then
  echo "[FAIL] codex install should be disabled" >&2
  exit 1
fi
grep -q "codex install is disabled" "$CODEX_INSTALL_OUT" || {
  echo "[FAIL] codex install failure message missing" >&2
  exit 1
}

echo "[PASS] install"
