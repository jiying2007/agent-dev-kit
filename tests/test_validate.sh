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
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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

# Exercise the public consumer against isolated source copies: each identity
# projection must fail strict validation while quick retains its existing scope.
with tempfile.TemporaryDirectory(prefix="adk-strict-version-") as temp:
    fixture = Path(temp) / "source"
    shutil.copytree(root, fixture, symlinks=True, ignore=shutil.ignore_patterns(
        ".git", ".cache", ".ruff_cache", ".mypy_cache", "__pycache__", "build", "dist", "*.egg-info"))
    environment = dict(os.environ, ADK_PYTHON_BIN=sys.executable, ADK_ROOT=str(fixture))
    environment["PYTHONPATH"] = str(fixture / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")

    def fixture_projection(name):
        projection = fixture / name
        projection.parent.resolve().relative_to(fixture.resolve())
        return projection

    def replace_projection(projection, text):
        # Operate only on the fixture path: remove copied links before writing.
        fixture_projection(projection.relative_to(fixture))
        projection.unlink(missing_ok=True)
        projection.write_text(text, encoding="utf-8")

    outside_parent = Path(temp) / "outside-parent"
    outside_parent.mkdir()
    outside_target = outside_parent / "target.txt"
    outside_target.write_bytes(b"unchanged target\n")
    parent_link = fixture / "outside-parent"
    parent_link.symlink_to(outside_parent, target_is_directory=True)
    try:
        for operation in (
            lambda: fixture_projection("outside-parent/target.txt").read_bytes(),
            lambda: replace_projection(parent_link / "target.txt", "changed"),
        ):
            try:
                operation()
            except ValueError:
                pass
            else:
                raise AssertionError("fixture projection allowed an external parent")
        assert outside_target.read_bytes() == b"unchanged target\n"
    finally:
        parent_link.unlink()

    def consume(*arguments):
        completed = subprocess.run(
            [sys.executable, "-m", "agent_dev_kit.cli", "validate", *arguments, "--summary-json"],
            cwd=temp, env=environment, capture_output=True, text=True, check=False,
        )
        return completed.returncode, json.loads(completed.stdout)

    for name in ("CONTEXT.md", "manifests/software_m5_eval_contract.json"):
        projection = fixture_projection(name)
        original_text = projection.read_text(encoding="utf-8")
        linked_target = Path(temp) / name.replace("/", "-")
        original_bytes = original_text.encode("utf-8")
        linked_target.write_bytes(original_bytes)
        version = json.loads((fixture / "manifest.json").read_text(encoding="utf-8"))["version"]
        for missing in (False, True):
            projection.unlink()
            projection.symlink_to(linked_target)
            try:
                if missing:
                    projection.unlink()
                    expected = "missing " + name
                else:
                    replace_projection(projection, original_text.replace(version, "0.0.0"))
                    assert projection.is_file() and not projection.is_symlink(), projection
                    expected = "version mismatch in " + name
                assert linked_target.read_bytes() == original_bytes, linked_target
                rc, payload = consume("--strict")
                assert rc == 1 and payload["status"] == "fail", (name, missing, rc, payload)
                assert expected in payload["failures"], (expected, payload)
                for arguments in (("--quick",), ("--strict", "--quick")):
                    rc, payload = consume(*arguments)
                    assert rc == 0 and payload["status"] == "pass", (name, missing, arguments, payload)
            finally:
                replace_projection(projection, original_text)
                assert projection.is_file() and not projection.is_symlink(), projection
                assert linked_target.read_bytes() == original_bytes, linked_target
PY

[[ ! -e "$ROOT_DIR/scripts/release-validate.sh" ]] || {
  echo "[FAIL] retired release validation wrapper returned" >&2
  exit 1
}

echo "[PASS] validate"
