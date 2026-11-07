#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
export ADK_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON_SELECTION="explicit"
if [[ -n "${ADK_PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="${ADK_PYTHON_BIN}"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
  # An active venv is the developer's selected build environment. Never
  # silently jump to a newer host interpreter and lose installed dependencies.
  PYTHON_SELECTION="venv"
  PYTHON_BIN="${VIRTUAL_ENV%/}/bin/python"
else
  PYTHON_SELECTION="auto"
  PYTHON_BIN=""
  for candidate in python3.12 python3; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      PYTHON_BIN="${candidate}"
      break
    fi
  done
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

if [[ "${PYTHON_BIN}" == */* ]]; then
  [[ -x "${PYTHON_BIN}" ]] || {
    echo "[FAIL] selected ADK Python (${PYTHON_SELECTION}) is not executable: ${PYTHON_BIN}" >&2
    exit 2
  }
elif ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[FAIL] ADK_PYTHON_BIN was not found on PATH: ${PYTHON_BIN}" >&2
  exit 2
fi

read -r PYTHON_VERSION PYTHON_SUPPORTED < <(
  "${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])), int(sys.version_info[:2] == (3, 12)))'
) || {
  echo "[FAIL] unable to inspect ADK Python interpreter: ${PYTHON_BIN}" >&2
  exit 2
}

if [[ "${PYTHON_SUPPORTED}" != "1" ]]; then
  echo "[FAIL] ADK requires CPython 3.12.x; ${PYTHON_SELECTION}-selected ${PYTHON_BIN}=${PYTHON_VERSION}" >&2
  echo "[INFO] use Python 3.12 .venv or set ADK_PYTHON_BIN to a reviewed Python 3.12 interpreter" >&2
  exit 2
fi

exec "${PYTHON_BIN}" -m agent_dev_kit.cli "$@"
