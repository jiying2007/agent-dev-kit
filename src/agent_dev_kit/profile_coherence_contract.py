from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from .model import Manifest, ManifestError

_FORBIDDEN_CORE_AGENTS = {"driver-engineer", "bsp-analyst", "hardware-debugger"}
_FORBIDDEN_CORE_SKILLS = {
    "adk-driver-implementation",
    "adk-driver-bringup-checklist",
    "adk-register-map-design",
    "adk-bsp-analysis",
    "adk-bsp-porting-playbook",
    "adk-rtos-task-design",
    "adk-interrupt-dma-patterns",
    "adk-cmake-cross-build",
    "adk-unit-test-embedded",
    "adk-static-analysis-c-cpp",
    "adk-integration-hil-sil",
    "adk-production-field-readiness",
}


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _profiles(manifest: Manifest) -> Mapping[str, Mapping[str, Any]]:
    value = manifest.data.get("profiles")
    if not isinstance(value, dict):
        return {}
    return {str(name): raw for name, raw in value.items() if isinstance(raw, dict)}


def _parents(raw: Mapping[str, Any]) -> list[str]:
    value = raw.get("extends")
    if isinstance(value, str) and value:
        return [value]
    return _strings(value)


def _collect_direct(
    profiles: Mapping[str, Mapping[str, Any]],
    name: str,
    key: str,
    visiting: set[str] | None = None,
) -> list[str]:
    visiting = set() if visiting is None else set(visiting)
    if name in visiting:
        raise ValueError(f"profile inheritance cycle at {name}")
    raw = profiles.get(name)
    if raw is None:
        raise ValueError(f"unknown profile: {name}")
    visiting.add(name)
    result: list[str] = []
    for parent in _parents(raw):
        for item in _collect_direct(profiles, parent, key, visiting):
            if item not in result:
                result.append(item)
    for item in _strings(raw.get(key)):
        if item not in result:
            result.append(item)
    return result


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in values:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return sorted(duplicates)


def validate_profile_coherence(root: Path) -> dict[str, Any]:
    manifest = Manifest.load(root)
    profiles = _profiles(manifest)
    failures: list[str] = []
    warnings: list[str] = []

    default_profile = manifest.data.get("default_profile")
    if not isinstance(default_profile, str) or default_profile not in profiles:
        failures.append(f"default_profile is missing or unknown: {default_profile or '<empty>'}")

    agents = {
        str(item.get("name", "")): item
        for item in manifest.data.get("agents", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    skills = {
        str(item.get("name", ""))
        for item in manifest.data.get("skills", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }

    for name, raw in profiles.items():
        if not isinstance(raw.get("description"), str) or not raw["description"].strip():
            failures.append(f"profile {name} missing description")

        for key in ("include_agents", "include_skills"):
            direct = _strings(raw.get(key))
            for item in _duplicates(direct):
                failures.append(f"profile {name} duplicates {key}: {item}")
            inherited: set[str] = set()
            for parent in _parents(raw):
                if parent not in profiles:
                    failures.append(f"profile {name} extends unknown profile: {parent}")
                    continue
                try:
                    inherited.update(_collect_direct(profiles, parent, key))
                except ValueError as exc:
                    failures.append(str(exc))
            for item in sorted(set(direct) & inherited):
                failures.append(f"profile {name} redeclares inherited {key}: {item}")

        for agent in _strings(raw.get("include_agents")):
            if agent not in agents:
                failures.append(f"profile {name} references unknown include_agents: {agent}")
        for skill in _strings(raw.get("include_skills")):
            if skill not in skills:
                failures.append(f"profile {name} references unknown include_skills: {skill}")

        try:
            resolution = manifest.resolve_profiles([name])
        except ManifestError as exc:
            failures.append(str(exc))
            continue
        resolved_agents = {item.name for item in resolution.agents}
        resolved_skills = {item.name for item in resolution.skills}
        for agent in sorted(resolved_agents):
            record = agents.get(agent, {})
            for skill in _strings(record.get("default_skills")):
                if skill not in resolved_skills:
                    failures.append(
                        f"profile {name} includes agent '{agent}' but misses default skill '{skill}'"
                    )

        for conflict in _strings(raw.get("conflicts_with")):
            warnings.append(f"profile '{name}' conflicts with '{conflict}'")

    if "core" in profiles and "embedded-fullstack" in profiles:
        try:
            core = manifest.resolve_profiles(["core"])
            embedded = manifest.resolve_profiles(["embedded-fullstack"])
            core_agents = {item.name for item in core.agents}
            core_skills = {item.name for item in core.skills}
            embedded_agents = {item.name for item in embedded.agents}
            embedded_skills = {item.name for item in embedded.skills}
            for item in sorted(_FORBIDDEN_CORE_AGENTS):
                if item in core_agents:
                    failures.append(f"platform-neutral core contains embedded-only agent: {item}")
                if item not in embedded_agents:
                    failures.append(f"embedded-fullstack is missing embedded agent: {item}")
            for item in sorted(_FORBIDDEN_CORE_SKILLS):
                if item in core_skills:
                    failures.append(f"platform-neutral core contains embedded-only skill: {item}")
                if item not in embedded_skills:
                    failures.append(f"embedded-fullstack is missing embedded skill: {item}")
        except ManifestError as exc:
            failures.append(str(exc))

    return {
        "schema": "adk-profile-coherence/v2",
        "status": "fail" if failures else "pass",
        "source": "manifest.json",
        "default_profile": default_profile,
        "profiles": len(profiles),
        "failures": failures,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ADK profile coherence from manifest.json")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = validate_profile_coherence(Path(args.root).resolve())
    except (OSError, ValueError, ManifestError, json.JSONDecodeError) as exc:
        result = {
            "schema": "adk-profile-coherence/v2",
            "status": "fail",
            "source": "manifest.json",
            "failures": [str(exc)],
            "warnings": [],
        }
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        for warning in result.get("warnings", []):
            print(f"[WARN] {warning}")
        for failure in result.get("failures", []):
            print(f"[FAIL] {failure}", file=sys.stderr)
        if result["status"] == "pass":
            print("[PASS] profile coherence checks passed")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
