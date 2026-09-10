from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from .model import Manifest, ManifestError, ensure_within

_Kebab = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PLACEHOLDER = re.compile(r"TODO|TBD|FIXME|待补充|描述待定|示例|占位", re.IGNORECASE)
_WORKFLOW_COMMAND = re.compile(r"^rtk\s+bash\s+((?:scripts|tests)/\S+)")
_AGENT_HEADINGS = (
    "## 角色定位",
    "## 适用输入",
    "## 核心决策规则",
    "## 执行流程",
    "## 必跑验证",
    "## 阻塞与升级",
    "## 输出契约",
)
_SKILL_HEADINGS = ("## Goal", "## Workflow", "## Quality Gate")
_SKILL_KEYS = ("name", "description", "triggers", "non_triggers", "inputs", "outputs", "constraints")


def _records(data: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _frontmatter(path: Path) -> Mapping[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    value = yaml.safe_load(text[4:end])
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be a mapping")
    return value


def _validate_description(label: str, value: Any, failures: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{label} description is empty")
        return
    if len(value.strip()) < 8:
        failures.append(f"{label} description too short for discovery")
    if _PLACEHOLDER.search(value):
        failures.append(f"{label} description contains placeholder text")


def _validate_agent_files(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    disk = {path.name for path in (manifest.root / "agents").iterdir() if path.is_dir()}
    records = {str(item.get("name", "")): item for item in _records(manifest.data, "agents")}
    if disk != set(records):
        missing = sorted(disk - set(records))
        extra = sorted(set(records) - disk)
        if missing:
            failures.append("manifest missing agents: " + ", ".join(missing))
        if extra:
            failures.append("manifest agents missing on disk: " + ", ".join(extra))
    for name, record in records.items():
        if not _Kebab.fullmatch(name):
            failures.append(f"invalid agent name: {name}")
            continue
        raw_path = record.get("path")
        if not isinstance(raw_path, str):
            continue
        path = manifest.root / raw_path
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for heading in _AGENT_HEADINGS:
            if heading not in text.splitlines():
                failures.append(f"agent '{name}' missing heading '{heading}'")
        if strict:
            _validate_description(f"agent '{name}'", record.get("description"), failures)
            for key in ("owns", "does_not_own", "handoff_to", "default_skills"):
                if not _strings(record.get(key)):
                    failures.append(f"agent '{name}' manifest list '{key}' is empty")


def _validate_skill_files(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    core_names = {str(item.get("name", "")) for item in _records(manifest.data, "skills")}
    optional_names = {str(item.get("name", "")) for item in _records(manifest.data, "optional_skills")}
    if core_names & optional_names:
        failures.append("optional skills duplicate core skills: " + ", ".join(sorted(core_names & optional_names)))

    descriptions: dict[str, str] = {}
    for section, label in (("skills", "skill"), ("optional_skills", "optional skill")):
        for record in _records(manifest.data, section):
            name = str(record.get("name", ""))
            if not _Kebab.fullmatch(name):
                failures.append(f"invalid {label} name: {name}")
                continue
            raw_path = record.get("path")
            if not isinstance(raw_path, str):
                continue
            path = manifest.root / raw_path
            if not path.is_file():
                continue
            try:
                frontmatter = _frontmatter(path)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                failures.append(f"{label} '{name}' invalid frontmatter: {exc}")
                continue
            for key in _SKILL_KEYS:
                if key not in frontmatter:
                    failures.append(f"{label} '{name}' frontmatter key '{key}' missing")
            if frontmatter.get("name") != name:
                failures.append(f"{label} '{name}' frontmatter name mismatch: {frontmatter.get('name')}")
            for key in ("triggers", "non_triggers", "inputs", "outputs", "constraints"):
                if not _strings(frontmatter.get(key)):
                    failures.append(f"{label} '{name}' frontmatter list '{key}' is empty")
            text_lines = path.read_text(encoding="utf-8").splitlines()
            for heading in _SKILL_HEADINGS:
                if heading not in text_lines:
                    failures.append(f"{label} '{name}' missing heading '{heading}'")
            if strict:
                description = frontmatter.get("description")
                _validate_description(f"{label} '{name}'", description, failures)
                if isinstance(description, str):
                    previous = descriptions.get(description)
                    if previous is not None:
                        failures.append(f"duplicate skill description in {previous} and {name}")
                    descriptions[description] = name
                if len(text_lines) > 140:
                    failures.append(f"skill entry exceeds 140 lines: {raw_path} ({len(text_lines)})")


def _validate_quality_tiers(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    tiers = manifest.data.get("quality_tiers")
    if not isinstance(tiers, dict) or not tiers:
        failures.append("manifest quality_tiers section is empty")
        return
    names = set(tiers)
    for name, raw in tiers.items():
        if not _Kebab.fullmatch(str(name)):
            failures.append(f"invalid quality tier name: {name}")
        if strict and (not isinstance(raw, dict) or not isinstance(raw.get("description"), str) or not raw["description"]):
            failures.append(f"quality tier '{name}' missing description in strict mode")
    for section, label in (("agents", "agent"), ("skills", "skill"), ("optional_skills", "optional skill")):
        for record in _records(manifest.data, section):
            tier = record.get("quality_tier")
            name = str(record.get("name", ""))
            if strict and not isinstance(tier, str):
                failures.append(f"{label} '{name}' missing quality_tier in strict mode")
            elif isinstance(tier, str) and tier not in names:
                failures.append(f"{label} '{name}' has unknown quality_tier '{tier}'")


def _validate_reference_and_targets(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    references = manifest.data.get("reference_sources")
    if not isinstance(references, dict) or not references:
        failures.append("manifest has no reference_sources")
    else:
        for name, raw in references.items():
            if not isinstance(raw, dict):
                failures.append(f"reference source '{name}' must be an object")
                continue
            for key in ("display_name", "source_type", "boundary", "runtime_enablement", "governance_manifest"):
                if key not in raw:
                    failures.append(f"reference source '{name}' missing key: {key}")
            if raw.get("runtime_enablement") is not False:
                failures.append(f"reference source '{name}' must not enable runtime behavior")
            governance = raw.get("governance_manifest")
            if isinstance(governance, str) and not (manifest.root / governance).is_file():
                failures.append(f"reference source '{name}' governance manifest missing: {governance}")

    direct = manifest.direct_targets()
    for name, raw in direct.items():
        for key in ("display_name", "default_root", "agents_dir", "skills_dir"):
            if not raw.get(key):
                failures.append(f"tool target '{name}' missing key: {key}")
        if strict and not _strings(raw.get("detect")):
            failures.append(f"tool target '{name}' detect list is empty in strict mode")

    external = manifest.external_targets()
    codex = external.get("codex")
    if not isinstance(codex, dict):
        failures.append("Codex must be declared as an external handoff target")
    else:
        if codex.get("handoff_mode") != "source-to-live":
            failures.append("Codex external handoff must use source-to-live mode")
        if codex.get("direct_tool_target") is not False:
            failures.append("Codex external handoff must not be a direct tool target")
        chain = codex.get("handoff_chain")
        if not isinstance(chain, str) or "~/codex" not in chain or "~/.codex" not in chain:
            failures.append("Codex external handoff must document ~/codex -> ~/.codex")
        guards = set(_strings(codex.get("must_not")))
        for required in ("direct-write-live-home", "direct-convert-target", "implicit-tool-target"):
            if required not in guards:
                failures.append(f"Codex external handoff missing must_not guard: {required}")


def _validate_context_layers(manifest: Manifest, failures: list[str]) -> None:
    for key in ("context_layers", "embedded_context_layers"):
        for ref in _strings(manifest.data.get(key)):
            if ref.startswith(("skills/", "docs/", "knowledge/", "rules/", "templates/", "workflows/")):
                try:
                    path = ensure_within(manifest.root / ref, manifest.root, "context path")
                except ManifestError as exc:
                    failures.append(str(exc))
                    continue
                if not path.exists():
                    failures.append(f"manifest references missing path: {ref}")


def _validate_workflows(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    if not strict:
        return
    agents = {str(item.get("name", "")) for item in _records(manifest.data, "agents")}
    skills = {str(item.get("name", "")) for item in _records(manifest.data, "skills")}
    skills.update(str(item.get("name", "")) for item in _records(manifest.data, "optional_skills"))
    profiles = manifest.data.get("profiles") if isinstance(manifest.data.get("profiles"), dict) else {}
    for workflow in _records(manifest.data, "workflows"):
        name = str(workflow.get("name", ""))
        if not _Kebab.fullmatch(name):
            failures.append(f"invalid workflow name: {name}")
            continue
        path = workflow.get("path")
        if path != f"workflows/{name}/WORKFLOW.md":
            failures.append(f"workflow '{name}' path must be workflows/{name}/WORKFLOW.md")
        primary_agent = workflow.get("primary_agent")
        primary_skill = workflow.get("primary_skill")
        if primary_agent not in agents:
            failures.append(f"workflow '{name}' primary_agent unknown: {primary_agent}")
        if primary_skill not in skills:
            failures.append(f"workflow '{name}' primary_skill unknown: {primary_skill}")
        if workflow.get("command_risk") not in {"low", "medium", "high"}:
            failures.append(f"workflow '{name}' command_risk must be low|medium|high")
        for key in ("profiles", "triggers", "agents", "skills", "commands", "verification", "supporting_skills"):
            if not _strings(workflow.get(key)):
                failures.append(f"workflow '{name}' manifest list '{key}' is empty")
        for profile in _strings(workflow.get("profiles")):
            if profile not in profiles:
                failures.append(f"workflow '{name}' references unknown profile '{profile}'")
        for command in _strings(workflow.get("commands")) + _strings(workflow.get("verification")):
            match = _WORKFLOW_COMMAND.match(command)
            if match is None:
                failures.append(f"workflow '{name}' command must use a checked rtk bash scripts|tests path: {command}")
                continue
            if not (manifest.root / match.group(1)).is_file():
                failures.append(f"workflow '{name}' command references missing script: {match.group(1)}")


def _validate_mcp_and_change_sets(manifest: Manifest, strict: bool, failures: list[str]) -> None:
    if not strict:
        return
    for server in _records(manifest.data, "mcp_servers"):
        name = str(server.get("name", ""))
        if not server.get("command"):
            failures.append(f"MCP server '{name}' missing command")
        if server.get("transport") not in {"stdio", "http", "sse"}:
            failures.append(f"MCP server '{name}' has invalid transport '{server.get('transport')}'")
        if server.get("risk_level") not in {"low", "medium", "high"}:
            failures.append(f"MCP server '{name}' must declare risk_level low|medium|high")
    change_sets = _records(manifest.data, "change_sets")
    if not change_sets:
        failures.append("manifest change_sets section is empty")
    for item in change_sets:
        name = str(item.get("name", ""))
        for key in ("root", "archive_root"):
            value = item.get(key)
            if not isinstance(value, str) or not (manifest.root / value).is_dir():
                failures.append(f"change set '{name}' {key} missing: {value}")
        if not _strings(item.get("required_files")):
            failures.append(f"change set '{name}' required_files is empty")


def validate_assets(root: Path, *, strict: bool, quick: bool) -> dict[str, Any]:
    manifest = Manifest.load(root)
    failures = manifest.validate(strict=strict and not quick)
    data = manifest.data
    _validate_quality_tiers(manifest, strict, failures)
    _validate_reference_and_targets(manifest, strict, failures)
    _validate_agent_files(manifest, strict, failures)
    _validate_skill_files(manifest, strict, failures)
    _validate_context_layers(manifest, failures)
    _validate_workflows(manifest, strict and not quick, failures)
    _validate_mcp_and_change_sets(manifest, strict and not quick, failures)
    if not quick:
        profiles = data.get("profiles")
        if isinstance(profiles, dict):
            for name in profiles:
                try:
                    resolution = manifest.resolve_profiles([str(name)])
                except ManifestError as exc:
                    failures.append(str(exc))
                    continue
                if not resolution.agents:
                    failures.append(f"profile '{name}' resolves to zero agents")
                if not resolution.skills:
                    failures.append(f"profile '{name}' resolves to zero skills")
    result = {
        "schema": "adk-asset-validation/v2",
        "status": "fail" if failures else "pass",
        "strict": strict,
        "quick": quick,
        "failures": failures,
        "counts": {
            "agents": len(_records(data, "agents")),
            "skills": len(_records(data, "skills")),
            "optional_skills": len(_records(data, "optional_skills")),
            "profiles": len(data.get("profiles", {})) if isinstance(data.get("profiles"), dict) else 0,
            "workflows": len(_records(data, "workflows")),
            "change_sets": len(_records(data, "change_sets")),
        },
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ADK assets against canonical manifest.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_assets(Path(args.root).resolve(), strict=args.strict, quick=args.quick)
    except (OSError, ManifestError, ValueError, json.JSONDecodeError) as exc:
        result = {"schema": "adk-asset-validation/v2", "status": "fail", "failures": [str(exc)]}
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["status"] == "pass":
        print(f"Validation passed. strict={int(args.strict)} quick={int(args.quick)}")
    else:
        for failure in result.get("failures", []):
            print(f"[FAIL] {failure}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
