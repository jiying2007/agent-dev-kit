#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ADK_PYTHON_BIN:-python3}"

PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_BIN}" "${ROOT_DIR}/tests/test_workflow_ir.py"

[[ ! -e "$ROOT_DIR/scripts/check-workflow-ir.sh" ]] || {
  echo "[FAIL] retired Workflow IR shell wrapper returned" >&2
  exit 1
}
