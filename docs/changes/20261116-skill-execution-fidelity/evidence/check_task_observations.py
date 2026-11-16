"""Local synthetic consistency counterexamples. No candidate/model is executed."""
import json
from pathlib import Path

from test_task_trials import synthetic_task_trials
from test_task_evidence import MANIFEST, write_json
from agent_dev_kit.model import sha256_bytes
from agent_dev_kit.task_trials import compare_task_trials

ROOT = Path(__file__).resolve().parent


def mutate(root, data, change):
    for trial in data["trials"]:
        for side in ("baseline", "candidate"):
            for reference in trial[side]:
                path = root / reference["path"]
                envelope = json.loads(path.read_text())
                change(side, path.parent, envelope)
                write_json(path, envelope)
                reference["sha256"] = sha256_bytes(path.read_bytes())
    write_json(root / "task-trials.json", data)


def preregistration_case():
    root = ROOT / "before-registration"
    data = synthetic_task_trials(root)

    def change(side, directory, envelope):
        envelope["run"]["started_at"] = "2026-09-24T09:00:00Z"

    mutate(root, data, change)
    report = compare_task_trials(root / "task-trials.json", MANIFEST)
    return {"case": "run-starts-before-registration", "started_at": "2026-09-24T09:00:00Z",
            "registered_at": data["plan"]["registered_at"], "window": data["plan"]["window"],
            "actual_verdict": report["verdict"], "actual_reason": report["comparison"]["reason"],
            "expected": "reject explicit start-before-registration or fixed-window contradiction"}


def changed_grader_case():
    root = ROOT / "changed-grader-contract"
    data = synthetic_task_trials(root)

    def change(side, directory, envelope):
        if side != "candidate":
            return
        acceptance = json.loads((directory / envelope["acceptance"]["path"]).read_text())
        new_check = write_json(directory / "different-check.json", {
            "synthetic": True, "grading_contract": "accept-any-result", "status": "passed"})
        acceptance["checks"] = [{"name": "different-easier-check", "status": "passed", "evidence": new_check}]
        envelope["acceptance"] = write_json(directory / "acceptance.json", acceptance)

    mutate(root, data, change)
    report = compare_task_trials(root / "task-trials.json", MANIFEST)
    return {"case": "same-grader-id-different-contract", "grader_id": data["grader_id"],
            "actual_verdict": report["verdict"], "actual_reason": report["comparison"]["reason"],
            "actual_control_grader_ref": data["plan"]["controls"]["grader_ref"],
            "expected": "bind task-specific grader/check contract before declaring controlled comparison",
            "qualification": "missing frozen control; report remains explicitly caller-observed/test-only"}


if __name__ == "__main__":
    results = [preregistration_case(), changed_grader_case()]
    text = json.dumps({"synthetic": True, "results": results}, indent=2)
    print(text)
    (ROOT / "observation-consistency-results.json").write_text(text + "\n")
