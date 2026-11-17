"""Independent C2 contract probe; frozen inputs never import implementation tests.

Usage: python -B replay_frozen_probe.py /absolute/candidate/repository
Exit 0 means the four acceptance controls hold; exit 1 preserves a real failure.
The verifier below is synthetic and does not certify any real host permission.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO / "src"))

from agent_dev_kit.execution_policy import ExecutionPolicyError, evaluate, reduce_events


def managed_mode_verifier(intake: dict, authority_policy: dict) -> bool:
    """Original baseline test-only verifier, not a production authority registry."""
    return (
        authority_policy["verification_backend"] == "managed-authority-registry"
        and intake["authority_id"] == "routing-authority"
        and intake["request_sha256"] == "d" * 64
        and intake["routing_decision_sha256"] == "e" * 64
    )


def main() -> int:
    inputs = json.loads(Path(__file__).with_name("frozen-inputs.json").read_text())
    expected = {
        "latest_implementation": (False, False),
        "replayed_older_readonly_new_event_id": (True, None),
        "replay_without_trusted_verifier": (True, None),
        "fresh_readonly_after_implementation": (False, True),
    }
    observations = []
    for case in inputs["cases"]:
        reject_expected, gate_expected = expected[case["case"]]
        row = {"case": case["case"], "managed_verifier": case["managed_verifier"]}
        try:
            state = reduce_events(case["events"])
            decision = evaluate(
                state,
                inputs["policy"],
                gate_event=inputs["gate_event"],
                mode_authority_verifier=managed_mode_verifier if case["managed_verifier"] else None,
                as_of=datetime.fromisoformat(inputs["as_of"]),
            )
            row.update(
                rejected=False,
                intake_revision=state["goal"]["intake_revision"],
                task_mode=decision["task_mode"],
                effective_artifact_mode=decision["effective_artifact_mode"],
                missing_artifacts=decision["missing_artifacts"],
                gate_allowed=decision["gate_allowed"],
                completion_allowed=decision["completion_allowed"],
                expectation_met=not reject_expected and decision["gate_allowed"] is gate_expected,
            )
        except ExecutionPolicyError as exc:
            row.update(rejected=True, error=str(exc), expectation_met=reject_expected)
        observations.append(row)
    result = {
        "baseline_sha": inputs["baseline_sha"],
        "verifier_scope": inputs["verifier_scope"],
        "cases": observations,
        "all_expectations_met": all(row["expectation_met"] for row in observations),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["all_expectations_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
