#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ADK_PYTHON_BIN:-python3}"

PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "${PYTHON_BIN}" -m agent_dev_kit.workflow_ir --root "${ROOT_DIR}" "$@"
