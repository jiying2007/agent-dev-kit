#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
export ADK_ROOT="${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON_SELECTION="explicit"
if [[ -n "${ADK_PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="${ADK_PYTHON_BIN}"
else
  PYTHON_SELECTION="auto"
  PYTHON_BIN=""
  for candidate in python3.12 python3.11 python3; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      PYTHON_BIN="${candidate}"
      break
    fi
  done
  PYTHON_BIN="${PYTHON_BIN:-python3}"
fi
REQUIRE_SUPPORTED="${ADK_REQUIRE_SUPPORTED_PYTHON:-0}"

case "${REQUIRE_SUPPORTED}" in
  0|1) ;;
  *)
    echo "[FAIL] ADK_REQUIRE_SUPPORTED_PYTHON must be 0 or 1" >&2
    exit 2
    ;;
esac

if [[ "${PYTHON_BIN}" == */* ]]; then
  [[ -x "${PYTHON_BIN}" ]] || {
    echo "[FAIL] ADK_PYTHON_BIN is not executable: ${PYTHON_BIN}" >&2
    exit 2
  }
elif ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[FAIL] ADK_PYTHON_BIN was not found on PATH: ${PYTHON_BIN}" >&2
  exit 2
fi

read -r PYTHON_VERSION PYTHON_SUPPORTED < <(
  "${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])), int(sys.version_info >= (3, 11)))'
) || {
  echo "[FAIL] unable to inspect ADK Python interpreter: ${PYTHON_BIN}" >&2
  exit 2
}

COMMAND="${1:-help}"
if [[ "${PYTHON_SUPPORTED}" != "1" && "${COMMAND}" != "doctor" ]]; then
  if [[ "${REQUIRE_SUPPORTED}" == "1" ]]; then
    echo "[FAIL] ADK requires Python 3.11+; ${PYTHON_SELECTION}-selected ${PYTHON_BIN}=${PYTHON_VERSION}" >&2
    echo "[INFO] set ADK_PYTHON_BIN to a reviewed Python 3.11/3.12 interpreter or use scripts/run-local-ci-parity.sh" >&2
    exit 2
  fi
  echo "[WARN] unsupported ADK Python ${PYTHON_VERSION}; ${PYTHON_SELECTION}-selected ${PYTHON_BIN}; result is development-only, not release evidence" >&2
  echo "[WARN] set ADK_REQUIRE_SUPPORTED_PYTHON=1 for fail-fast release validation" >&2
fi

exec "${PYTHON_BIN}" -m agent_dev_kit.cli "$@"
