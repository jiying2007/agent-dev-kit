#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_runtime_bundle.py"

echo '[PASS] isolated runtime bundle identity and dirty-source rejection; no production receipt emitted'
