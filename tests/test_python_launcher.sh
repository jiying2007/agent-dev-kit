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

# Retired interpreters must fail before loading any ADK Python package, even
# for informational commands. No legacy environment bypass exists.
for version in 3.8.20 3.10.22 3.11.14 3.13.0 3.14.0; do
  old_python="$TMP_DIR/python-$version"
  cat >"$old_python" <<SH
#!/usr/bin/env bash
set -euo pipefail
if [[ "\${1:-}" == "-c" ]]; then
  echo "$version 0"
  exit 0
fi
echo "[FAIL] unsupported interpreter reached ADK CLI" >&2
exit 99
SH
  chmod +x "$old_python"
  if ADK_PYTHON_BIN="$old_python" bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/old.out" 2>&1; then
    echo "[FAIL] unsupported Python $version was accepted" >&2
    exit 1
  fi
  rg -q --fixed-strings -- "ADK requires CPython 3.12.x" "$TMP_DIR/old.out"
done

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

env -u ADK_PYTHON_BIN -u VIRTUAL_ENV PATH="$auto_bin:$PATH" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/auto.out" 2>"$TMP_DIR/auto.err"
rg -q --fixed-strings -- "auto-selected-python3.12" "$TMP_DIR/auto.out"

# An activated venv must override the host's auto Python 3.12, and explicit
# ADK_PYTHON_BIN must still override the activated venv.
mkdir -p "$TMP_DIR/venv/bin"
cat >"$TMP_DIR/venv/bin/python" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "-c" ]]; then
  echo "3.12.14 1"
  exit 0
fi
echo "venv-selected-python3.12"
SH
chmod +x "$TMP_DIR/venv/bin/python"
env -u ADK_PYTHON_BIN VIRTUAL_ENV="$TMP_DIR/venv" PATH="$auto_bin:$PATH" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/venv.out" 2>"$TMP_DIR/venv.err"
rg -q --fixed-strings -- "venv-selected-python3.12" "$TMP_DIR/venv.out"

ADK_PYTHON_BIN="$auto_bin/python3.12" VIRTUAL_ENV="$TMP_DIR/venv" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/override.out" 2>"$TMP_DIR/override.err"
rg -q --fixed-strings -- "auto-selected-python3.12" "$TMP_DIR/override.out"

mkdir -p "$TMP_DIR/old-venv/bin"
ln -s "$TMP_DIR/python-3.11.14" "$TMP_DIR/old-venv/bin/python"
if env -u ADK_PYTHON_BIN VIRTUAL_ENV="$TMP_DIR/old-venv" PATH="$auto_bin:$PATH" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/old-venv.out" 2>&1; then
  echo "[FAIL] unsupported activated venv silently fell back to host Python" >&2
  exit 1
fi
rg -q 'venv-selected .*3.11.14' "$TMP_DIR/old-venv.out"

if env -u ADK_PYTHON_BIN VIRTUAL_ENV="$TMP_DIR/missing-venv" PATH="$auto_bin:$PATH" \
  bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/missing-venv.out" 2>&1; then
  echo "[FAIL] missing activated venv silently fell back to host Python" >&2
  exit 1
fi
rg -q --fixed-strings -- 'selected ADK Python (venv) is not executable' "$TMP_DIR/missing-venv.out"

ADK_PYTHON_BIN=python3 bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/help.out" 2>"$TMP_DIR/help.err"
rg -q --fixed-strings -- "Commands:" "$TMP_DIR/help.out"

doctor_rc=0
ADK_PYTHON_BIN=python3 bash "$ROOT_DIR/scripts/devkit.sh" doctor --summary-json >"$TMP_DIR/doctor.json" 2>"$TMP_DIR/doctor.err" || doctor_rc=$?
[[ "$doctor_rc" -eq 0 || "$doctor_rc" -eq 1 ]] || {
  echo "[FAIL] doctor must remain available on current Python" >&2
  exit 1
}
python3 - "$TMP_DIR/doctor.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    data = json.load(stream)
support = data["environment_support"]
assert support["python_minimum"] == "3.12", support
assert support["python_support_scope"] == "build-control-plane-only", support
assert support["python_ci_matrix"] == ["3.12"], support
assert support["delivered_skill_requires_adk_python"] is False, support
PY

for version in 3.12.12; do
  fixture="$TMP_DIR/python-$version"
  cat >"$fixture" <<SH
#!/usr/bin/env bash
if [[ "\${1:-}" == "-c" ]]; then
  echo "$version 1"
  exit 0
fi
echo "fixture-compatible-runtime"
SH
  chmod +x "$fixture"
  ADK_PYTHON_BIN="$fixture" bash "$ROOT_DIR/scripts/devkit.sh" help >"$TMP_DIR/class.out" 2>"$TMP_DIR/class.err"
  rg -q 'fixture-compatible-runtime' "$TMP_DIR/class.out"
done

[[ ! -e "$ROOT_DIR/src/agent_dev_kit/compat.py" ]] || {
  echo "[FAIL] retired Python 3.8 compatibility module has returned" >&2
  exit 1
}
python3 - "$ROOT_DIR/pyproject.toml" <<'PY'
import pathlib
import sys
import tomllib

metadata = tomllib.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
project = metadata["project"]
assert project["requires-python"] == ">=3.12,<3.13", project
assert set(project["dependencies"]) == {"PyYAML==6.0.3", "jsonschema==4.26.0"}, project
assert metadata["tool"]["ruff"]["target-version"] == "py312", metadata
assert metadata["tool"]["mypy"]["python_version"] == "3.12", metadata
assert "test" not in project.get("optional-dependencies", {}), "retired empty test extra remains"
PY
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_python_support.py"
echo "[PASS] ADK Python 3.12-only launcher and build-runtime boundary hold"
