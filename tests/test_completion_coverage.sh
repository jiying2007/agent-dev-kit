#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m unittest tests.test_completion_coverage -v
(
  cd /
  PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m agent_dev_kit.completion_coverage --help
  PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" python3 -m agent_dev_kit.completion_coverage \
    --input "$ROOT/tests/fixtures/completion_coverage_valid.json" --summary-json
)
