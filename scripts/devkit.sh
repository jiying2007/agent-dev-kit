#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
export ADK_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

# shellcheck source=./lib-python-runtime.sh
source "${SCRIPT_DIR}/lib-python-runtime.sh"
adk_select_python

if [[ "$#" -eq 1 && "$1" == "--check-python" ]]; then
  printf '[PASS] CPython %s (%s): %s\n' "${PYTHON_VERSION}" "${PYTHON_SELECTION}" "${PYTHON_BIN}"
  exit 0
fi

exec "${PYTHON_BIN}" -m agent_dev_kit.cli "$@"
