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


def _phrase_match(text: str, phrase_set: str) -> Optional[Tuple[str, int]]:
    matches = _phrase_matches(text, phrase_set)
    if not matches:
        return None
    phrase, position, _ = min(matches, key=lambda item: (-item[2], item[1]))
    return phrase, position


def _contains_phrase(text: str, phrase_set: str) -> Optional[str]:
    match = _phrase_match(text, phrase_set)
    return match[0] if match is not None else None


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


def match_text(
    manifest: Manifest,
    text: str,
    skill: Optional[str] = None,
    scope: str = "auto",
) -> Dict[str, Any]:
    if not text:
        raise ManifestError("--text is required")
    if skill:
        path = _specific_skill_path(manifest, skill, scope)
        if path is None:
            return {"match": False, "skill": skill, "reason": "skill_not_found"}
        frontmatter = _frontmatter(path)
        for phrase_set in _phrases(frontmatter, "non_triggers"):
            phrase = _contains_phrase(text, phrase_set)
            if phrase is not None:
                return {
                    "match": False,
                    "skill": skill,
                    "reason": "matched_non_trigger",
                    "phrase": phrase,
                }
        for phrase_set in _phrases(frontmatter, "triggers"):
            phrase = _contains_phrase(text, phrase_set)
            if phrase is not None:
                return {
                    "match": True,
                    "skill": skill,
                    "reason": "matched_trigger",
                    "phrase": phrase,
                }
        return {"match": False, "skill": skill, "reason": "no_trigger_matched"}

    routing = manifest.data.get("routing", {})
    intents = routing.get("intents", []) if isinstance(routing, dict) and routing.get("enabled") else []
    route_matches = []
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
                total_specificity = sum(item[2] for item in matched_phrases)
                best_specificity = max(item[2] for item in matched_phrases)
                first_position = min(item[1] for item in matched_phrases)
                route_matches.append(
                    (-total_specificity, -best_specificity, first_position, order, entry)
                )
    if route_matches:
        entry = min(route_matches, key=lambda item: item[:4])[4]
        supporting = entry.get("supporting_skills", [])
        return {
            "match": True,
            "source": "routing",
            "skill": entry["primary_skill"],
            "intent_zh": entry["intent_zh"],
            "supporting_skills": supporting if isinstance(supporting, list) else [],
        }

    for section, source in (("skills", "skill_trigger"), ("optional_skills", "optional_skill_trigger")):
        for name, path in _managed_skill_entries(manifest, section):
            if not path.is_file():
                continue
            frontmatter = _frontmatter(path)
            for phrase_set in _phrases(frontmatter, "triggers"):
                phrase = _contains_phrase(text, phrase_set)
                if phrase is not None:
                    return {
                        "match": True,
                        "source": source,
                        "skill": name,
                        "trigger": phrase_set,
                    }
    return {"match": False, "reason": "no_match_found"}


def format_result(result: Mapping[str, Any]) -> str:
    if result.get("match") is True and result.get("source") == "routing":
        supporting = result.get("supporting_skills", [])
        suffix = ""
        if isinstance(supporting, list) and supporting:
            suffix = " supporting_skills=" + ",".join(str(item) for item in supporting)
        return "match=true source=routing skill={} intent_zh={}{}".format(
            result["skill"],
            json.dumps(result["intent_zh"], ensure_ascii=False),
            suffix,
        )
    if result.get("match") is True and result.get("source") in ("skill_trigger", "optional_skill_trigger"):
        return "match=true source={} skill={} trigger={}".format(
            result["source"],
            result["skill"],
            json.dumps(result["trigger"], ensure_ascii=False),
        )
    if result.get("match") is True:
        return "match=true skill={} reason=matched_trigger phrase={}".format(
            result["skill"], result["phrase"]
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
        if (candidate / "manifest.json").is_file() and (candidate / "scripts/skill-match.sh").is_file():
            return candidate.resolve()
    raise ManifestError("ADK asset root not found")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="skill-match.sh")
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
