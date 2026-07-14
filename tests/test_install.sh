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

[[ -f "$TARGET/agents/requirements-analyst.md" ]] || { echo "[FAIL] missing core agent" >&2; exit 1; }
[[ -f "$TARGET/agents/driver-engineer.md" ]] || { echo "[FAIL] missing core agent driver-engineer" >&2; exit 1; }
[[ -f "$TARGET/skills/adk-requirements-triage/SKILL.md" ]] || { echo "[FAIL] missing core skill" >&2; exit 1; }
[[ ! -f "$TARGET/agents/application-engineer.md" ]] || { echo "[FAIL] unexpected non-core agent" >&2; exit 1; }
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

[[ -f "$TARGET/agents/security-compliance-reviewer.md" ]] || { echo "[FAIL] missing extra-profile agent" >&2; exit 1; }
[[ -d "$TARGET/.adk-backups" ]] || { echo "[FAIL] missing install backup" >&2; exit 1; }
[[ -f "$REPORT" ]] || { echo "[FAIL] missing install report" >&2; exit 1; }
grep -q "manifest_version" "$REPORT" || { echo "[FAIL] install report missing version" >&2; exit 1; }

set +e
"$ROOT_DIR/scripts/install-assets.sh" \
  --tool claude-code \
  --mode symlink \
  --target "$TARGET" \
  --profile core \
  --dry-run >"$TMP_DIR/symlink.out" 2>"$TMP_DIR/symlink.err"
symlink_rc=$?
set -e
[[ "$symlink_rc" -eq 2 ]] || { echo "[FAIL] symlink mode must return 2" >&2; exit 1; }
grep -q "unsupported_install_mode" "$TMP_DIR/symlink.err" || {
  echo "[FAIL] symlink rejection code missing" >&2
  exit 1
}

BOUND_TARGET_OUT="$TMP_DIR/platform-bound-target.out"
if "$ROOT_DIR/scripts/install-assets.sh" --tool vendor-specific-runtime --target "$TMP_DIR/platform-bound-target" --profile core >"$BOUND_TARGET_OUT" 2>&1; then
  echo "[FAIL] platform-bound target should be rejected" >&2
  exit 1
fi
grep -q "unknown tool: vendor-specific-runtime" "$BOUND_TARGET_OUT" || {
  echo "[FAIL] platform-bound target rejection message missing" >&2
  exit 1
}

echo "[PASS] install"
