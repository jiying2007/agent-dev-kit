#!/usr/bin/env python3
"""Read-only source audit; write synthetic Git fixtures and exports to scratch only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


REPO = Path(sys.argv[1]).resolve()
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "src"))
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import load_target_contract, render_asset, render_selection


def command(cwd: Path, args: list[str]) -> dict:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=15)
    return {"command": shlex.join(args), "returncode": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def checked(cwd: Path, args: list[str]) -> dict:
    result = command(cwd, args)
    assert result["returncode"] == 0, result
    return result


def commit(cwd: Path, message: str) -> None:
    checked(cwd, ["git", "add", "fixture.py"])
    checked(cwd, ["git", "-c", "user.name=ADK-Audit", "-c",
                  "user.email=audit@example.invalid", "commit", "-qm", message])


manifest = Manifest.load(REPO)
review = next(a for a in manifest.all_assets("skill") if a.name == "adk-code-review-loop")
rendered = render_asset(manifest, load_target_contract(manifest, "claude-code"), review)
reference = next(f for f in rendered
                 if f.destination.endswith("/references/review-evidence-template.md"))
reference_text = reference.content.decode()
match = re.search(r"```bash\n(.*?)\n```", reference_text, re.DOTALL)
assert match
snapshot = match.group(1).split("<project-lint-cmd>", 1)[0].strip()
snapshot_lines = snapshot.splitlines()
assert all(line.startswith("git ") for line in snapshot_lines), snapshot
OUTPUT.mkdir(parents=True, exist_ok=True)
(OUTPUT / "exported-review-evidence-template.md").write_text(reference_text)

cases = []
for mode in ("staged", "working-tree-unstaged", "whole-branch-clean", "working-tree-mixed"):
    with tempfile.TemporaryDirectory(prefix="adk-general-audit-") as temporary:
        work = Path(temporary)
        checked(work, ["git", "init", "-q"])
        fixture = work / "fixture.py"
        fixture.write_text("def cents_to_dollars(cents):\n    return cents / 100\n")
        commit(work, "baseline")
        baseline = checked(work, ["git", "rev-parse", "HEAD"])["stdout"].strip()
        marker = "WHOLE_BRANCH_REGRESSION" if mode == "whole-branch-clean" else "WORKTREE_REGRESSION"
        fixture.write_text("def cents_to_dollars(cents):\n    return cents / 1000  # " + marker + "\n")
        if mode == "staged":
            checked(work, ["git", "add", "fixture.py"])
            expected = ["git", "diff", "--cached"]
        elif mode == "whole-branch-clean":
            commit(work, "feature regression")
            expected = ["git", "diff", baseline + "...HEAD"]
        elif mode == "working-tree-mixed":
            fixture.write_text("def cents_to_dollars(cents):\n    return cents / 100.0  # STAGED_BENIGN_CHANGE\n")
            checked(work, ["git", "add", "fixture.py"])
            fixture.write_text("def cents_to_dollars(cents):\n    return cents / 1000  # " + marker + "\n")
            expected = ["git", "diff", "HEAD"]
        else:
            expected = ["git", "diff", "HEAD"]
        commands = [command(work, shlex.split(line)) for line in snapshot_lines]
        combined = "".join(item["stdout"] for item in commands)
        control = checked(work, expected)
        assert marker in control["stdout"], control
        assert all(item["returncode"] == 0 for item in commands), commands
        assert (marker in combined) == (mode == "staged"), (mode, combined)
        cases.append({"review_target": mode, "base": baseline, "commands": commands,
                      "expected_changed_content": marker,
                      "template_captured_expected_content": marker in combined,
                      "comparison_control": control})

dependencies = {
    "adk-context-engineering": "schemas/agent-handoff-v1.schema.json",
    "adk-context-compress-handoff": "templates/context/continuity-attestation.md",
}
profile_results = []
for profile in manifest.data["profiles"]:
    names = {a.name for a in manifest.resolve_profiles([profile]).skills}
    relevant = sorted(names.intersection(dependencies))
    if not relevant:
        continue
    for target in ("claude-code", "opencode"):
        bundle = render_selection(manifest, target, [profile])
        bodies = {f.name: f for f in bundle.files if f.destination.endswith("/SKILL.md")}
        missing = []
        for name in relevant:
            dependency = dependencies[name]
            assert dependency in bodies[name].content.decode()
            matching = [f.destination for f in bundle.files
                        if Path(f.destination).name == Path(dependency).name]
            assert not matching, matching
            missing.append({"skill": name, "body_destination": bodies[name].destination,
                            "reference": dependency, "source_exists": (REPO / dependency).is_file(),
                            "matching_exported_dependencies": matching})
        profile_results.append({"profile": profile, "target": target,
                                "file_count": len(bundle.files), "missing": missing})

exports = []
for target in ("claude-code", "opencode"):
    result = export_assets(manifest, target, OUTPUT / "core-exports", ["core"], clean=True)
    assert result["status"] == "pass"
    destination = Path(result["output"])
    checks = []
    for skill, dependency in dependencies.items():
        body = next(path for path in destination.rglob("SKILL.md") if path.parent.name == skill)
        assert dependency in body.read_text()
        candidates = [destination / dependency, body.parent / dependency]
        assert not any(path.exists() for path in candidates)
        checks.append({"skill": skill, "body": str(body),
                       "attempted_locations": [str(path) for path in candidates],
                       "missing_locations": [not path.exists() for path in candidates]})
    exports.append({"target": target, "output": str(destination), "checks": checks})

source_paths = ["skills/adk-code-review-loop/references/review-evidence-template.md",
                "skills/adk-context-engineering/SKILL.md",
                "skills/adk-context-compress-handoff/SKILL.md",
                "src/agent_dev_kit/compiler.py", "src/agent_dev_kit/targets.py",
                "tests/test_skill_content_contract.py"]
report = {
    "scope": "read-only audit of repository source; synthetic Git and exports in scratch",
    "repository": str(REPO),
    "head": checked(REPO, ["git", "rev-parse", "HEAD"])["stdout"].strip(),
    "source_sha256": {path: hashlib.sha256((REPO / path).read_bytes()).hexdigest()
                      for path in source_paths},
    "snapshot_commands_from_rendered_asset": snapshot,
    "review_cases": cases,
    "context_profile_checks": profile_results,
    "actual_export_checks": exports,
    "limits": ["No model execution; template evidence coverage is measured, not model review accuracy.",
               "No native host invocation; exported file contents and existence are measured.",
               "Project lint/test placeholders were not executed."]
}
result_path = OUTPUT / "results.json"
result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"report": str(result_path), "head": report["head"],
                  "review_cases": [{"target": c["review_target"],
                                    "captured": c["template_captured_expected_content"]} for c in cases],
                  "context_profile_target_cases": len(profile_results),
                  "actual_exports": [e["target"] for e in exports]}, ensure_ascii=False))
