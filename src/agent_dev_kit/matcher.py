"""Fast, deterministic matching for managed ADK skills."""

from __future__ import annotations

import argparse
import json
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import yaml

from .model import Manifest, ManifestError


def _phrase_matches(text: str, phrase_set: str) -> Sequence[Tuple[str, int, int]]:
    normalized = "".join(text.casefold().split())
    matches = []
    seen = set()
    for phrase in phrase_set.split("/"):
        phrase = phrase.strip()
        normalized_phrase = "".join(phrase.casefold().split())
        if not normalized_phrase or normalized_phrase in seen:
            continue
        seen.add(normalized_phrase)
        position = normalized.find(normalized_phrase) if normalized_phrase else -1
        if position >= 0:
            specificity = sum(2 if ord(character) > 127 else 1 for character in normalized_phrase)
            matches.append((phrase, position, specificity))
    return matches


def _all_phrase_matches(text: str, phrase_set: str) -> Sequence[Tuple[str, int, int]]:
    """Return every occurrence for polarity checks without changing route scoring.

    Route scoring intentionally keeps the historic first-occurrence behavior in
    ``_phrase_matches``.  Negation polarity must inspect later occurrences too:
    ``准备发布……不执行发布`` contains an active and a negated occurrence of the
    same action phrase.
    """

    normalized = _normalized(text)
    matches = []
    seen = set()
    for phrase in phrase_set.split("/"):
        phrase = phrase.strip()
        normalized_phrase = _normalized(phrase)
        if not normalized_phrase or normalized_phrase in seen:
            continue
        seen.add(normalized_phrase)
        specificity = sum(2 if ord(character) > 127 else 1 for character in normalized_phrase)
        position = normalized.find(normalized_phrase)
        while position >= 0:
            matches.append((phrase, position, specificity))
            position = normalized.find(normalized_phrase, position + len(normalized_phrase))
    return matches


def _phrase_match(text: str, phrase_set: str) -> Optional[Tuple[str, int]]:
    matches = _phrase_matches(text, phrase_set)
    if not matches:
        return None
    phrase, position, _ = min(matches, key=lambda item: (-item[2], item[1]))
    return phrase, position


def _contains_phrase(text: str, phrase_set: str) -> Optional[str]:
    match = _phrase_match(text, phrase_set)
    return match[0] if match is not None else None


def _normalized(value: str) -> str:
    return "".join(value.casefold().split())


def _is_locally_negated(
    text: str,
    match: Tuple[str, int, int],
    markers: Sequence[str],
) -> bool:
    """Return true only when a configured marker directly prefixes a phrase.

    This intentionally does not use an arbitrary character window.  A remote
    ``不`` elsewhere in the request must not suppress an unrelated positive
    intent; multi-clause negation belongs in routing-ir/v2 ``all_of`` rules.
    """

    _, position, _ = match
    prefix = _normalized(text)[:position]
    return any(prefix.endswith(_normalized(marker)) for marker in markers if _normalized(marker))


def _active_phrase_matches(
    text: str,
    phrase_set: str,
    markers: Sequence[str],
) -> Sequence[Tuple[str, int, int]]:
    return tuple(
        item for item in _phrase_matches(text, phrase_set) if not _is_locally_negated(text, item, markers)
    )


@lru_cache(maxsize=512)
def _frontmatter_cached(path_value: str, mtime_ns: int, size: int) -> Mapping[str, Any]:
    del mtime_ns, size
    path = Path(path_value)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ManifestError("skill frontmatter is missing: {}".format(path))
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ManifestError("skill frontmatter is not terminated: {}".format(path)) from exc
    try:
        value = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ManifestError("skill frontmatter is invalid: {}".format(path)) from exc
    if not isinstance(value, dict):
        raise ManifestError("skill frontmatter must be a mapping: {}".format(path))
    return value


