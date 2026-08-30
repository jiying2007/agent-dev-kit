#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if ADK_PYTHON_BIN=python-that-does-not-exist \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/missing.out" 2>&1; then
  echo "[FAIL] missing ADK_PYTHON_BIN unexpectedly passed" >&2
  exit 1
fi
rg -q --fixed-strings -- "ADK_PYTHON_BIN was not found on PATH" "$TMP_DIR/missing.out"

old_python="$TMP_DIR/python-old"
cat >"$old_python" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "-c" ]]; then
  echo "3.8.10 0"
  exit 0
fi
echo "[FAIL] old-python fixture reached CLI execution" >&2
exit 99
SH
chmod +x "$old_python"

if ADK_PYTHON_BIN="$old_python" ADK_REQUIRE_SUPPORTED_PYTHON=1 \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/old.out" 2>&1; then
  echo "[FAIL] strict unsupported Python fixture unexpectedly passed" >&2
  exit 1
fi
rg -q --fixed-strings -- "ADK requires Python 3.11+" "$TMP_DIR/old.out"
rg -q --fixed-strings -- "scripts/run-local-ci-parity.sh" "$TMP_DIR/old.out"

if ADK_REQUIRE_SUPPORTED_PYTHON=invalid \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/invalid.out" 2>&1; then
  echo "[FAIL] invalid strict Python mode unexpectedly passed" >&2
  exit 1
fi
rg -q --fixed-strings -- "ADK_REQUIRE_SUPPORTED_PYTHON must be 0 or 1" "$TMP_DIR/invalid.out"

auto_bin="$TMP_DIR/auto-bin"
mkdir -p "$auto_bin"
cat >"$auto_bin/python3.12" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "-c" ]]; then
  echo "3.12.9 1"
  exit 0
fi
echo "auto-selected-python3.12"
SH
cat >"$auto_bin/python3.11" <<'SH'
#!/usr/bin/env bash
echo "[FAIL] python3.11 fixture selected before python3.12" >&2
exit 98
SH
cat >"$auto_bin/python3" <<'SH'
#!/usr/bin/env bash
echo "[FAIL] python3 fixture selected before python3.12" >&2
exit 97
SH
chmod +x "$auto_bin/python3.12" "$auto_bin/python3.11" "$auto_bin/python3"

env -u ADK_PYTHON_BIN PATH="$auto_bin:$PATH" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/auto.out" 2>"$TMP_DIR/auto.err"
rg -q --fixed-strings -- "auto-selected-python3.12" "$TMP_DIR/auto.out"

ADK_PYTHON_BIN=python3 bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/help.out" 2>"$TMP_DIR/help.err"
rg -q --fixed-strings -- "Commands:" "$TMP_DIR/help.out"

doctor_rc=0
ADK_PYTHON_BIN=python3 ADK_REQUIRE_SUPPORTED_PYTHON=1 \
  bash "$ROOT_DIR/scripts/devkit.sh" doctor --summary-json >"$TMP_DIR/doctor.json" 2>"$TMP_DIR/doctor.err" || doctor_rc=$?
[[ "$doctor_rc" -eq 0 || "$doctor_rc" -eq 1 ]] || {
  echo "[FAIL] doctor must remain available for unsupported-environment diagnostics" >&2
  exit 1
}
python3 - "$TMP_DIR/doctor.json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)
assert "environment_support" in data
assert "python_supported" in data["environment_support"]
PY

echo "[PASS] ADK Python launcher selection and fail-fast contract hold"
