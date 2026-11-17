"""Independent, read-only binding audit for the final retained observations."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
CHANGE = ROOT / "docs/changes/20261117-routing-context-integrity"
EVIDENCE = CHANGE / "evidence"
BASE = "6d902f721f560f02883516e809fbd93a326405b6"
HEAD = "713d0d3a85c74bd9fe4b27a23c8dc8b2a066565a"
TREE = "1f9c586dadb20d6195263cd305efa9e5080291e2"
PATCH_SHA = "1b1b1c4d33ed504a36e7796c41421fff7939270a3e8f0b2dc2fbce5f752ace57"
INDEX_SHA = "da6836967f0275b8b3e8794ba4df1db238d8daf70c6a22ce130ea14bc181c2fe"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def load(path: str) -> dict:
    return json.loads((EVIDENCE / path).read_bytes())


def main() -> None:
    state = load("review-input-state.json")
    index_raw = (EVIDENCE / "observation-index.json").read_bytes()
    index = json.loads(index_raw)
    checks = {
        "current_head_is_reviewed_source": git("rev-parse", "HEAD").decode().strip() == HEAD,
        "source_tree_matches": git("rev-parse", HEAD + "^{tree}").decode().strip() == TREE,
        "review_input_identity_matches": (
            state["source_commit"] == HEAD and state["base_commit"] == BASE
            and state["source_tree"] == TREE and state["original_patch_sha256"] == PATCH_SHA
            and state["observation_index_sha256"] == INDEX_SHA
        ),
        "observation_index_digest_matches": digest(index_raw) == INDEX_SHA,
    }
    entries = index["files"]
    paths = [entry["path"] for entry in entries]
    assert len(paths) == len(set(paths)), "duplicate observation index paths"
    invalid_entries = []
    observed_bytes = 0
    for entry in entries:
        path = EVIDENCE / entry["path"]
        assert path.resolve().is_relative_to(EVIDENCE), entry["path"]
        assert not path.is_symlink() and path.is_file(), entry["path"]
        assert all(not p.is_symlink() for p in path.parents), entry["path"]
        raw = path.read_bytes()
        observed_bytes += len(raw)
        if len(raw) != entry["bytes"] or digest(raw) != entry["sha256"]:
            invalid_entries.append(entry["path"])
    checks["all_indexed_raw_observations_match"] = not invalid_entries
    checks["index_counts_match"] = len(entries) == index["file_count"] == 136
    checks["index_bytes_match"] = observed_bytes == index["total_bytes"] == 2062950
    patch = git("diff", "--full-index", "--binary", "--no-ext-diff", BASE, HEAD)
    checks["original_patch_is_exact_cumulative_diff"] = (
        patch == (EVIDENCE / "original.patch").read_bytes() and digest(patch) == PATCH_SHA
    )

    before = load("final/sources-final-before.json")
    after = load("final/sources-final-after.json")
    checks["source_inputs_unchanged_during_full_run"] = before["files"] == after["files"]
    checks["source_input_count_matches"] = before["file_count"] == after["file_count"] == len(before["files"]) == 1082
    excluded = before["excluded_prefixes"]
    assert excluded == after["excluded_prefixes"] == ["docs/changes/", "reports/", "evals/results/"]
    tree_records = git("ls-tree", "-rz", "--full-tree", HEAD).split(b"\0")
    source_blobs = {}
    for item in tree_records:
        if not item:
            continue
        metadata, raw_path = item.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        path = raw_path.decode()
        if mode in ("100644", "100755") and not any(path.startswith(prefix) for prefix in excluded):
            assert kind == "blob"
            source_blobs[path] = oid
    checks["snapshot_covers_all_operational_tracked_files"] = set(source_blobs) == set(before["files"])
    request = "".join(oid + "\n" for oid in source_blobs.values()).encode()
    cat = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT, input=request, capture_output=True, check=True).stdout
    offset = 0
    mismatches = []
    current_differences = []
    for path, oid in source_blobs.items():
        end = cat.index(b"\n", offset)
        response_oid, kind, size = cat[offset:end].decode().split()
        assert response_oid == oid and kind == "blob"
        size = int(size)
        raw = cat[end + 1:end + 1 + size]
        offset = end + 1 + size + 1
        expected = before["files"][path]
        if len(raw) != expected["bytes"] or digest(raw) != expected["sha256"]:
            mismatches.append(path)
        current = (ROOT / path).read_bytes()
        if digest(current) != expected["sha256"]:
            current_differences.append(path)
    assert offset == len(cat)
    checks["all_operational_inputs_match_reviewed_commit"] = not mismatches
    checks["current_operational_differences_are_only_reviewed_attributes"] = current_differences == [".gitattributes"]
    changed = git("diff", "--name-only", HEAD).decode().splitlines()
    checks["packaging_changes_are_bounded"] = all(
        path == ".gitattributes" or path.startswith("docs/changes/20261117-routing-context-integrity/")
        for path in changed
    )

    summary = load("final/integration-summary.json")
    timing = load("final/full-timing.json")
    full_stage = next(stage for stage in summary["stages"] if stage["name"] == "full-regression")
    checks["all_six_final_stages_exited_zero"] = len(summary["stages"]) == 6 and all(
        stage["exit_code"] == 0 for stage in summary["stages"]
    )
    checks["timing_has_102_unique_passing_groups"] = (
        timing["total"] == timing["pass"] == len(timing["tests"]) == 102
        and timing["fail"] == 0
        and len({test["name"] for test in timing["tests"]}) == 102
        and all(test["status"] == "pass" for test in timing["tests"])
    )
    log = (EVIDENCE / "final/full-regression.log").read_text()
    checks["raw_full_log_has_actual_passing_summary"] = log.rstrip().endswith(
        "[SUMMARY] tests=102 pass=102 fail=0\nAll tests passed"
    )
    quality = load("quality/summary.json")
    checks["quality_gate_logs_match_recorded_digests"] = all(
        digest((EVIDENCE / "quality" / Path(gate["log"]).name).read_bytes()) == gate["log_sha256"]
        and gate["exit_code"] == 0 for gate in quality["gates"]
    )
    interruptions = [load(name + "/interruption.json") for name in (
        "first-incomplete-run", "source-root-environment-failure"
    )]
    checks["both_incomplete_executions_remain_explicit"] = all(
        result["exec_exit_code"] == 130 and result["full_regression_pass_claimed"] is False
        for result in interruptions
    )
    result = {
        "reviewer_id": "independent-reviewer-routing-context-20261117",
        "observed_at": datetime.now(UTC).isoformat(),
        "base_commit": BASE, "head_commit": HEAD, "source_tree": TREE,
        "original_patch_sha256": PATCH_SHA, "observation_index_sha256": INDEX_SHA,
        "indexed_observation_files": len(entries), "indexed_observation_bytes": observed_bytes,
        "operational_source_files": len(source_blobs), "source_snapshot_excluded_prefixes": excluded,
        "invalid_index_entries": invalid_entries, "source_commit_mismatches": mismatches,
        "current_operational_differences": current_differences,
        "full_regression": {key: full_stage[key] for key in (
            "started_at", "completed_at", "elapsed_seconds", "exit_code"
        )},
        "checks": checks, "all_checks_passed": all(checks.values()),
        "scope": "Read-only source, index, execution-log and packaging integrity audit; no new product/runtime/device execution",
    }
    destination = EVIDENCE / "independent/final-evidence-integrity.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    assert result["all_checks_passed"], "final evidence integrity audit failed"


if __name__ == "__main__":
    main()
