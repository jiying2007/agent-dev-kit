#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
workflow_dir = root / ".github/workflows"
workflow_files = sorted(workflow_dir.glob("*.yml"))
assert workflow_files, "no hosted workflows found"

consumer_files = sorted(workflow_dir.glob("*-consumer-contract.yml"))
assert len(consumer_files) == 1, consumer_files

# Every checkout is read-only by construction: no persisted git credential may remain.
for path in workflow_files:
    text = path.read_text(encoding="utf-8")
    checkout_count = text.count("uses: actions/checkout@")
    credential_count = text.count("persist-credentials: false")
    assert credential_count == checkout_count, (
        path.name,
        checkout_count,
        credential_count,
    )

# Superseded-run cancellation is safe only for PR validation. Non-PR runs must be
# isolated by run_id so fresh-main, scheduled, and manual evidence cannot cancel.
pr_cancellable = {
    workflow_dir / "ci.yml": "agent-dev-kit-ci-v2",
    workflow_dir / "security-codeql.yml": "security-codeql",
    workflow_dir / "platform-vnext.yml": "platform-vnext",
    workflow_dir / "digital-worker-contract.yml": "digital-worker-contract",
    consumer_files[0]: consumer_files[0].stem,
}
for path, group in pr_cancellable.items():
    text = path.read_text(encoding="utf-8")
    assert "permissions:\n  contents: read\n" in text, path.name
    assert f"group: {group}-${{{{ github.event.pull_request.number || github.run_id }}}}" in text, path.name
    assert "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text, path.name

for path in (consumer_files[0], workflow_dir / "digital-worker-contract.yml"):
    text = path.read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text, path.name
    assert "fetch-tags: true" in text, path.name

branch_gc = (workflow_dir / "branch-gc.yml").read_text(encoding="utf-8")
assert "cancel-in-progress: false" in branch_gc, "branch-gc write/cleanup evidence must stay non-cancellable"

release = (workflow_dir / "release.yml").read_text(encoding="utf-8")
assert "concurrency:" not in release, "release serialization semantics must remain unchanged"

dependency_review = (workflow_dir / "security-dependency-review.yml").read_text(encoding="utf-8")
assert "pull_request:" in dependency_review, "dependency review must remain PR-only"
assert "cancel-in-progress: true" in dependency_review, "PR-only dependency review may cancel superseded runs"
PY

echo "[PASS] hosted workflow hygiene"
