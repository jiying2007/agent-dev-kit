#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
workflow_dir = root / ".github/workflows"
consumer_files = sorted(workflow_dir.glob("*-consumer-contract.yml"))
assert len(consumer_files) == 1, consumer_files

targets = [
    workflow_dir / "platform-vnext.yml",
    workflow_dir / "digital-worker-contract.yml",
    consumer_files[0],
]
for path in targets:
    filename = path.name
    group = path.stem
    text = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read\n" in text, filename
    assert "persist-credentials: false" in text, filename
    assert f"group: {group}-${{{{ github.event.pull_request.number || github.run_id }}}}" in text, filename
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, filename

for path in (consumer_files[0], workflow_dir / "digital-worker-contract.yml"):
    text = path.read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text, path.name
    assert "fetch-tags: true" in text, path.name

branch_gc = (workflow_dir / "branch-gc.yml").read_text(encoding="utf-8")
assert "cancel-in-progress: false" in branch_gc, "branch-gc write/cleanup evidence must stay non-cancellable"
PY

echo "[PASS] hosted workflow hygiene"
