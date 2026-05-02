#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

BRIDGE="$ROOT_DIR/scripts/openspec_bridge.sh"
OPENSPEC_ROOT="$TMP_DIR/openspec"
GDK_CHANGE_ROOT="$TMP_DIR/gdk/changes"

mkdir -p "$OPENSPEC_ROOT/changes/archive" "$GDK_CHANGE_ROOT"

create_openspec_change() {
  local change_id="$1"
  local tasks_body="$2"
  local with_design="$3"
  local base="$OPENSPEC_ROOT/changes/$change_id"

  mkdir -p "$base/specs/ui"
  cat > "$base/proposal.md" <<PROPOSAL
# Proposal: $change_id

## Intent
- smoke test
PROPOSAL

  cat > "$base/tasks.md" <<TASKS
# Implementation Tasks
$tasks_body
TASKS

  if [[ "$with_design" == "yes" ]]; then
    cat > "$base/design.md" <<DESIGN
# Design: $change_id
DESIGN
  fi

  cat > "$base/specs/ui/spec.md" <<SPEC
# UI Spec
SPEC
}

create_openspec_change "incomplete-task" $'- [ ] 1.1 todo' "yes"
"$BRIDGE" import --change incomplete-task --openspec-root "$OPENSPEC_ROOT" --gdk-root "$GDK_CHANGE_ROOT"
grep -q '^stage: proposed$' "$GDK_CHANGE_ROOT/incomplete-task/state.yaml" || { echo "[FAIL] expected proposed stage" >&2; exit 1; }
[[ -f "$GDK_CHANGE_ROOT/incomplete-task/checklist.md" ]] || { echo "[FAIL] checklist not created" >&2; exit 1; }
[[ -f "$GDK_CHANGE_ROOT/incomplete-task/negative-results.md" ]] || { echo "[FAIL] negative-results not created" >&2; exit 1; }

create_openspec_change "all-complete" $'- [x] 1.1 done' "no"
"$BRIDGE" import --change all-complete --openspec-root "$OPENSPEC_ROOT" --gdk-root "$GDK_CHANGE_ROOT"
grep -q '^stage: applied$' "$GDK_CHANGE_ROOT/all-complete/state.yaml" || { echo "[FAIL] expected applied stage" >&2; exit 1; }
[[ -f "$GDK_CHANGE_ROOT/all-complete/design.md" ]] || { echo "[FAIL] default design not created" >&2; exit 1; }

mkdir -p "$OPENSPEC_ROOT/changes/archive/2026-05-02-archived-change"
cat > "$OPENSPEC_ROOT/changes/archive/2026-05-02-archived-change/proposal.md" <<'PROPOSAL'
# Proposal: archived-change
PROPOSAL
cat > "$OPENSPEC_ROOT/changes/archive/2026-05-02-archived-change/tasks.md" <<'TASKS'
# Implementation Tasks
- [x] done
TASKS
"$BRIDGE" import --change archived-change --from-archive --openspec-root "$OPENSPEC_ROOT" --gdk-root "$GDK_CHANGE_ROOT"
grep -q '^stage: archived$' "$GDK_CHANGE_ROOT/archived-change/state.yaml" || { echo "[FAIL] expected archived stage" >&2; exit 1; }

mkdir -p "$GDK_CHANGE_ROOT/export-active/specs/auth"
cat > "$GDK_CHANGE_ROOT/export-active/proposal.md" <<'PROPOSAL'
# 变更提案：export-active
PROPOSAL
cat > "$GDK_CHANGE_ROOT/export-active/design.md" <<'DESIGN'
# 设计说明：export-active
DESIGN
cat > "$GDK_CHANGE_ROOT/export-active/tasks.md" <<'TASKS'
# 执行任务：export-active
- [x] done
TASKS
cat > "$GDK_CHANGE_ROOT/export-active/state.yaml" <<'STATE'
stage: review-passed
owner: tester
updated_at: 2026-05-02T00:00:00Z
STATE
cat > "$GDK_CHANGE_ROOT/export-active/verify-report.md" <<'VERIFY'
# verify
VERIFY
cat > "$GDK_CHANGE_ROOT/export-active/review-report.md" <<'REVIEW'
# review
REVIEW
cat > "$GDK_CHANGE_ROOT/export-active/specs/auth/spec.md" <<'SPEC'
# Auth Spec
SPEC

"$BRIDGE" export --change export-active --openspec-root "$OPENSPEC_ROOT" --gdk-root "$GDK_CHANGE_ROOT"
[[ -f "$OPENSPEC_ROOT/changes/export-active/proposal.md" ]] || { echo "[FAIL] export proposal missing" >&2; exit 1; }
[[ -f "$OPENSPEC_ROOT/changes/export-active/.openspec-bridge.yaml" ]] || { echo "[FAIL] export bridge metadata missing" >&2; exit 1; }
grep -q '^gdk_stage: review-passed$' "$OPENSPEC_ROOT/changes/export-active/.openspec-bridge.yaml" || { echo "[FAIL] gdk stage metadata mismatch" >&2; exit 1; }

mkdir -p "$GDK_CHANGE_ROOT/export-archive"
cat > "$GDK_CHANGE_ROOT/export-archive/proposal.md" <<'PROPOSAL'
# 变更提案：export-archive
PROPOSAL
cat > "$GDK_CHANGE_ROOT/export-archive/design.md" <<'DESIGN'
# 设计说明：export-archive
DESIGN
cat > "$GDK_CHANGE_ROOT/export-archive/tasks.md" <<'TASKS'
# 执行任务：export-archive
- [x] done
TASKS
cat > "$GDK_CHANGE_ROOT/export-archive/state.yaml" <<'STATE'
stage: applied
owner: tester
updated_at: 2026-05-02T00:00:00Z
STATE

"$BRIDGE" export --change export-archive --archive-date 2026-05-02 --openspec-root "$OPENSPEC_ROOT" --gdk-root "$GDK_CHANGE_ROOT"
[[ -d "$OPENSPEC_ROOT/changes/archive/2026-05-02-export-archive" ]] || { echo "[FAIL] archive export path missing" >&2; exit 1; }

"$BRIDGE" status-map | rg -q "OpenSpec -> gdk stage mapping" || { echo "[FAIL] status-map output mismatch" >&2; exit 1; }

echo "[PASS] openspec bridge"
