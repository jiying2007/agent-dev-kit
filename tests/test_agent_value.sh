#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ADK_PYTHON_BIN:-python3}"

PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_BIN}" "${ROOT_DIR}/tests/test_agent_value.py"

PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_BIN}" -m agent_dev_kit.agent_value \
  --manifest-root "${ROOT_DIR}" \
  --summary-json | rg -q '"emitter_status":"not-measured"'

echo "[PASS] Agent value lifecycle contract test"
