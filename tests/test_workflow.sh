#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CHANGE_ROOT="$TMP_DIR/changes"
CHANGE_ID="smoke-change"

"$ROOT_DIR/scripts/workflow.sh" propose --change "$CHANGE_ID" --title "workflow smoke" --root "$CHANGE_ROOT"
[[ -f "$CHANGE_ROOT/$CHANGE_ID/negative-results.md" ]] || { echo "[FAIL] missing negative-results artifact" >&2; exit 1; }
grep -q "^## 问题陈述（单问题）" "$CHANGE_ROOT/$CHANGE_ID/proposal.md" || { echo "[FAIL] missing single-problem section" >&2; exit 1; }
grep -q "^## Ownership 与并行冲突检查" "$CHANGE_ROOT/$CHANGE_ID/tasks.md" || { echo "[FAIL] missing ownership section" >&2; exit 1; }

if "$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID" --root "$CHANGE_ROOT" --result pass --blockers 0 --majors 0 --minors 0 >/dev/null 2>&1; then
  echo "[FAIL] review should fail before verify stage" >&2
  exit 1
fi

"$ROOT_DIR/scripts/workflow.sh" apply --change "$CHANGE_ID" --root "$CHANGE_ROOT"
if "$ROOT_DIR/scripts/workflow.sh" archive --change "$CHANGE_ID" --root "$CHANGE_ROOT" >/dev/null 2>&1; then
  echo "[FAIL] archive should fail before review pass" >&2
  exit 1
fi

"$ROOT_DIR/scripts/workflow.sh" verify --change "$CHANGE_ID" --root "$CHANGE_ROOT"
"$ROOT_DIR/scripts/workflow.sh" review --change "$CHANGE_ID" --root "$CHANGE_ROOT" --result pass --blockers 0 --majors 0 --minors 1
"$ROOT_DIR/scripts/workflow.sh" archive --change "$CHANGE_ID" --root "$CHANGE_ROOT"

ARCHIVE_MATCH="$(find "$CHANGE_ROOT/archive" -maxdepth 1 -type d -name "*-smoke-change" | head -n 1 || true)"
[[ -n "$ARCHIVE_MATCH" ]] || { echo "[FAIL] archive directory not found" >&2; exit 1; }

echo "[PASS] workflow"
