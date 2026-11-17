"""Independent deterministic projection/compatibility probes; synthetic evidence only."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import types
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
BASE = "5f113b8f5ae6f83662d41d99d0907026f4e44c9d"
RTK = "/workspace/scratch/fe8de3b42084/verification-tools/rtk"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.task_evidence import import_task_evidence
from agent_dev_kit.trace_summary import diagnose_trace_summary
from test_task_evidence import synthetic_package, write_json

original = subprocess.run(
    [RTK, "proxy", "git", "show", f"{BASE}:src/agent_dev_kit/task_evidence.py"],
    cwd=ROOT, text=True, capture_output=True, check=True,
).stdout
baseline = types.ModuleType("agent_dev_kit._independent_baseline_task_evidence")
baseline.__package__ = "agent_dev_kit"
baseline.__file__ = str(ROOT / "src/agent_dev_kit/task_evidence.py")
sys.modules[baseline.__name__] = baseline
exec(compile(original, f"{BASE}:task_evidence.py", "exec"), baseline.__dict__)
manifest = Manifest.load(ROOT)
results = []


def persist(root, envelope, events, acceptance):
    for index, item in enumerate(events["events"], 1):
        item["seq"] = index
    envelope["events"] = write_json(root / "events.json", events)
    envelope["acceptance"] = write_json(root / "acceptance.json", acceptance)
    write_json(root / "observation.json", envelope)


def resolve_pointer(value, pointer):
    for part in pointer.lstrip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


with tempfile.TemporaryDirectory(prefix="independent-c1-") as directory:
    for scenario in (
        "ordinary",
        "unobserved-metrics",
        "unrun-acceptance",
        "process-failure-then-pass",
        "maximum-event-ledger",
    ):
        root = Path(directory) / scenario
        envelope, events, acceptance = synthetic_package(root)
        if scenario == "unobserved-metrics":
            events["coverage"]["model_calls"] = False
        elif scenario == "unrun-acceptance":
            acceptance["status"] = "not-run"
            acceptance["checks"][0]["status"] = "not-run"
        elif scenario == "process-failure-then-pass":
            first = copy.deepcopy(events["events"][-1])
            first.update(event_id="guardrail-first-failed", status="failed")
            events["events"].insert(-1, first)
        elif scenario == "maximum-event-ledger":
            statuses = ("succeeded", "failed", "blocked", "cancelled", "not-available")
            for index in range(4096 - len(events["events"])):
                events["events"].append({
                    "event_id": f"extra-tool-{index}", "kind": "tool-call",
                    "attempt_id": "attempt-1", "tool": "bulk-inspection",
                    "outcome": statuses[index % len(statuses)],
                })
        persist(root, envelope, events, acceptance)
        path = root / "observation.json"
        old = baseline.import_task_evidence(path, manifest)
        current = import_task_evidence(path, manifest)
        with_diagnostics = import_task_evidence(path, manifest, diagnostics=True)
        diagnostic = with_diagnostics.pop("diagnostics")
        trace = current["run_evidence"]["trace_summary"]
        assert old == current == with_diagnostics, scenario
        assert "diagnostics" not in current, scenario
        counts = {}
        for event in events["events"]:
            if event["kind"] == "tool-call":
                counts.setdefault(event["tool"], Counter())[event["outcome"]] += 1
        for tool, actual in diagnostic["facts"]["tool_outcome_counts"].items():
            assert sum(actual.values()) == sum(counts[tool].values()), scenario
            for outcome, count in actual.items():
                assert count == counts[tool][outcome], (scenario, tool, outcome)
        for finding in diagnostic["findings"]:
            assert resolve_pointer(trace, finding["location"]) == finding["fact"], scenario
        before = copy.deepcopy(trace)
        first = diagnose_trace_summary(trace)
        assert first == diagnose_trace_summary(trace), scenario
        first["facts"]["outcome"]["status"] = "independent-mutation"
        for finding in first["findings"]:
            if isinstance(finding["fact"], dict):
                finding["fact"]["independent-mutation"] = True
        assert trace == before, scenario
        results.append({
            "scenario": scenario, "status": "pass", "event_count": len(events["events"]),
            "default_equal_to_baseline": True, "diagnostics_removal_restores_default": True,
            "finding_locations_match_trace": True, "no_input_mutation": True,
            "recorded_attempts": diagnostic["facts"]["attempt_count"],
            "observed_tool_calls": diagnostic["facts"]["tool_calls"],
            "findings": [item["code"] for item in diagnostic["findings"]],
        })

    for nonterminal in ("queued", "staged", "deferred"):
        root = Path(directory) / nonterminal
        envelope, events, acceptance = synthetic_package(root)
        events["events"][2]["outcome"] = nonterminal
        persist(root, envelope, events, acceptance)
        outcomes = []
        for implementation, kwargs in (
            (baseline.import_task_evidence, {}),
            (import_task_evidence, {}),
            (import_task_evidence, {"diagnostics": True}),
        ):
            try:
                implementation(root / "observation.json", manifest, **kwargs)
            except ManifestError as error:
                outcomes.append({"rejected": True, "error": str(error)})
            else:
                raise AssertionError(f"{nonterminal} accepted as completed tool evidence")
        results.append({"scenario": nonterminal, "status": "pass", "outcomes": outcomes})

print(json.dumps({
    "scope": "deterministic synthetic mechanics, not host delivery or no-replay proof",
    "baseline": BASE,
    "baseline_module_sha256": hashlib.sha256(original.encode()).hexdigest(),
    "results": results,
}, ensure_ascii=False, indent=2))
