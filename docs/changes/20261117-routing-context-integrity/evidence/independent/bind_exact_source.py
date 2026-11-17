"""Bind the reviewed patch and changed files to the independently inspected Git source."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path("/workspace/scratch/d417066aafa8/agent-dev-kit")
BASE = "6d902f721f560f02883516e809fbd93a326405b6"
HEAD = "713d0d3a85c74bd9fe4b27a23c8dc8b2a066565a"
TREE = "1f9c586dadb20d6195263cd305efa9e5080291e2"
PATCH_SHA = "1b1b1c4d33ed504a36e7796c41421fff7939270a3e8f0b2dc2fbce5f752ace57"
PATCH = ROOT / "docs/changes/20261117-routing-context-integrity/evidence/original.patch"


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT, timeout=30)


if __name__ == "__main__":
    actual_head = git("rev-parse", "HEAD").decode().strip()
    actual_tree = git("rev-parse", HEAD + "^{tree}").decode().strip()
    original = git("diff", "--full-index", "--binary", "--no-ext-diff", BASE, HEAD)
    retained = PATCH.read_bytes()
    remote = git("ls-remote", "--exit-code", "origin", "refs/heads/fix/routing-context-integrity-20261117").decode().strip()
    paths = git("diff", "--name-only", "-z", BASE, HEAD).decode().rstrip("\0").split("\0")
    rows = []
    for path in paths:
        committed = git("show", f"{HEAD}:{path}")
        working = (ROOT / path).read_bytes()
        rows.append({"path": path, "sha256": hashlib.sha256(working).hexdigest(),
                     "bytes": len(working), "matches_commit": working == committed})
    value = {
        "observed_at": datetime.now(UTC).isoformat(), "base_commit": BASE, "head_commit": HEAD,
        "patch_command": ["git", "diff", "--full-index", "--binary", "--no-ext-diff", BASE, HEAD],
        "expected_tree": TREE, "actual_tree": actual_tree, "current_head_matches": actual_head == HEAD,
        "remote_branch_identity": remote, "remote_branch_head_matches": remote.split()[0] == HEAD,
        "tree_matches": actual_tree == TREE,
        "original_patch_sha256": hashlib.sha256(original).hexdigest(),
        "retained_patch_sha256": hashlib.sha256(retained).hexdigest(),
        "retained_patch_is_exact_cumulative_git_diff": original == retained,
        "patch_matches_expected_identity": hashlib.sha256(original).hexdigest() == PATCH_SHA,
        "changed_source_files": rows, "changed_source_count": len(rows),
        "all_changed_source_matches_commit": all(row["matches_commit"] for row in rows),
        "tracked_changes": git("status", "--porcelain=v1", "--untracked-files=no").decode(),
    }
    print(json.dumps(value, ensure_ascii=False, indent=2))
