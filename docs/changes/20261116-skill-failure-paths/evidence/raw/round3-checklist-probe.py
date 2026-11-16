"""Inspect current shipped blank completion checklist; exports only to temp dirs."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/workspace/scratch/fe5385ca063a/agent-dev-kit")
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest


def rows(text: str) -> list[dict[str, str]]:
    section = text.split("## Completion Review", 1)[1].split("## Rework Decision", 1)[0]
    data = []
    for line in section.splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) == 3 and cells[0] not in ("Check", "---"):
                data.append(dict(zip(("check", "result", "evidence"), cells)))
    return data


def main() -> None:
    relative = Path("skills/adk-parallel-agent-governance/references/subagent-review-checklist.md")
    raw = (ROOT / relative).read_bytes()
    source_rows = rows(raw.decode())
    report = {
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(relative),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_rows": source_rows,
        "source_blank_evidence_pass_rows": sum(row["result"] == "pass" and not row["evidence"] for row in source_rows),
        "exports": [],
        "boundary": "Template states and export identity only; does not measure an agent or claim a runtime gate was bypassed.",
    }
    manifest = Manifest.load(ROOT)
    with tempfile.TemporaryDirectory(prefix="round3-checklist-") as directory:
        for runtime in ("claude-code", "opencode"):
            exported = export_assets(manifest, runtime, Path(directory), ["core"])
            consumer = Path(exported["output"])
            skill = next(path for path in consumer.rglob("SKILL.md")
                         if path.parent.name == "adk-parallel-agent-governance")
            package = skill.parent / "references/parallel-worktree-task-package.md"
            checklist = skill.parent / "references/subagent-review-checklist.md"
            delivered = checklist.read_bytes()
            emitted_rows = rows(delivered.decode())
            assert "subagent-review-checklist.md" in package.read_text()
            assert delivered == raw
            assert len(emitted_rows) == 5
            report["exports"].append({
                "target": runtime,
                "skill_entry": str(skill.relative_to(consumer)),
                "default_package_references_checklist": True,
                "checklist_source_identical": True,
                "blank_evidence_pass_rows": sum(row["result"] == "pass" and not row["evidence"] for row in emitted_rows),
            })
    target = Path(__file__).with_suffix(".json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
