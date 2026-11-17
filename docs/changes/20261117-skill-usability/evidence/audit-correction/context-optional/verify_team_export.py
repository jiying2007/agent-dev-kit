"""Verify full assigned-scope export through the appropriate existing profile."""
import json
from pathlib import Path

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest

root = Path("/workspace/scratch/fe8de3b42084/adk-skill-usability")
audit = Path("/workspace/scratch/fe8de3b42084/skill-usability-audit/context-optional")
items = json.loads((audit.parent / "groups.json").read_text())["groups"]["context_optional"]
expected = {item["name"] for item in items}
optional = [item["name"] for item in items if item["path"].startswith("optional-skills/")]
manifest = Manifest.load(root)
results = []
for target in ("claude-code", "opencode"):
    result = export_assets(manifest, target, audit / "fixtures/team-exports", ["team-core"], optional, "skill")
    output = Path(result["output"])
    names = {path.parent.name for path in output.rglob("SKILL.md")}
    missing = sorted(expected - names)
    if missing:
        raise RuntimeError(missing)
    results.append({"target": target, "profile": "team-core", "output": str(output),
                    "covered": len(expected), "missing": missing,
                    "source_helpers_present": (output / "scripts/devkit.sh").exists()})
destination = audit / "export-coverage-control.json"
destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(results, ensure_ascii=False))