def _frontmatter(path: Path) -> Mapping[str, Any]:
    stat = path.stat()
    return _frontmatter_cached(str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def _phrases(frontmatter: Mapping[str, Any], key: str) -> Iterable[str]:
    value = frontmatter.get(key, [])
    if not isinstance(value, list):
        raise ManifestError("skill frontmatter {} must be a list".format(key))
    for item in value:
        if isinstance(item, str) and item:
            yield item


def _managed_skill_entries(manifest: Manifest, section: str) -> Iterable[Tuple[str, Path]]:
    entries = manifest.data.get(section, [])
    if not isinstance(entries, list):
        raise ManifestError("manifest {} must be an array".format(section))
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            continue
        path_value = entry.get("path")
        if isinstance(path_value, str):
            yield str(entry["name"]), manifest.root / path_value


def _specific_skill_path(manifest: Manifest, skill: str, scope: str) -> Optional[Path]:
    core = manifest.root / "skills" / skill / "SKILL.md"
    optional = dict(_managed_skill_entries(manifest, "optional_skills")).get(skill)
    if scope == "skill":
        return core if core.is_file() else None
    if scope == "optional-skill":
        return optional if optional is not None and optional.is_file() else None
    if scope != "auto":
        raise ManifestError("unsupported --scope: {}".format(scope))
    if core.is_file():
        return core
    return optional if optional is not None and optional.is_file() else None


def _routing_ir(manifest: Manifest) -> Mapping[str, Any]:
    routing = manifest.data.get("routing", {})
    if not isinstance(routing, dict) or not routing.get("enabled"):
        return {}
    return routing


def _routing_phrase_classes(
    routing: Mapping[str, Any],
    key: str,
) -> Mapping[str, Sequence[str]]:
    value = routing.get(key, {})
    if not isinstance(value, dict) or not value:
        raise ManifestError("routing.{} must be a non-empty object".format(key))
    result: Dict[str, Sequence[str]] = {}
    for name, phrases in value.items():
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(phrases, list)
            or not phrases
            or not all(isinstance(phrase, str) and phrase for phrase in phrases)
        ):
            raise ManifestError("routing.{} phrase class is invalid: {}".format(key, name))
        result[name] = tuple(phrases)
    return result


def _routing_markers(routing: Mapping[str, Any]) -> Sequence[str]:
    classes = _routing_phrase_classes(routing, "negation_phrase_classes")
    return tuple(
        dict.fromkeys(
            phrase
            for phrases in classes.values()
            for phrase in phrases
        )
    )


def _phrase_class_condition_matches(
    text: str,
    condition: Mapping[str, Any],
    phrase_classes: Mapping[str, Sequence[str]],
    markers: Sequence[str],
) -> bool:
    class_name = condition.get("phrase_class")
    polarity = condition.get("polarity")
    if not isinstance(class_name, str) or class_name not in phrase_classes:
        raise ManifestError("routing negated intent references unknown phrase class: {}".format(class_name))
    if polarity not in ("positive", "negated"):
        raise ManifestError("routing negated intent polarity is invalid: {}".format(polarity))
    phrase_set = "/".join(phrase_classes[class_name])
    matches = _all_phrase_matches(text, phrase_set)
    if polarity == "positive":
        return any(not _is_locally_negated(text, match, markers) for match in matches)
    return any(_is_locally_negated(text, match, markers) for match in matches)


def _classify_task_mode(
    routing: Mapping[str, Any],
    text: str,
    markers: Sequence[str],
) -> Dict[str, Any]:
    defaults = routing.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ManifestError("routing.defaults must be an object")
    fallback = {
        "task_mode": str(defaults.get("task_mode", "needs-triage")),
        "mutation_permission": str(defaults.get("mutation_permission", "deny")),
        "explicit": False,
    }
    task_modes = routing.get("task_modes", [])
    if not isinstance(task_modes, list):
        raise ManifestError("routing.task_modes must be an array")

    candidates = []
    for order, entry in enumerate(task_modes):
        if not isinstance(entry, dict):
            continue
        intent_zh = entry.get("intent_zh")
        task_mode = entry.get("task_mode")
        mutation_permission = entry.get("mutation_permission")
        priority = entry.get("priority")
        if (
            not isinstance(intent_zh, str)
            or not isinstance(task_mode, str)
            or not isinstance(mutation_permission, str)
            or not isinstance(priority, int)
        ):
            continue
        active = _active_phrase_matches(text, intent_zh, markers)
        if not active:
            continue
        best_specificity = max(item[2] for item in active)
        first_position = min(item[1] for item in active)
        candidates.append((-priority, -best_specificity, first_position, order, entry))

    if not candidates:
        return fallback
    entry = min(candidates, key=lambda item: item[:4])[4]
    return {
        "task_mode": entry["task_mode"],
        "mutation_permission": entry["mutation_permission"],
        "explicit": True,
    }


