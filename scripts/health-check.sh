#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

usage() {
  cat <<'USAGE'
健康检查脚本

Usage:
  ./scripts/health-check.sh <command> [options]

Commands:
  check-all
  check-structure
  check-dependencies
  check-configuration
  check-tests
  check-quality

Options:
  --verbose
  --fix
  --summary-json
  -h, --help
USAGE
}

COMMAND="${1:-}"
[[ -n "$COMMAND" ]] || { usage; exit 1; }
shift || true
VERBOSE=0
FIX=0
SUMMARY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --verbose) VERBOSE=1 ;;
    --fix) FIX=1 ;;
    --summary-json) SUMMARY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[FAIL] unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
  shift
done

run_group() {
  local group="$1"
  python3 - "$ROOT_DIR" "$group" "$FIX" <<'PY'
import sys
from pathlib import Path
from agent_dev_kit.health_contract import (
    check_configuration, check_dependencies, check_quality, check_structure, check_tests,
)
root = Path(sys.argv[1])
group = sys.argv[2]
run_tests = sys.argv[3] == "1"
funcs = {
    "structure": lambda: check_structure(root),
    "dependencies": check_dependencies,
    "configuration": lambda: check_configuration(root),
    "tests": lambda: check_tests(root, run_tests),
    "quality": lambda: check_quality(root),
}
failures = funcs[group]()
for item in failures:
    print(f"[FAIL] {item}", file=sys.stderr)
raise SystemExit(1 if failures else 0)
PY
}

case "$COMMAND" in
  check-all)
    args=(--root "$ROOT_DIR")
    [[ "$FIX" -eq 1 ]] && args+=(--run-tests)
    [[ "$SUMMARY" -eq 1 ]] && args+=(--summary-json)
    python3 -m agent_dev_kit.health_contract "${args[@]}"
    ;;
  check-structure) run_group structure ;;
  check-dependencies) run_group dependencies ;;
  check-configuration) run_group configuration ;;
  check-tests) run_group tests ;;
  check-quality) run_group quality ;;
  *) echo "[FAIL] unknown command: $COMMAND" >&2; usage >&2; exit 1 ;;
esac
