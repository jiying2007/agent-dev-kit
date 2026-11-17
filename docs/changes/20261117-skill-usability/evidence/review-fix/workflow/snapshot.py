"""Record the final correction, unchanged authority helpers, and original ratchets."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.model import Manifest
from agent_dev_kit.profile_context_footprint import enforce_profile_ratchet


def git(*args: str) -> bytes:
    return subprocess.check_output([RTK, "bypass", "git", *args], cwd=ROOT)


def functions(source: str) -> dict[str, str | None]:
    return {node.name: ast.get_source_segment(source, node) for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)}


def main() -> None:
    manifest = Manifest.load(ROOT)
    kernel_path = "src/agent_dev_kit/_matcher_kernel.py"
    baseline_kernel = git("show", "HEAD:" + kernel_path)
    before = functions(baseline_kernel.decode())
    after = functions((ROOT / kernel_path).read_text())
    unchanged = {name: before[name] == after[name] for name in (
        "_phrase_matches", "_all_phrase_matches", "_is_locally_negated", "_active_phrase_matches",
        "_skill_identity_declined", "_classify_task_mode", "_matching_negated_intent",
        "_strictest_permission", "_resolved_policy",
    )}
    ratchet_path = "manifests/profile_context_ratchets.json"
    ratchets = json.loads((ROOT / ratchet_path).read_text())
    profiles = [enforce_profile_ratchet(manifest, name) for name in ratchets["profiles"]]
    previous = {row["path"]: row for row in json.loads(
        (OUT.parent / "t3b-source-delta.json").read_text())["files"]}
    paths = (kernel_path, "skills/adk-production-field-readiness/SKILL.md", "tests/test_skill_trigger_matrix.py")
    files = []
    for path in paths:
        data = (ROOT / path).read_bytes()
        prior_size = len(baseline_kernel) if path == kernel_path else previous[path]["current_bytes"]
        files.append({"path": path, "previous_t3b_bytes": prior_size, "current_bytes": len(data),
                      "delta": len(data) - prior_size, "sha256": hashlib.sha256(data).hexdigest()})
    result = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "head": git("rev-parse", "HEAD").decode().strip(),
              "manifest_version": manifest.data.get("version"),
              "files": files, "unchanged_global_helpers": unchanged,
              "ratchet_source_unchanged": git("show", "HEAD:" + ratchet_path) == (ROOT / ratchet_path).read_bytes(),
              "profiles": profiles,
              "authority": "Only implicit-context eligibility changed; no runtime, device, commit or publish action"}
    (OUT / "snapshot.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (OUT / "cumulative-owned.diff").write_bytes(git("diff", "--", *paths))
    summary = {**result, "profiles": [{"profile": row["profile"], "status": row["status"],
                "full_source_bytes": row["actual"]["potential_full_source_bytes"],
                "full_source_limit": row["ratchet"]["potential_full_source_bytes"]} for row in profiles]}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    assert all(unchanged.values()) and result["ratchet_source_unchanged"]
    assert all(row["status"] == "pass" for row in profiles)


if __name__ == "__main__":
    main()