def _matching_negated_intent(
    text: str,
    entry: Mapping[str, Any],
    phrase_classes: Mapping[str, Sequence[str]],
    markers: Sequence[str],
) -> Optional[str]:
    rules = entry.get("negated_intents", [])
    if not isinstance(rules, list):
        raise ManifestError("routing intent negated_intents must be an array")
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        name = rule.get("name")
        conditions = rule.get("all_of")
        if not isinstance(name, str) or not isinstance(conditions, list) or not conditions:
            raise ManifestError("routing negated intent rule is invalid")
        if not all(isinstance(condition, dict) for condition in conditions):
            raise ManifestError("routing negated intent conditions must be objects")
        if all(
            _phrase_class_condition_matches(text, condition, phrase_classes, markers)
            for condition in conditions
        ):
            return name
    return None


def _matched_skill_non_trigger(
    manifest: Manifest,
    skill: str,
    text: str,
    markers: Sequence[str],
) -> Optional[str]:
    path = _specific_skill_path(manifest, skill, "auto")
    if path is None:
        return None
    frontmatter = _frontmatter(path)
    for phrase_set in _phrases(frontmatter, "non_triggers"):
        active = _active_phrase_matches(text, phrase_set, markers)
        if active:
            return min(active, key=lambda item: (-item[2], item[1]))[0]
    return None


def _strictest_permission(*values: Any) -> str:
    order = {
        "deny": 0,
        "explicit-authorization-required": 1,
        "workspace-write": 2,
    }
    permissions = [str(value) for value in values if value in order]
    return min(permissions, key=lambda item: order[item]) if permissions else "deny"


def _artifact_mode(routing: Mapping[str, Any], task_mode: Any) -> Optional[str]:
    mapping = routing.get("artifact_mode_mapping", {})
    if not mapping and task_mode == "needs-triage":
        return None
    if not isinstance(mapping, dict):
        raise ManifestError("routing.artifact_mode_mapping must be an object")
    if task_mode not in mapping:
        raise ManifestError("routing task_mode has no artifact mode mapping: {}".format(task_mode))
    value = mapping[task_mode]
    if value is not None and not isinstance(value, str):
        raise ManifestError("routing artifact mode must be a string or null")
    return value


