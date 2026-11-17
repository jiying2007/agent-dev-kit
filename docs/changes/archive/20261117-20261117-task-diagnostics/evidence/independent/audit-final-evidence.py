"""Independently check exact product and retained evidence bytes; no mutations."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
TOP = ROOT.parent
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
BASE = "5f113b8f5ae6f83662d41d99d0907026f4e44c9d"
HEAD = "d01d1bcb7c2f322c342656a95e523fba8b55505e"
TREE = "4fe0cfa656ad7feeabf1a25daa9012dcfd673ce0"
C1 = ROOT / "docs/changes/20261117-task-diagnostics"
C2 = ROOT / "docs/changes/20261117-goal-replan-replay"


def git(*args, cwd=ROOT):
    return subprocess.check_output([RTK, "proxy", "git", *args], cwd=cwd)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular_bytes(path):
    assert not path.is_symlink(), str(path)
    assert path.is_file(), str(path)
    return path.read_bytes()


frozen = json.loads(regular_bytes(C1 / "evidence/review-input-state.json"))
assert (frozen["base_commit"], frozen["head_commit"], frozen["tree"]) == (BASE, HEAD, TREE)
assert git("rev-parse", HEAD + "^{tree}").decode().strip() == TREE
product_checks = []
for name, expected in frozen["product_sources"].items():
    raw = regular_bytes(ROOT / name)
    assert raw == git("show", f"{HEAD}:{name}"), name
    assert digest(raw) == expected["sha256"] and len(raw) == expected["bytes"], name
    product_checks.append(name)
changed_products = [
    path for path in git("diff", "--name-only", BASE, HEAD).decode().splitlines()
    if not path.startswith("docs/changes/")
]
assert set(changed_products) == set(product_checks)

inventory_checks = []
for item in frozen["current_change_inputs"]:
    path = Path(item["path"])
    assert not path.is_absolute() and ".." not in path.parts
    assert item["path"].startswith((
        "docs/changes/20261117-task-diagnostics/",
        "docs/changes/20261117-goal-replan-replay/",
    ))
    raw = regular_bytes(ROOT / path)
    assert len(raw) == item["bytes"] and digest(raw) == item["sha256"], item["path"]
    inventory_checks.append(item["path"])

bundle_checks = []
for name in (
    C1 / "evidence/final/raw-command-output.json",
    C1 / "evidence/full-attempt1/raw-command-output.json",
    C1 / "evidence/implementation-observations.json",
    C2 / "evidence/implementation-observations.json",
    C1 / "evidence/footprint-fix-observations.json",
):
    bundle = json.loads(regular_bytes(name))
    counts = 0
    for key, observation in bundle["observations"].items():
        assert observation["encoding"] == "UTF-8", key
        raw = observation["content"].encode("utf-8")
        assert len(raw) == observation["bytes"] and digest(raw) == observation["sha256"], key
        assert raw == regular_bytes(Path(observation["source_path"])), key
        counts += 1
    bundle_checks.append({"path":str(name.relative_to(ROOT)), "observations":counts,
                          "raw_utf8_bytes_and_original_sources_equal":True})

counterexamples = []
for path in sorted((C2 / "evidence/original-counterexample").iterdir()):
    raw = regular_bytes(path)
    original = TOP / "independent-review/c2-attestation-replay" / path.name
    assert raw == regular_bytes(original), path.name
    counterexamples.append({"path":path.name, "sha256":digest(raw), "bytes":len(raw)})
expected_frozen = {
    "frozen-inputs.json":"1bddace1b0edebc3475f8e51f1cd0d9a4878c5e9f0c4b17d6d2bf001a2779d60",
    "replay_frozen_probe.py":"b6f5a02415a3310e12fc554f8d166767bf585709b1469c5bd1ecbe10f8ebfa7d",
}
for name, value in expected_frozen.items():
    assert digest(regular_bytes(C2 / "evidence/original-counterexample" / name)) == value

patch = git("diff", "--no-ext-diff", "--binary", BASE, HEAD)
for change in (C1, C2):
    assert regular_bytes(change / "evidence/original.patch") == patch
assert digest(patch) == "52fd79f40d5a6592d646c7897d5af605c32d88e6a3ade2c11e2ad41090affafe"

runs = []
for retained, original, worktree, expected_pass, expected_fail in (
    ("full-attempt1", "adk-local-final", "adk-11.4.0-verify", 101, 1),
    ("final", "adk-local-final-attempt2", "adk-11.4.0-final-verify", 102, 0),
):
    bundle_dir = C1 / "evidence" / retained
    original_dir = TOP / "delivery-11.4.0" / original
    for name in ("results.json", "full-timing.json", "source-before.json", "source-after.json", "summary.json"):
        assert regular_bytes(bundle_dir / name) == regular_bytes(original_dir / name), name
    before = json.loads(regular_bytes(bundle_dir / "source-before.json"))
    after = json.loads(regular_bytes(bundle_dir / "source-after.json"))
    timing = json.loads(regular_bytes(bundle_dir / "full-timing.json"))
    results = json.loads(regular_bytes(bundle_dir / "results.json"))
    assert before == after and before["tracked_status"] == ""
    root = TOP / worktree
    names = git("ls-files", "-z", cwd=root).decode().split("\0")
    expected_paths = {
        name for name in names if name and not name.startswith(("docs/changes/", "reports/", "evals/results/"))
        and (root / name).is_file()
    }
    assert expected_paths == set(before["files"]) and len(expected_paths) == 1082
    for name, expected in before["files"].items():
        raw = regular_bytes(root / name)
        assert len(raw) == expected["bytes"] and digest(raw) == expected["sha256"], name
    for item in results:
        raw = regular_bytes(original_dir / item["log"])
        assert digest(raw) == item["log_sha256"], item["log"]
    assert timing["total"] == len(timing["tests"]) == 102
    assert timing["pass"] == expected_pass and timing["fail"] == expected_fail
    assert sum(item["status"] == "pass" for item in timing["tests"]) == expected_pass
    assert sum(item["status"] == "fail" for item in timing["tests"]) == expected_fail
    runs.append({
        "retained":retained,"head":before["head"],"tree":before["tree"],"source_count":1082,
        "snapshots_equal_and_actual_worktree_matches":True,
        "total":102,"pass":expected_pass,"fail":expected_fail,
        "stages":[{"name":item["name"],"exit_code":item["exit_code"]} for item in results],
    })

delta = git("diff", "--name-only", "d0d2b2dc7cac3e7e7bb853bc372d4afc9975f6bd", HEAD).decode().splitlines()
assert set(delta) == {
    "skills/adk-after-action-review/references/after-action-review.md",
    "templates/memory/after-action-review.md",
}
template = regular_bytes(ROOT / delta[1])
reference = regular_bytes(ROOT / delta[0])
old_template = git("show", f"{BASE}:templates/memory/after-action-review.md")
assert template == reference and len(template) == 819
assert template.split(b"task:\n",1)[1] == old_template.split(b"task:\n",1)[1]
print(json.dumps({
    "status":"pass","reviewer":"ai/independent-review",
    "observed_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    "base_commit":BASE,"head_commit":HEAD,"tree":TREE,
    "original_patch":{"bytes":len(patch),"sha256":digest(patch)},
    "frozen_input_state_sha256":digest(regular_bytes(C1 / "evidence/review-input-state.json")),
    "product_file_count":len(product_checks),"frozen_inventory_count":len(inventory_checks),
    "bundle_checks":bundle_checks,"counterexamples":counterexamples,"runs":runs,
    "final_delta":delta,"aar_original_task_body_preserved":True,
    "boundaries":[
        "Input-state paths denote the original pre-archive capture location.",
        "Historical lifecycle records may later advance; tested product bytes are separate.",
        "This script audits observed evidence bytes and never fabricates an execution or qualification.",
    ],
}, ensure_ascii=False, indent=2))
