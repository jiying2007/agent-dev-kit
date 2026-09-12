#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PASS_COUNT=0
FAIL_COUNT=0
TOTAL=0

run_smoke() {
  local name="$1"
  shift
  TOTAL=$((TOTAL + 1))
  local rc=0
  timeout 5 bash "$@" </dev/null >/dev/null 2>&1 || rc=$?
  # 127 means the script path did not resolve; fatal signals are 128+ except timeout 124.
  if [[ $rc -eq 127 || ( $rc -ge 128 && $rc -ne 124 ) ]]; then
    echo "  FAIL  $name (fatal exit $rc)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  else
    echo "  PASS  $name (rc=$rc)"
    PASS_COUNT=$((PASS_COUNT + 1))
  fi
}

echo "=== Script Smoke Tests ==="
echo ""

cd "$ADK_ROOT"

run_smoke "devkit.sh help"                scripts/devkit.sh help
run_smoke "health-check.sh"              scripts/health-check.sh
run_smoke "lib-manifest.sh (source)"     -c "source scripts/lib-manifest.sh && type adk_require_manifest >/dev/null 2>&1"
run_smoke "version-manager.sh"           scripts/version-manager.sh
run_smoke "version-manager.sh verify"    scripts/version-manager.sh verify
run_smoke "backup-rollback.sh"           scripts/backup-rollback.sh
run_smoke "release-manager.sh"           scripts/release-manager.sh
run_smoke "auto-ops.sh"                  scripts/auto-ops.sh
run_smoke "monitoring.sh"                scripts/monitoring.sh
run_smoke "performance.sh"               scripts/performance.sh
run_smoke "security.sh"                  scripts/security.sh
run_smoke "token budget help"            scripts/check-token-budget.sh --help
run_smoke "devkit codify governance"     scripts/devkit.sh codify-governance
run_smoke "devkit knowledge compile"     scripts/devkit.sh knowledge-compile
run_smoke "devkit reuse before rebuild"  scripts/devkit.sh reuse-before-rebuild
run_smoke "devkit context experience"    scripts/devkit.sh context-experience
run_smoke "devkit goal check"            scripts/devkit.sh goal check --summary-json
run_smoke "devkit capability health"     scripts/devkit.sh capability health --summary-json
run_smoke "devkit perf budget"           scripts/devkit.sh perf budget --summary-json
run_smoke "official docs governance help" scripts/check-official-docs-governance.sh --help
run_smoke "runtime capabilities help"    scripts/check-runtime-capabilities.sh --help
run_smoke "run_all help"                 tests/run_all.sh --help
run_smoke "production field pilot help"  scripts/run-embedded-production-field-pilot.sh --help
run_smoke "workflow pilots help"         scripts/run-embedded-workflow-pilots.sh --help

echo ""
echo "=== Version Changelog Placeholder Test ==="
version="smoke-$(date +%s)"
changelog="$ADK_ROOT/CHANGELOG-$version.md"
cleanup_changelog() {
  rm -f "$changelog"
}
trap cleanup_changelog EXIT
bash "$ADK_ROOT/scripts/version-manager.sh" changelog --version "$version" >/dev/null
if rg -q '待补充|TODO|TBD|FIXME|PLACEHOLDER|占位(符|内容|文本|字段)' "$changelog"; then
  echo "  FAIL  changelog contains placeholder text"
  FAIL_COUNT=$((FAIL_COUNT + 1))
else
  echo "  PASS  changelog has no placeholder text"
  PASS_COUNT=$((PASS_COUNT + 1))
fi
TOTAL=$((TOTAL + 1))
cleanup_changelog

echo ""
echo "=== Summary: $PASS_COUNT/$TOTAL PASS, $FAIL_COUNT FAIL ==="

if [[ $FAIL_COUNT -gt 0 ]]; then
  exit 1
fi
