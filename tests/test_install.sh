#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

TARGET="$TMP_DIR/.claude"
PLAN="$TMP_DIR/install-plan.json"
REPLAN="$TMP_DIR/reinstall-plan.json"

bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --output "$PLAN" \
  --summary-json >"$TMP_DIR/plan.json"

bash "$ROOT_DIR/scripts/devkit.sh" install apply \
  --plan "$PLAN" \
  --summary-json >"$TMP_DIR/apply.json"

[[ -f "$TARGET/agents/requirements-analyst.md" ]] || { echo "[FAIL] missing core agent" >&2; exit 1; }
[[ -f "$TARGET/agents/component-engineer.md" ]] || { echo "[FAIL] missing core agent component-engineer" >&2; exit 1; }
[[ ! -e "$TARGET/agents/driver-engineer.md" ]] || { echo "[FAIL] embedded driver agent leaked into core" >&2; exit 1; }
[[ -f "$TARGET/skills/adk-requirements-triage/SKILL.md" ]] || { echo "[FAIL] missing core skill" >&2; exit 1; }
[[ ! -f "$TARGET/agents/application-engineer.md" ]] || { echo "[FAIL] unexpected non-core agent" >&2; exit 1; }
[[ ! -d "$TARGET/skills/adk-incident-rca-report" ]] || { echo "[FAIL] unexpected optional skill without request" >&2; exit 1; }

python3 - "$TARGET/.adk-install-receipt.json" <<'PY'
import json, sys
value=json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema"] == "adk-install-receipt/v3", value
assert isinstance(value.get("receipt_sha256"), str) and len(value["receipt_sha256"]) == 64, value
PY

bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --extra-profile release-hardening \
  --output "$REPLAN" \
  --summary-json >"$TMP_DIR/replan.json"

bash "$ROOT_DIR/scripts/devkit.sh" install apply \
  --plan "$REPLAN" \
  --summary-json >"$TMP_DIR/reapply.json"

[[ -f "$TARGET/agents/security-compliance-reviewer.md" ]] || { echo "[FAIL] missing extra-profile agent" >&2; exit 1; }
[[ -d "$TARGET/.adk-backups" ]] || { echo "[FAIL] missing transactional install backup" >&2; exit 1; }

set +e
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --mode symlink \
  --target "$TMP_DIR/symlink-target" \
  --profile core \
  --output "$TMP_DIR/symlink-plan.json" \
  --summary-json >"$TMP_DIR/symlink.out" 2>"$TMP_DIR/symlink.err"
symlink_rc=$?
set -e
[[ "$symlink_rc" -eq 2 ]] || { echo "[FAIL] symlink mode must return 2" >&2; exit 1; }
grep -q "unsupported_install_mode" "$TMP_DIR/symlink.err" || {
  echo "[FAIL] symlink rejection code missing" >&2
  exit 1
}

for schema in adk-install-receipt/v1 adk-install-receipt/v2; do
  legacy_target="$TMP_DIR/legacy-${schema##*/}"
  mkdir -p "$legacy_target"
  printf '{"schema":"%s"}\n' "$schema" >"$legacy_target/.adk-install-receipt.json"
  set +e
  bash "$ROOT_DIR/scripts/devkit.sh" install plan \
    --tool claude-code \
    --mode copy \
    --target "$legacy_target" \
    --profile core \
    --output "$TMP_DIR/legacy-plan.json" \
    --summary-json >"$TMP_DIR/legacy.out" 2>"$TMP_DIR/legacy.err"
  legacy_rc=$?
  set -e
  [[ "$legacy_rc" -eq 1 ]] || { echo "[FAIL] retired receipt schema must fail closed: $schema" >&2; exit 1; }
  grep -q "expected adk-install-receipt/v3" "$TMP_DIR/legacy.err" || {
    echo "[FAIL] retired receipt schema rejection is not explicit: $schema" >&2
    exit 1
  }
done

set +e
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool vendor-specific-runtime \
  --mode copy \
  --target "$TMP_DIR/platform-bound-target" \
  --profile core \
  --output "$TMP_DIR/platform-plan.json" \
  --summary-json >"$TMP_DIR/platform.out" 2>"$TMP_DIR/platform.err"
platform_rc=$?
set -e
[[ "$platform_rc" -eq 1 ]] || { echo "[FAIL] unknown target must fail closed" >&2; exit 1; }
grep -q "vendor-specific-runtime" "$TMP_DIR/platform.err" || {
  echo "[FAIL] rejected target identity missing from canonical error" >&2
  exit 1
}

[[ ! -e "$ROOT_DIR/scripts/install-assets.sh" ]] || {
  echo "[FAIL] retired install-assets.sh compatibility wrapper returned" >&2
  exit 1
}

echo "[PASS] canonical transactional installer only accepts receipt v3"
