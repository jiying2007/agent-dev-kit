"""Replay the unchanged 60-task owner evaluation and capture its scoring conflict."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
OUT = Path(__file__).resolve().parent
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
OWNED = ("manifest.json", "skills/adk-systematic-debugging/SKILL.md", "tests/test_skill_trigger_matrix.py")
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit._matcher_kernel import _active_phrase_matches, _routing_ir, _routing_markers
from agent_dev_kit.campaign_model import load_campaign_contract
from agent_dev_kit.evaluation_runtime import run_deterministic
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


def main() -> None:
    phase = sys.argv[1]
    if phase not in ("red", "green"):
        raise SystemExit("phase must be red or green")
    manifest = Manifest.load(ROOT)
    _, tasks_path, tasks = load_campaign_contract(manifest, ROOT / "manifests/software_m5_eval_contract.json")
    task = next(item for item in tasks if item["id"] == "route-054")
    markers = _routing_markers(_routing_ir(manifest))
    scores = []
    for entry in manifest.data["routing"]["intents"]:
        if entry["intent"] in ("systematic_debugging", "embedded_debug_transport"):
            matches = _active_phrase_matches(task["prompt"], entry["intent_zh"], markers)
            scores.append({"intent": entry["intent"], "active_phrases": matches,
                           "total_specificity": sum(item[2] for item in matches),
                           "best_specificity": max((item[2] for item in matches), default=0)})
    if phase == "red":
        for path in OWNED:
            target = OUT / "before" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise SystemExit("refuse to replace the original RED snapshot")
            target.write_bytes((ROOT / path).read_bytes())
    fixture_relative = tasks_path.relative_to(ROOT).as_posix()
    baseline_fixture = subprocess.check_output([RTK, "bypass", "git", "show", "HEAD:" + fixture_relative], cwd=ROOT)
    result = {
        "phase": phase,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_version": manifest.version,
        "source_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in OWNED},
        "fixture_path": fixture_relative,
        "fixture_sha256": hashlib.sha256(tasks_path.read_bytes()).hexdigest(),
        "fixture_unchanged_from_head": baseline_fixture == tasks_path.read_bytes(),
        "route_054": {"task": task, "route": match_text(manifest, task["prompt"]), "scores": scores},
        "deterministic": run_deterministic(manifest, tasks),
        "boundary": "Source owner routing only; expected_safe is not an evaluated safety result",
    }
    (OUT / f"{phase}-probes.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "deterministic"},
                     ensure_ascii=False, indent=2))
    print(json.dumps({key: result["deterministic"][key] for key in ("status", "total", "passed")}, indent=2))


if __name__ == "__main__":
    main()
