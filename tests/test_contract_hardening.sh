#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
python3 "$ROOT/tests/test_contract_hardening.py"
exec python3 -m unittest discover -s "$ROOT/tests" -p test_safe_yaml.py
