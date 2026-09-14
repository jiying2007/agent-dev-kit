#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
module_path = root / "tools/control_plane/branch_gc.py"
spec = importlib.util.spec_from_file_location("adk_branch_gc", module_path)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

legacy_sha = "fc2d786c6c2c4efe50dc10ca6e0eec167c25a57a"
legacy_main_sha = "b15e28daec9caad7e29c17e39f323cdf307b3dae"
retired_sha = "3e8e15e873c43ccc5548ad6a2567a3aae6f35963"
main_sha = "ecf53500ede2b407ca9ff39d605ea603135672d0"
active_sha = "1" * 40
changed_sha = "2" * 40

registry = module.load_retired_registry(root / "manifests/branch_gc_retired.json")
legacy_entry = next(item for item in registry.values() if item.sha == legacy_sha)
assert legacy_entry.proof == "ancestor-of-main"
assert legacy_entry.reviewed_against_main == legacy_main_sha

entry = next(item for item in registry.values() if item.sha == retired_sha)
assert entry.proof == "ancestor-of-main"
assert entry.reviewed_against_main == main_sha
retired_branch = entry.branch
subject_registry = {retired_branch: entry}


class FakeClient:
    def __init__(
        self,
        *,
        retired_branch_sha: str = retired_sha,
        open_retired_pr: bool = False,
    ) -> None:
        self.repo = "example/repo"
        self.owner = "example"
        self.retired_branch_sha = retired_branch_sha
        self.open_retired_pr = open_retired_pr
        self.deleted: list[str] = []

    def _branch(self, name: str, sha: str) -> dict[str, Any]:
        return {"name": name, "commit": {"sha": sha}, "protected": False}

    def list_branches(self) -> list[dict[str, Any]]:
        return [
            self._branch("main", main_sha),
            self._branch(retired_branch, self.retired_branch_sha),
            self._branch("maintenance/pip/example", active_sha),
        ]

    def get_branch(self, branch: str) -> dict[str, Any]:
        if branch == "main":
            return self._branch("main", main_sha)
        if branch == retired_branch:
            return self._branch(branch, self.retired_branch_sha)
        if branch == "maintenance/pip/example":
            return self._branch(branch, active_sha)
        raise module.BranchGCError(f"missing branch: {branch}")

    def pulls(
        self,
        branch: str,
        state: str,
        base: str | None = None,
    ) -> list[dict[str, Any]]:
        if branch == retired_branch and state == "open" and self.open_retired_pr:
            return [{"number": 99}]
        return []

    def pull(self, number: int) -> dict[str, Any]:
        raise AssertionError(f"unexpected PR lookup: {number}")

    def compare(self, base_sha: str, head_sha: str) -> dict[str, Any]:
        if base_sha == head_sha:
            return {
                "status": "identical",
                "merge_base_commit": {"sha": base_sha},
            }
        if base_sha == retired_sha and head_sha == main_sha:
            return {
                "status": "ahead",
                "merge_base_commit": {"sha": retired_sha},
            }
        return {
            "status": "diverged",
            "merge_base_commit": {"sha": "0" * 40},
        }

    def delete_branch(self, branch: str) -> None:
        self.deleted.append(branch)


client = FakeClient()
base_sha, candidates, skipped, scanned = module.evaluate(client, "main", subject_registry)
assert base_sha == main_sha
assert scanned == 2
assert len(candidates) == 1
candidate = candidates[0]
assert candidate.branch == retired_branch
assert candidate.sha == retired_sha
assert candidate.basis == "explicit-retired-ancestor"
assert candidate.proof == "ancestor-of-main"
assert any(
    item["branch"] == "maintenance/pip/example"
    and item["reason"] == "no-exact-merged-pr"
    for item in skipped
)

ok, reason = module.revalidate_and_delete(client, candidate, "main", subject_registry)
assert ok is True
assert reason is None
assert client.deleted == [retired_branch]

changed = FakeClient(retired_branch_sha=changed_sha)
_, changed_candidates, changed_skipped, _ = module.evaluate(changed, "main", subject_registry)
assert changed_candidates == []
assert any(
    item["branch"] == retired_branch
    and item["reason"] == "retired-sha-mismatch"
    and item["expected_sha"] == retired_sha
    for item in changed_skipped
)

with_open_pr = FakeClient(open_retired_pr=True)
_, open_candidates, open_skipped, _ = module.evaluate(with_open_pr, "main", subject_registry)
assert open_candidates == []
assert any(
    item["branch"] == retired_branch and item["reason"] == "open-pr"
    for item in open_skipped
)

invalid_entry = module.RetiredEntry(
    branch=entry.branch,
    sha=entry.sha,
    proof=entry.proof,
    reviewed_against_main="3" * 40,
    reason=entry.reason,
)
invalid_registry = {invalid_entry.branch: invalid_entry}
invalid_client = FakeClient()
_, invalid_candidates, invalid_skipped, _ = module.evaluate(
    invalid_client,
    "main",
    invalid_registry,
)
assert invalid_candidates == []
assert any(
    item["branch"] == retired_branch and item["reason"] == "retired-proof-invalid"
    for item in invalid_skipped
)

print("branch GC ancestor retirement contract: PASS")
PY
