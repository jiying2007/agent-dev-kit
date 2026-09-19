#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ ! -e "$ROOT_DIR/tests/test_skill_governance_v3.py" ]] || { echo "[FAIL] retired skill governance v3 Python test returned" >&2; exit 1; }
[[ ! -e "$ROOT_DIR/tests/test_skill_governance_v3.sh" ]] || { echo "[FAIL] retired skill governance v3 shell test returned" >&2; exit 1; }
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
python3 -m unittest tests.test_skill_governance -v
