"""Internal deterministic routing kernel for the canonical ADK matcher."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import yaml

from .model import Manifest, ManifestError
from .safe_yaml import safe_load


def _phrase_occurrences(text: str, phrase: str) -> Iterable[Tuple[str, int]]:
    """Find a literal phrase, allowing bounded embedded-driver target modifiers.

    Existing action phrases remain the trigger: a bare bus/runtime/driver noun
    cannot match, and modifiers cannot cross a clause or arbitrary prose. The
    matched span retains the action's start for the canonical negation check.
    """
    if phrase in ("实现驱动", "编写驱动", "写驱动"):
        modifier = (
            r"(?:linux(?:kernel)?|freertos|rtos|zephyr|裸机|bare-?metal|"
            r"spi|i2c|uart|usart|dma|gpio|usb|can|sdio|ethernet|"
            r"外设|设备|一个|新的|的|上|中|[-/])"
        )
        pattern = re.escape(phrase[:-2]) + modifier + r"{0,8}驱动"
        for match in re.finditer(pattern, text):
            yield match.group(0), match.start()
        return
    position = text.find(phrase)
    while position >= 0:
        yield phrase, position
        position = text.find(phrase, position + len(phrase))


def _all_phrase_matches(text: str, phrase_set: str) -> Sequence[Tuple[str, int, int]]:
    """Keep every occurrence: a later affirmative action may survive a denial."""

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
        for matched, position in _phrase_occurrences(normalized, normalized_phrase):
            matches.append((phrase if matched == normalized_phrase else matched, position, specificity))
    return matches


def _normalized(value: str) -> str:
    return "".join(value.casefold().split())


def _is_locally_negated(
    text: str,
    match: Tuple[str, int, int],
    markers: Sequence[str],
) -> bool:
    """Match nearby prohibitions within one clause, not distant unrelated intent.

    The bounded filler grammar covers common verbs and rephrasing without
    treating an arbitrary '不' elsewhere in the request as a negation.
    """

    _, position, _ = match
    prefix = _normalized(text)[:position]
    clause_start = max(prefix.rfind(separator) for separator in "，,。.!！?？；;：:")
    local = prefix[clause_start + 1:]
    fillers = ("", "做", "进行", "执行", "重新", "再", "先", "去",
               "安排", "启动", "开始", "现在", "尝试", "继续",
               "做一下", "先做", "先进行", "重新做", "重新进行",
               "使用", "用", "调用", "加载", "触发", "use", "load", "invoke", "activate")
    candidates = tuple(_normalized(marker) for marker in markers if _normalized(marker)) + (
        "donot", "don't", "dont", "never", "avoid", "without",
    )
    # Creation is a verb + optional determiner + newness + tool qualifier.
    # No arbitrary prose or intervening action may connect a denial to a noun.
    creation = r"(?:创建|新建|create)(?:一个|一棵|任何|任意|another|any|the|an|a)?(?:新(?:的)?|new)?(?:git)?$"
    return any(local.endswith(marker + filler) for marker in candidates for filler in fillers) or any(
        re.search(re.escape(marker) + creation, local) is not None for marker in candidates
    )


def _is_mentioned_action(text: str, match: Tuple[str, int, int]) -> bool:
    """An action under explanation/review is an object, not an execution request.

    Scope ends at a clause or a new coordinated action. Request prefixes keep
    nouns such as compatibility explanations from acting as global exclusions.
    """
    prefix = _normalized(text)[:match[1]]
    local = re.split(r"[，,。.!！?？；;]|然后|接着|而是|但是|但|并且|(?<!合)并(?!发|行|列)", prefix)[-1]
    request = r"(?:^|请|只读|先|仅|只|帮我|需要|希望|不要|不用|无需|别)"
    return re.search(request + r"(?:解释|说明|介绍|讲解|审查|评审)", local) is not None


def _active_phrase_matches(
    text: str,
    phrase_set: str,
    markers: Sequence[str],
) -> Sequence[Tuple[str, int, int]]:
    matches = _all_phrase_matches(text, phrase_set)
    inactive_spans = tuple(
        (item[1], item[1] + len(_normalized(item[0])))
        for item in matches
        if _is_locally_negated(text, item, markers) or _is_mentioned_action(text, item)
    )
    return tuple(
        item for item in matches
        if not any(start <= item[1] and item[1] + len(_normalized(item[0])) <= end
                   for start, end in inactive_spans)
    )


def _skill_identity_declined(text: str, skill: str, markers: Sequence[str]) -> bool:
    folded = text.casefold()
    pattern = r"(?<![a-z0-9_-])" + re.escape(skill.casefold()) + r"(?![a-z0-9_-])"
    for match in re.finditer(pattern, folded):
        # Recognize only bounded display/call prefixes around this exact name;
        # arbitrary punctuation elsewhere must retain the canonical polarity.
        start = match.start()
        if start > 0 and folded[start - 1] in "$@":
            start -= 1
        if start > 0 and folded[start - 1] == "`":
            start -= 1
        position = len(_normalized(folded[:start]))
        if _is_locally_negated(text, (skill, position, 0), markers):
            return True
    return False


@lru_cache(maxsize=512)
def _frontmatter_cached(raw: bytes) -> Mapping[str, Any]:
    lines = raw.decode("utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ManifestError("skill frontmatter is missing")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ManifestError("skill frontmatter is not terminated") from exc
    try:
        value = safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ManifestError("skill frontmatter is invalid") from exc
    if not isinstance(value, dict):
        raise ManifestError("skill frontmatter must be a mapping")
    return value


def _frontmatter(path: Path) -> Mapping[str, Any]:
    try:
        return _frontmatter_cached(path.read_bytes())
    except (OSError, UnicodeError) as exc:
        raise ManifestError("skill frontmatter is unreadable: {}".format(path)) from exc
    except ManifestError as exc:
        raise ManifestError("{}: {}".format(exc, path)) from exc


def _phrases(frontmatter: Mapping[str, Any], key: str) -> Iterable[str]:
    value = frontmatter.get(key, [])
    if not isinstance(value, list):
        raise ManifestError("skill frontmatter {} must be a list".format(key))
    for item in value:
        if isinstance(item, str) and item:
            yield item


def _has_affirmative_context(text: str, contexts: Sequence[str], markers: Sequence[str]) -> bool:
    """Extend domain negation only across adjacent, declared domain names.

    Punctuation and intervening actions break the compact list. This does not
    change the action/mode/permission polarity used by the routing IR.
    """
    normalized = _normalized(text)
    matches = sorted(
        (match for phrase in contexts for match in _all_phrase_matches(text, phrase)),
        key=lambda item: item[1],
    )
    negated_ends: set[int] = set()
    conjunctions = {"或", "和", "与", "及", "、", "and", "or", "nor"}
    for match in matches:
        phrase, position, _ = match
        inherited = any(
            position - len(conjunction) in negated_ends
            and normalized[position - len(conjunction):position] == conjunction
            for conjunction in conjunctions
        )
        if not inherited and not _is_locally_negated(text, match, markers):
            return True
        negated_ends.add(position + len(_normalized(phrase)))
    return False


def _implicit_context_matches(
    frontmatter: Mapping[str, Any],
    text: str,
    markers: Sequence[str],
) -> bool:
    """Require an affirmative domain hint only when the Skill opts in.

    This lexical eligibility check is not the runtime Fit Gate. Context may
    precede the task in another sentence. Inline formatting preserves domain
    names; fenced code and explicitly introduced quotations are not domain facts.
    Explicit single-Skill diagnostics do not apply this implicit-only filter.
    """
    if "implicit_context" not in frontmatter:
        return True
    contexts = frontmatter["implicit_context"]
    if (
        not isinstance(contexts, list) or not contexts
        or not all(isinstance(value, str) and any(part.strip() for part in value.split("/"))
                   for value in contexts)
    ):
        raise ManifestError("skill implicit_context must be a non-empty phrase list")
    context_text = re.sub(r"\x60{3}.*?\x60{3}|~{3}.*?~{3}", " ", text, flags=re.DOTALL)
    inline = r"\x60[^\x60\n]*\x60|\"[^\"\n]*\"|“[^”\n]*”|‘[^’\n]*’|(?<!\w)'[^'\n]*'(?!\w)"
    context_text = re.sub(
        r"(^|[，,。.!！?？；;：:\n])\s*(?:文档写着|(?:文档)?示例|引述|example|quoted?)\s*[:：]?\s*(?:"
        + inline + ")",
        r"\1 ", context_text, flags=re.IGNORECASE,
    )
    context_text = re.sub(inline, lambda match: match.group(0)[1:-1], context_text)
    context_markers = (*markers, "非", "不涉及", "not", "non-")
    return _has_affirmative_context(context_text, contexts, context_markers)


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
        return bool(_active_phrase_matches(text, phrase_set, markers))
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


def _promotion_exclusion(
    manifest: Manifest,
    skill: str,
    text: str,
    markers: Sequence[str],
) -> Optional[str]:
    """Apply the primary's exclusions even when a supporting Skill matched.

    Absence of a primary trigger is allowed: the same-group support supplied
    it. An applicable non-trigger or an explicitly declined primary is not.
    Use the canonical polarity rules rather than a second negation grammar.
    """
    if _matched_skill_non_trigger(manifest, skill, text, markers) is not None:
        return "matched_non_trigger"
    path = _specific_skill_path(manifest, skill, "auto")
    if path is None:
        return "skill_not_found"
    if not _implicit_context_matches(_frontmatter(path), text, markers):
        return "missing_implicit_context"
    if _skill_identity_declined(text, skill, markers):
        return "negated_skill_identity"
    phrases = list(_phrases(_frontmatter(path), "triggers"))
    routing = _routing_ir(manifest)
    classes = _routing_phrase_classes(routing, "phrase_classes") if routing else {}
    for entry in routing.get("intents", []):
        if not isinstance(entry, dict) or entry.get("primary_skill") != skill:
            continue
        phrase_set = entry.get("intent_zh")
        if not isinstance(phrase_set, str):
            continue
        phrases.append(phrase_set)
        if _all_phrase_matches(text, phrase_set) and _matching_negated_intent(text, entry, classes, markers):
            return "negated_intent"
    matching = any(_all_phrase_matches(text, phrase_set) for phrase_set in phrases)
    active = bool(_active_phrase_matches(text, "/".join(phrases), markers))
    return "negated_trigger" if matching and not active else None


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
        if _skill_identity_declined(text, skill, markers):
            return {"match": False, "skill": skill, "reason": "negated_skill_identity"}
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
        active = _active_phrase_matches(text, "/".join(_phrases(frontmatter, "triggers")), markers)
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
    # The existing phrase-class IR may identify explicit requested actions.
    # Prefer an affirmative action over incidental topics; this affects only
    # selection, never task-mode or permission classification.
    requested_actions = {
        _normalized(phrase)
        for phrase_set in phrase_classes.get("requested_action", ())
        for phrase in phrase_set.split("/") if phrase.strip()
    }
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
            matched_phrases = _all_phrase_matches(text, intent_zh)
            if matched_phrases:
                path = _specific_skill_path(manifest, primary, "auto")
                if path is not None and not _implicit_context_matches(_frontmatter(path), text, markers):
                    continue
                active_phrases = _active_phrase_matches(text, intent_zh, markers)
                negated_rule = _matching_negated_intent(
                    text,
                    entry,
                    phrase_classes,
                    markers,
                )
                skill_non_trigger = _matched_skill_non_trigger(manifest, primary, text, markers)
                if (negated_rule is not None or skill_non_trigger is not None or not active_phrases
                        or _skill_identity_declined(text, primary, markers)):
                    negated_intents.append(str(entry.get("intent", primary)))
                    negated_skills.add(primary)
                    continue
                total_specificity = sum(item[2] for item in active_phrases)
                best_specificity = max(item[2] for item in active_phrases)
                first_position = min(item[1] for item in active_phrases)
                requested_action = any(_normalized(item[0]) in requested_actions for item in active_phrases)
                route_matches.append(
                    (-int(requested_action), -total_specificity, -best_specificity, first_position, order, entry)
                )
    if route_matches:
        entry = min(route_matches, key=lambda item: item[:5])[5]
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
            if (not path.is_file() or name in negated_skills
                    or _skill_identity_declined(text, name, markers)):
                continue
            frontmatter = _frontmatter(path)
            if not _implicit_context_matches(frontmatter, text, markers):
                continue
            non_trigger = _matched_skill_non_trigger(manifest, name, text, markers)
            if non_trigger is not None:
                negated_intents.append(name)
                continue
            trigger_sets = tuple(_phrases(frontmatter, "triggers"))
            active_triggers = set(_active_phrase_matches(text, "/".join(trigger_sets), markers))
            for phrase_set in trigger_sets:
                matches = _all_phrase_matches(text, phrase_set)
                active = tuple(item for item in _active_phrase_matches(text, phrase_set, markers)
                               if item in active_triggers)
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


def _discover_root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    current = Path(__file__).resolve()
    for candidate in [Path.cwd()] + list(current.parents):
        if (candidate / "manifest.json").is_file() and (candidate / "scripts/devkit.sh").is_file():
            return candidate.resolve()
    raise ManifestError("ADK asset root not found")