def _resolved_policy(
    routing: Mapping[str, Any],
    classified: Mapping[str, Any],
    entry: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    defaults = routing.get("defaults", {})
    if not isinstance(defaults, dict):
        defaults = {}
    entry = entry or {}
    classified_mode = classified.get("task_mode", defaults.get("task_mode", "needs-triage"))
    entry_mode = entry.get("task_mode")
    if classified.get("explicit") and classified_mode == "readonly":
        task_mode = "readonly"
    elif isinstance(entry_mode, str):
        task_mode = entry_mode
    elif classified.get("explicit"):
        task_mode = classified_mode
    else:
        task_mode = defaults.get("task_mode", "needs-triage")
    mutation_permission = _strictest_permission(
        entry.get("mutation_permission"),
        classified.get("mutation_permission") if classified.get("explicit") else None,
        defaults.get("mutation_permission", "deny") if not entry and not classified.get("explicit") else None,
    )
    if task_mode in ("needs-triage", "readonly", "debugging", "review"):
        mutation_permission = "deny"
    return {
        "task_mode": task_mode,
        "mutation_permission": mutation_permission,
        "artifact_mode": _artifact_mode(routing, task_mode),
        "risk": entry.get("risk", defaults.get("risk", "unknown")),
        "profile_availability": entry.get(
            "profile_availability",
            entry.get("availability", defaults.get("profile_availability", "fallback-profile")),
        ),
        "required_evidence": entry.get("required_evidence", defaults.get("required_evidence", [])),
    }


def _abstain_result(
    routing: Mapping[str, Any],
    classified: Mapping[str, Any],
    negated_intents: Sequence[str],
) -> Dict[str, Any]:
    abstain = routing.get("abstain", {})
    if not isinstance(abstain, dict) or not abstain.get("enabled"):
        return {"match": False, "reason": "no_match_found"}
    policy = _resolved_policy(routing, classified)
    return {
        "match": False,
        "decision": str(abstain.get("decision", "abstain")),
        "reason": str(abstain.get("reason", "needs-triage")),
        "task_mode": policy["task_mode"],
        "mutation_permission": str(abstain.get("mutation_permission", "deny")),
        "artifact_mode": policy["artifact_mode"],
        "negated_intents": list(dict.fromkeys(negated_intents)),
    }


def match_text(
    manifest: Manifest,
    text: str,
    skill: Optional[str] = None,
    scope: str = "auto",
) -> Dict[str, Any]:
    if not text:
        raise ManifestError("--text is required")
    routing = _routing_ir(manifest)
    markers = _routing_markers(routing) if routing else ()
    phrase_classes = _routing_phrase_classes(routing, "phrase_classes") if routing else {}
    if skill:
        path = _specific_skill_path(manifest, skill, scope)
        if path is None:
            return {"match": False, "skill": skill, "reason": "skill_not_found"}
        frontmatter = _frontmatter(path)
        for phrase_set in _phrases(frontmatter, "non_triggers"):
            active = _active_phrase_matches(text, phrase_set, markers)
            if active:
                phrase = min(active, key=lambda item: (-item[2], item[1]))[0]
                return {
                    "match": False,
                    "skill": skill,
                    "reason": "matched_non_trigger",
                    "phrase": phrase,
                }
        for phrase_set in _phrases(frontmatter, "triggers"):
            active = _active_phrase_matches(text, phrase_set, markers)
            if active:
                phrase = min(active, key=lambda item: (-item[2], item[1]))[0]
                return {
                    "match": True,
                    "skill": skill,
                    "reason": "matched_trigger",
                    "phrase": phrase,
                }
        return {"match": False, "skill": skill, "reason": "no_trigger_matched"}

    classified = _classify_task_mode(routing, text, markers) if routing else {
        "task_mode": "needs-triage",
        "mutation_permission": "deny",
        "explicit": False,
    }
    intents = routing.get("intents", []) if isinstance(routing, dict) and routing.get("enabled") else []
    route_matches = []
    negated_intents = []
    negated_skills = set()
    if isinstance(intents, list):
        for order, entry in enumerate(intents):
            if not isinstance(entry, dict):
                continue
            intent_zh = entry.get("intent_zh")
            primary = entry.get("primary_skill")
            if not isinstance(intent_zh, str) or not isinstance(primary, str):
                continue
            matched_phrases = _phrase_matches(text, intent_zh)
            if matched_phrases:
                active_phrases = _active_phrase_matches(text, intent_zh, markers)
                negated_rule = _matching_negated_intent(
                    text,
                    entry,
                    phrase_classes,
                    markers,
                )
                skill_non_trigger = _matched_skill_non_trigger(manifest, primary, text, markers)
                if negated_rule is not None or skill_non_trigger is not None or not active_phrases:
                    negated_intents.append(str(entry.get("intent", primary)))
                    negated_skills.add(primary)
                    continue
                total_specificity = sum(item[2] for item in active_phrases)
                best_specificity = max(item[2] for item in active_phrases)
                first_position = min(item[1] for item in active_phrases)
                route_matches.append(
                    (-total_specificity, -best_specificity, first_position, order, entry)
                )
    if route_matches:
        entry = min(route_matches, key=lambda item: item[:4])[4]
        supporting = entry.get("supporting_skills", [])
        result = {
            "match": True,
            "source": "routing",
            "skill": entry["primary_skill"],
            "intent": entry["intent"],
            "intent_zh": entry["intent_zh"],
            "supporting_skills": supporting if isinstance(supporting, list) else [],
            "fallback_skills": entry.get("fallback_skills", []),
            "mutually_exclusive": entry.get("mutually_exclusive", []),
        }
        result.update(_resolved_policy(routing, classified, entry))
        return result

    for section, source in (("skills", "skill_trigger"), ("optional_skills", "optional_skill_trigger")):
        for name, path in _managed_skill_entries(manifest, section):
            if not path.is_file() or name in negated_skills:
                continue
            frontmatter = _frontmatter(path)
            non_trigger = _matched_skill_non_trigger(manifest, name, text, markers)
            if non_trigger is not None:
                negated_intents.append(name)
                continue
            for phrase_set in _phrases(frontmatter, "triggers"):
                matches = _phrase_matches(text, phrase_set)
                active = _active_phrase_matches(text, phrase_set, markers)
                if active:
                    phrase, _, _ = min(active, key=lambda item: (-item[2], item[1]))
                    result = {
                        "match": True,
                        "source": source,
                        "skill": name,
                        "trigger": phrase_set,
                    }
                    result.update(_resolved_policy(routing, classified))
                    return result
                if matches:
                    negated_intents.append(name)
    return _abstain_result(routing, classified, negated_intents)


def format_result(result: Mapping[str, Any]) -> str:
    if result.get("match") is True and result.get("source") == "routing":
        supporting = result.get("supporting_skills", [])
        suffix = ""
        if isinstance(supporting, list) and supporting:
            suffix = " supporting_skills=" + ",".join(str(item) for item in supporting)
        return "match=true source=routing skill={} intent_zh={}{} task_mode={} mutation_permission={} artifact_mode={}".format(
            result["skill"],
            json.dumps(result["intent_zh"], ensure_ascii=False),
            suffix,
            result.get("task_mode", "needs-triage"),
            result.get("mutation_permission", "deny"),
            result.get("artifact_mode") or "not-applicable",
        )
    if result.get("match") is True and result.get("source") in ("skill_trigger", "optional_skill_trigger"):
        return "match=true source={} skill={} trigger={} task_mode={} mutation_permission={} artifact_mode={}".format(
            result["source"],
            result["skill"],
            json.dumps(result["trigger"], ensure_ascii=False),
            result.get("task_mode", "needs-triage"),
            result.get("mutation_permission", "deny"),
            result.get("artifact_mode") or "not-applicable",
        )
    if result.get("match") is True:
        return "match=true skill={} reason=matched_trigger phrase={}".format(
            result["skill"], result["phrase"]
        )
    if result.get("decision") == "abstain":
        negated = result.get("negated_intents", [])
        suffix = ""
        if isinstance(negated, list) and negated:
            suffix = " negated_intents=" + ",".join(str(item) for item in negated)
        return "match=false decision=abstain reason={} task_mode={} mutation_permission={} artifact_mode={}{}".format(
            result.get("reason", "needs-triage"),
            result.get("task_mode", "needs-triage"),
            result.get("mutation_permission", "deny"),
            result.get("artifact_mode") or "not-applicable",
            suffix,
        )
    if result.get("skill"):
        suffix = ""
        if result.get("phrase"):
            suffix = " phrase=" + str(result["phrase"])
        return "match=false skill={} reason={}{}".format(result["skill"], result["reason"], suffix)
    return "match=false reason={}".format(result["reason"])


def _discover_root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    current = Path(__file__).resolve()
    for candidate in [Path.cwd()] + list(current.parents):
        if (candidate / "manifest.json").is_file() and (candidate / "scripts/devkit.sh").is_file():
            return candidate.resolve()
    raise ManifestError("ADK asset root not found")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh match")
    parser.add_argument("--text", required=True)
    parser.add_argument("--skill")
    parser.add_argument("--scope", choices=("auto", "skill", "optional-skill"), default="auto")
    args = parser.parse_args(argv)
    try:
        result = match_text(Manifest.load(_discover_root()), args.text, args.skill, args.scope)
    except ManifestError as exc:
        print("[FAIL] {}".format(exc), file=sys.stderr)
        return 1
    print(format_result(result))
    return 0 if result.get("match") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
