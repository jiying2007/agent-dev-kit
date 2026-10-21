#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-runtime-boundary.sh"

summary="$("$ROOT_DIR/scripts/check-runtime-boundary.sh" --summary-json)"
echo "$summary" | grep -q '"status":"pass"' || {
  echo "[FAIL] runtime boundary summary did not pass" >&2
  exit 1
}
echo "$summary" | grep -q '"runtime_scope":"generic-adk"' || {
  echo "[FAIL] runtime boundary summary missing generic scope" >&2
  exit 1
}
echo "$summary" | grep -q '"direct_tool_targets":2' || {
  echo "[FAIL] runtime boundary summary missing direct tool target count" >&2
  exit 1
}
echo "$summary" | grep -q '"external_handoff_targets":1' || {
  echo "[FAIL] runtime boundary summary missing external handoff target count" >&2
  exit 1
}
echo "$summary" | grep -q '"codex_direct_tool_target":false' || {
  echo "[FAIL] runtime boundary summary must keep Codex out of direct tool targets" >&2
  exit 1
}
echo "$summary" | grep -q '"codex_handoff_mode":"source-to-live"' || {
  echo "[FAIL] runtime boundary summary missing Codex source-to-live handoff mode" >&2
  exit 1
}

python3 - "$ROOT_DIR" <<'PY'
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

source = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="adk-handoff-stream-") as temporary:
    root = Path(temporary)
    for directory in ("scripts", "tests", "docs", "manifests", "src/agent_dev_kit"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    for relative in (
        "scripts/lib-manifest.sh",
        "scripts/check-runtime-boundary.sh",
        "src/agent_dev_kit/__init__.py",
        "src/agent_dev_kit/manifest_query.py",
        "README.md",
    ):
        shutil.copyfile(source / relative, root / relative)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    guards = manifest["external_handoff_targets"]["codex"]["must_not"]
    guards.extend("extra-guard-{:04d}-{}".format(index, "x" * 512) for index in range(2048))
    env = os.environ.copy()
    env.pop("BASH_ENV", None)
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONUNBUFFERED"] = "1"
    # Only the guard list grows. The real checker still enforces every boundary.
    for expected in ("pass", "fail"):
        if expected == "fail":
            guards.remove("direct-write-live-home")
        (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = subprocess.run(
            ["bash", "scripts/check-runtime-boundary.sh", "--summary-json"],
            cwd=str(root), env=env, capture_output=True, text=True,
            timeout=20, check=False,
        )
        assert (result.returncode == 0) == (expected == "pass"), (result.stdout, result.stderr)
        assert json.loads(result.stdout)["status"] == expected, result.stdout
        assert result.stderr == "", result.stderr
        if expected == "fail":
            assert json.loads(result.stdout)["failures"] == 1, result.stdout
PY

echo "[PASS] runtime boundary including large and missing handoff guards"
