#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ "${ADK_TEST_SUITE_MODE:-full}" == "quick" ]]; then
  summary="$(bash "$ROOT_DIR/scripts/devkit.sh" validate --quick --summary-json)"
else
  bash "$ROOT_DIR/scripts/devkit.sh" validate --quick
  summary="$(bash "$ROOT_DIR/scripts/devkit.sh" validate --strict --summary-json)"
fi
if [[ -n "${ADK_TEST_SUITE_DIR:-}" ]]; then
  printf '%s\n' "$summary" >"${ADK_TEST_SUITE_DIR}/validate-summary.json"
fi
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] validate summary did not pass" >&2
  exit 1
}
echo "$summary" | grep -q '"change_sets":1' || {
  echo "[FAIL] validate summary missing change set count" >&2
  exit 1
}

[[ ! -e "$ROOT_DIR/scripts/validate-assets.sh" ]] || { echo "[FAIL] retired validate-assets.sh returned" >&2; exit 1; }

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" <<'PY'
import contextlib
import io
import json
import sys

import agent_dev_kit.cli as cli
import agent_dev_kit.validation_contract as validation_contract

root = sys.argv[1]
assert str(cli.ROOT) == root, (cli.ROOT, root)

original = validation_contract._governance_gate_failure
try:
    validation_contract._governance_gate_failure = (
        lambda root, command, label: "forced-runtime-boundary-failure"
        if label == "runtime-boundary"
        else None
    )
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        rc = cli._cmd_validate(["--strict", "--summary-json"])
finally:
    validation_contract._governance_gate_failure = original

payload = json.loads(stream.getvalue())
assert rc == 1, rc
assert payload["status"] == "fail", payload
assert "forced-runtime-boundary-failure" in payload["failures"], payload
PY

[[ ! -e "$ROOT_DIR/scripts/release-validate.sh" ]] || {
  echo "[FAIL] retired release validation wrapper returned" >&2
  exit 1
}

echo "[PASS] validate"
