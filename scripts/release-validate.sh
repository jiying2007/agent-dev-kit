#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

exec env ADK_REQUIRE_SUPPORTED_PYTHON=1 \
  bash "${ROOT_DIR}/scripts/devkit.sh" validate --strict "$@"
