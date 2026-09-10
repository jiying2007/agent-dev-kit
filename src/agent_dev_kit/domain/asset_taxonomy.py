from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from agent_dev_kit.domain.manifest import load_canonical_manifest


SKILL_CATEGORIES = frozenset(
    {
        "routing",
        "intake",
        "planning",
        "design",
        "implementation",
        "debugging",
        "verification",
        "review_quality",
        "release_closure",
        "governance",
    }
)
SKILL_PATTERNS = frozenset(
    {"tool-wrapper", "generator", "reviewer", "inversion", "pipeline", "playbook", "governance"}
)
ACTIVATION_MODES = frozenset({"primary", "supporting", "fallback", "governance"})
WORKFLOW_TYPES = frozenset(
    {
        "feature-delivery",
        "bugfix-delivery",
        "refactor-delivery",
        "embedded-bringup-delivery",
        "diagnostic-delivery",
        "release-hardening",
        "incident-response",
        "research-intake",
        "skill-curation-delivery",
        "archive-memory-governance",
        "adk-governance",
    }
)
_SNAKE_CASE = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True)
class SkillRef:
    name: str
    section: str
    lifecycle_order: int
    stage_order: int
    activation_mode: str

    @property
    def sort_key(self) -> int:
        return self.lifecycle_order * 1000 + self.stage_order

    @property
    def optional(self) -> bool:
        return self.section == "optional_skills"


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _list(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    if nonempty and not value:
        raise ValueError(f"{label} must not be empty")
    return value


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def _named_items(manifest: dict[str, Any], section: str) -> list[dict[str, Any]]:
    values = _list(manifest.get(section), section)
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(values):
        item = _mapping(raw, f"{section}[{index}]")
        name = _string(item.get("name"), f"{section}[{index}].name")
        if name in seen:
            raise ValueError(f"{section} duplicate name: {name}")
        seen.add(name)
        result.append(item)
    return result


def _string_list(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    values = _list(value, label, nonempty=nonempty)
    result: list[str] = []
    for index, item in enumerate(values):
        result.append(_string(item, f"{label}[{index}]"))
    return result


def _skill_index(manifest: dict[str, Any]) -> dict[str, SkillRef]:
    result: dict[str, SkillRef] = {}
    for section in ("skills", "optional_skills"):
        semantic_keys: dict[int, str] = {}
        for item in _named_items(manifest, section):
            name = item["name"]
            category = _string(item.get("category"), f"{section}.{name}.category")
            if category not in SKILL_CATEGORIES:
                raise ValueError(f"{section} '{name}' has invalid category: {category}")
            lifecycle = _integer(item.get("lifecycle_order"), f"{section}.{name}.lifecycle_order")
            stage = _integer(item.get("stage_order"), f"{section}.{name}.stage_order")
            activation = _string(item.get("activation_mode"), f"{section}.{name}.activation_mode")
            if activation not in ACTIVATION_MODES:
                raise ValueError(f"{section} '{name}' has invalid activation_mode: {activation}")
            pattern = _string(item.get("pattern"), f"{section}.{name}.pattern")
            if pattern not in SKILL_PATTERNS:
                raise ValueError(f"{section} '{name}' has invalid pattern: {pattern}")
            ref = SkillRef(name, section, lifecycle, stage, activation)
            if ref.sort_key in semantic_keys:
                raise ValueError(
                    f"{section} duplicate semantic sort key {ref.sort_key}: "
                    f"'{semantic_keys[ref.sort_key]}' and '{name}'"
                )
            semantic_keys[ref.sort_key] = name
            if name in result:
                raise ValueError(f"skill name appears in multiple sections: {name}")
            result[name] = ref
    return result


def _require_primary(skill_index: dict[str, SkillRef], context: str, name: str, availability: Any) -> None:
    ref = skill_index.get(name)
    if ref is None:
        raise ValueError(f"{context} primary skill unknown: {name}")
    if ref.activation_mode != "primary":
        raise ValueError(
            f"{context} primary skill '{name}' activation_mode must be primary, got: {ref.activation_mode}"
        )
    if ref.optional and availability != "optional-skill-required":
        raise ValueError(
            f"{context} primary optional skill '{name}' requires availability: optional-skill-required"
        )


def _verify_skill_dependencies(manifest: dict[str, Any], skills: dict[str, SkillRef]) -> None:
    for section in ("skills", "optional_skills"):
        for item in _named_items(manifest, section):
            name = item["name"]
            ref = skills[name]
            for dependency in _string_list(item.get("depends_on", []), f"{section}.{name}.depends_on"):
                dependency_ref = skills.get(dependency)
                if dependency_ref is None:
                    raise ValueError(f"{section} '{name}' depends_on unknown skill: {dependency}")
                if dependency_ref.sort_key > ref.sort_key:
                    raise ValueError(
                        f"{section} '{name}' depends_on later skill '{dependency}' "
                        f"({dependency_ref.sort_key} > {ref.sort_key})"
                    )


def _verify_profiles(manifest: dict[str, Any], skills: dict[str, SkillRef]) -> set[str]:
    profiles = _mapping(manifest.get("profiles"), "profiles")
    for profile_name, raw in profiles.items():
        _string(profile_name, "profile name")
        profile = _mapping(raw, f"profiles.{profile_name}")
        previous = -1
        previous_skill = ""
        for skill in _string_list(profile.get("include_skills", []), f"profiles.{profile_name}.include_skills"):
            ref = skills.get(skill)
            if ref is None:
                raise ValueError(f"profile '{profile_name}' references unknown skill: {skill}")
            if ref.sort_key < previous:
                raise ValueError(
                    f"profile '{profile_name}' include_skills order drift: "
                    f"'{previous_skill}'({previous}) before '{skill}'({ref.sort_key})"
                )
            previous = ref.sort_key
            previous_skill = skill
    return set(profiles)


def _verify_workflows(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in _named_items(manifest, "workflows"):
        name = item["name"]
        names.add(name)
        workflow_type = _string(item.get("workflow_type"), f"workflows.{name}.workflow_type")
        if workflow_type not in WORKFLOW_TYPES:
            raise ValueError(f"workflow '{name}' has invalid workflow_type: {workflow_type}")
        _integer(item.get("lifecycle_order"), f"workflows.{name}.lifecycle_order")
        _string_list(item.get("entry_conditions"), f"workflows.{name}.entry_conditions", nonempty=True)
        _string_list(item.get("exit_evidence"), f"workflows.{name}.exit_evidence", nonempty=True)
    return names


def _verify_skill_refs(skills: dict[str, SkillRef], values: Iterable[str], context: str) -> None:
    for value in values:
        if value not in skills:
            raise ValueError(f"{context} unknown skill: {value}")


def _routing_intents(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routing = _mapping(manifest.get("routing"), "routing")
    intents = _list(routing.get("intents"), "routing.intents", nonempty=True)
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(intents):
        item = _mapping(raw, f"routing.intents[{index}]")
        name = _string(item.get("intent"), f"routing.intents[{index}].intent")
        if name in result:
            raise ValueError(f"routing intent duplicate: {name}")
        result[name] = item
    return result


def _verify_routing(
    manifest: dict[str, Any],
    skills: dict[str, SkillRef],
    profiles: set[str],
    workflows: set[str],
) -> int:
    intents = _routing_intents(manifest)
    for intent_name, intent in intents.items():
        primary = _string(intent.get("primary_skill"), f"routing intent '{intent_name}'.primary_skill")
        _require_primary(skills, f"routing intent '{intent_name}'", primary, intent.get("availability"))
        for key in ("supporting_skills", "fallback_skills", "mutually_exclusive"):
            values = _string_list(intent.get(key, []), f"routing intent '{intent_name}'.{key}")
            _verify_skill_refs(skills, values, f"routing intent '{intent_name}' {key}")

    scenarios = _named_items(manifest, "skill_routing_matrix")
    if not scenarios:
        raise ValueError("skill_routing_matrix has no scenarios")
    for scenario in scenarios:
        name = scenario["name"]
        if not _SNAKE_CASE.fullmatch(name):
            raise ValueError(f"routing scenario name must be snake_case: {name}")
        intent_name = _string(scenario.get("routing_intent"), f"routing scenario '{name}'.routing_intent")
        intent = intents.get(intent_name)
        if intent is None:
            raise ValueError(f"routing scenario '{name}' references unknown routing intent: {intent_name}")
        primary = _string(intent.get("primary_skill"), f"routing intent '{intent_name}'.primary_skill")
        _require_primary(skills, f"routing scenario '{name}'", primary, intent.get("availability"))
        workflow = _string(scenario.get("workflow"), f"routing scenario '{name}'.workflow")
        if workflow not in {"-", "none"} and workflow not in workflows:
            raise ValueError(f"routing scenario '{name}' workflow unknown: {workflow}")
        scenario_profiles = _string_list(
            scenario.get("profiles"), f"routing scenario '{name}'.profiles", nonempty=True
        )
        for profile in scenario_profiles:
            if profile not in profiles:
                raise ValueError(f"routing scenario '{name}' profile unknown: {profile}")
        _string_list(
            scenario.get("positive_examples"),
            f"routing scenario '{name}'.positive_examples",
            nonempty=True,
        )
        _string_list(
            scenario.get("negative_examples"),
            f"routing scenario '{name}'.negative_examples",
            nonempty=True,
        )
    return len(scenarios)


def validate_asset_taxonomy(root: Path) -> dict[str, Any]:
    manifest = load_canonical_manifest(root)
    _mapping(manifest.get("asset_taxonomy"), "asset_taxonomy")
    if "skill_routing_matrix" not in manifest:
        raise ValueError("manifest missing skill_routing_matrix")
    skills = _skill_index(manifest)
    _verify_skill_dependencies(manifest, skills)
    profiles = _verify_profiles(manifest, skills)
    workflows = _verify_workflows(manifest)
    scenario_count = _verify_routing(manifest, skills, profiles, workflows)
    return {
        "schema": "adk-asset-taxonomy-check/v2",
        "status": "pass",
        "source": "manifest.json",
        "skills": sum(1 for ref in skills.values() if not ref.optional),
        "optional_skills": sum(1 for ref in skills.values() if ref.optional),
        "profiles": len(profiles),
        "workflows": len(workflows),
        "routing_scenarios": scenario_count,
    }
