from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping

import yaml

from .model import Manifest


def _records(manifest: Manifest, section: str) -> list[Mapping[str, Any]]:
    value = manifest.data.get(section, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _named(manifest: Manifest, section: str) -> list[Mapping[str, Any]]:
    return sorted(
        _records(manifest, section),
        key=lambda item: (
            int(item.get("lifecycle_order", 999)),
            int(item.get("stage_order", 999)),
            str(item.get("name", "")),
        ),
    )


def _list_text(value: Any) -> str:
    if not isinstance(value, list):
        return "-"
    items = [str(item) for item in value if item not in (None, "")]
    return ", ".join(items) if items else "-"


def _skill_frontmatter(root: Path, record: Mapping[str, Any]) -> Mapping[str, Any]:
    path = root / str(record.get("path", ""))
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    value = yaml.safe_load(text[4:end])
    return value if isinstance(value, dict) else {}


def _agents(manifest: Manifest) -> list[str]:
    lines = ["## Agents", "", "| Name | Description | Path |", "|---|---|---|"]
    for item in _records(manifest, "agents"):
        name = str(item.get("name", ""))
        desc = str(item.get("description") or item.get("role") or "")
        path = str(item.get("path", ""))
        lines.append(f"| `{name}` | {desc} | `{path}` |")
    lines += ["", "## Agent Contract Matrix", "", "| Agent | Owns | Does Not Own | Handoff To | Default Skills | Quality Gate |", "|---|---|---|---|---|---|"]
    for item in _records(manifest, "agents"):
        lines.append(
            f"| `{item.get('name','')}` | {_list_text(item.get('owns'))} | {_list_text(item.get('does_not_own'))} | "
            f"{_list_text(item.get('handoff_to'))} | {_list_text(item.get('default_skills'))} | {item.get('quality_gate','')} |"
        )
    lines.append("")
    return lines


def _skills(manifest: Manifest, section: str, title: str) -> list[str]:
    lines = [f"## {title}", "", "| Order | Stage | Category | Activation | Pattern | Name | Description | First Trigger | Path |", "|---:|---:|---|---|---|---|---|---|---|"]
    for item in _named(manifest, section):
        frontmatter = _skill_frontmatter(manifest.root, item)
        triggers = frontmatter.get("triggers")
        trigger = str(triggers[0]) if isinstance(triggers, list) and triggers else ""
        lines.append(
            f"| {item.get('lifecycle_order','')} | {item.get('stage_order','')} | `{item.get('category','')}` | "
            f"{item.get('activation_mode','')} | {item.get('pattern','')} | `{item.get('name','')}` | "
            f"{frontmatter.get('description','')} | {trigger} | `{item.get('path','')}` |"
        )
    lines.append("")
    return lines


def _workflows(manifest: Manifest) -> list[str]:
    lines = ["## Workflows", "", "| Order | Type | Name | Description | Profiles | Primary Agent | Primary Skill | Path |", "|---:|---|---|---|---|---|---|---|"]
    for item in _named(manifest, "workflows"):
        lines.append(
            f"| {item.get('lifecycle_order','')} | `{item.get('workflow_type','')}` | `{item.get('name','')}` | "
            f"{item.get('description','')} | {_list_text(item.get('profiles'))} | `{item.get('primary_agent','')}` | "
            f"`{item.get('primary_skill','')}` | `{item.get('path','')}` |"
        )
    lines += ["", "## Workflow Matrix", "", "| Order | Type | Workflow | Profiles | Command Risk | Primary Agent | Primary Skill | Supporting Skills | Entry Conditions | Exit Evidence | Verification |", "|---:|---|---|---|---|---|---|---|---|---|---|"]
    for item in _named(manifest, "workflows"):
        lines.append(
            f"| {item.get('lifecycle_order','')} | `{item.get('workflow_type','')}` | `{item.get('name','')}` | "
            f"{_list_text(item.get('profiles'))} | {item.get('command_risk','')} | `{item.get('primary_agent','')}` | "
            f"`{item.get('primary_skill','')}` | {_list_text(item.get('supporting_skills'))} | "
            f"{_list_text(item.get('entry_conditions'))} | {_list_text(item.get('exit_evidence'))} | {_list_text(item.get('verification'))} |"
        )
    lines.append("")
    return lines


def _routing(manifest: Manifest) -> list[str]:
    routing = manifest.data.get("routing") if isinstance(manifest.data.get("routing"), dict) else {}
    intents = routing.get("intents") if isinstance(routing.get("intents"), list) else []
    intent_map = {str(item.get("intent", "")): item for item in intents if isinstance(item, dict)}
    lines = ["## Skill Routing Matrix", "", "| Scenario | Description | Availability | Profiles | Workflow | Primary | Supporting | Fallback | Mutually Exclusive | Positive Example | Negative Example |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for item in _records(manifest, "skill_routing_matrix"):
        intent = intent_map.get(str(item.get("routing_intent", "")), {})
        positive = item.get("positive_examples") if isinstance(item.get("positive_examples"), list) else []
        negative = item.get("negative_examples") if isinstance(item.get("negative_examples"), list) else []
        lines.append(
            f"| `{item.get('name','')}` | {item.get('description','')} | {intent.get('availability','profile-resolved')} | "
            f"{_list_text(item.get('profiles'))} | `{item.get('workflow','')}` | `{intent.get('primary_skill','')}` | "
            f"{_list_text(intent.get('supporting_skills'))} | {_list_text(intent.get('fallback_skills'))} | "
            f"{_list_text(intent.get('mutually_exclusive'))} | {positive[0] if positive else ''} | {negative[0] if negative else ''} |"
        )
    lines.append("")
    return lines


def _profiles(manifest: Manifest) -> list[str]:
    profiles = manifest.data.get("profiles") if isinstance(manifest.data.get("profiles"), dict) else {}
    lines = ["## Profiles", "", "| Name | Description | Optional | Extends |", "|---|---|---|---|"]
    for name, item in profiles.items():
        if not isinstance(item, dict):
            continue
        extends = item.get("extends")
        extends_text = _list_text(extends) if isinstance(extends, list) else str(extends or "-")
        optional = str(bool(item.get("optional", False))).lower()
        lines.append(f"| `{name}` | {item.get('description','')} | {optional} | {extends_text} |")
    lines.append("")
    return lines


def catalog_markdown(manifest: Manifest) -> str:
    lines = ["# Agent and Skill Catalog", "", "- source: manifest.json", ""]
    lines += _agents(manifest)
    lines += _skills(manifest, "skills", "Skills")
    lines += _skills(manifest, "optional_skills", "Optional Skills")
    lines += _workflows(manifest)
    lines += _routing(manifest)
    lines += _profiles(manifest)
    return "\n".join(lines).rstrip() + "\n"


def workflow_matrix_markdown(manifest: Manifest) -> str:
    workflow_lines = _workflows(manifest)
    matrix_index = workflow_lines.index("## Workflow Matrix")
    return "\n".join(["# Workflow Contract Matrix", "", "- source: manifest.json", ""] + workflow_lines[matrix_index:]).rstrip() + "\n"


def routing_matrix_markdown(manifest: Manifest) -> str:
    return "\n".join(["# Skill Routing Matrix", "", "- source: manifest.json:routing + skill_routing_matrix", ""] + _routing(manifest)[2:]).rstrip() + "\n"


def find_rows(manifest: Manifest, kind: str, keyword: str) -> list[str]:
    needle = keyword.casefold()
    rows = ["type\tname\tdescription\tpath"]
    sections = []
    if kind in {"all", "agent"}:
        sections.append(("agent", _records(manifest, "agents")))
    if kind in {"all", "skill"}:
        sections.append(("skill", _records(manifest, "skills")))
    if kind in {"all", "optional-skill"}:
        sections.append(("optional-skill", _records(manifest, "optional_skills")))
    if kind in {"all", "workflow"}:
        sections.append(("workflow", _records(manifest, "workflows")))
    for label, records in sections:
        for item in records:
            name = str(item.get("name", ""))
            path = str(item.get("path", ""))
            if label in {"skill", "optional-skill"}:
                desc = str(_skill_frontmatter(manifest.root, item).get("description", ""))
            else:
                desc = str(item.get("description") or item.get("role") or "")
            haystack = " ".join([name, desc, str(item.get("primary_agent", "")), str(item.get("primary_skill", ""))]).casefold()
            if needle in haystack:
                rows.append(f"{label}\t{name}\t{desc}\t{path}")
    if kind in {"all", "profile"}:
        profiles = manifest.data.get("profiles") if isinstance(manifest.data.get("profiles"), dict) else {}
        for name, item in profiles.items():
            if not isinstance(item, dict):
                continue
            desc = str(item.get("description", ""))
            if needle in f"{name} {desc}".casefold():
                rows.append(f"profile\t{name}\t{desc}\tmanifest.json")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate/search projections from canonical manifest.json")
    parser.add_argument("action", choices=("build", "find"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--out")
    parser.add_argument("--keyword")
    parser.add_argument("--type", default="all", choices=("all", "agent", "skill", "optional-skill", "workflow", "profile"))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    manifest = Manifest.load(root)
    if args.action == "build":
        output = Path(args.out).resolve() if args.out else root / "docs" / "agent-skill-catalog.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(catalog_markdown(manifest), encoding="utf-8")
        print(f"[OK] catalog generated: {output}")
        if args.out is None:
            (root / "docs" / "workflow-contract-matrix.md").write_text(workflow_matrix_markdown(manifest), encoding="utf-8")
            routing_path = root / "docs" / "reference" / "skill-routing-matrix.md"
            routing_path.parent.mkdir(parents=True, exist_ok=True)
            routing_path.write_text(routing_matrix_markdown(manifest), encoding="utf-8")
        return 0
    if not args.keyword:
        parser.error("--keyword is required for find")
    print("\n".join(find_rows(manifest, args.type, args.keyword)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
