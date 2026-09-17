"""Skill-content-v2 eligibility adapter for the stable matcher kernel.

The existing routing IR remains authoritative. This layer constrains implicit
trigger fallback with the v2 runtime-role/selection-group/effect-ceiling
contract; it never grants permissions that the routing IR did not already
grant. It also exposes side-effect escalation boundaries so workspace authority
cannot be confused with live-device or release-target authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from .matcher import (
    _abstain_result,
    _classify_task_mode,
    _discover_root,
    _managed_skill_entries,
    _resolved_policy,
    _routing_ir,
    _routing_markers,
    format_result,
    match_text as kernel_match_text,
)
from .model import Manifest, ManifestError


_CONTRACT = "manifests/skill_content_contracts_v2.json"
_READONLY_CEILINGS = {"read-only", "diagnostic-execution", "external-read"}
_ALLOWED_EFFECT_SCOPES = {
    "none",
    "workspace",
    "build",
    "host-system",
    "live-device",
    "external-service",
    "release-target",
}
_ALLOWED_EFFECT_OPERATIONS = {
    "read",
    "diagnostic",
    "write",
    "prepare",
    "register-write",
    "diagnostic-write",
    "flash",
    "storage-write",
    "publish",
}
_ALLOWED_ESCALATION_EFFECTS = {
    "live-device:register-write",
    "live-device:diagnostic-write",
    "live-device:flash",
    "live-device:storage-write",
    "release-target:publish",
}
_ALLOWED_IMPLICIT_POLICIES = {"eligible", "promote-same-group", "explicit-only"}


@lru_cache(maxsize=8)
def _load_contract(path_value: str, mtime_ns: int, size: int) -> Mapping[str, Any]:
    del mtime_ns, size
    path = Path(path_value)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("Skill v2 content contract is invalid: {}".format(exc)) from exc
    if not isinstance(value, dict) or value.get("schema_version") != "adk-skill-content-contract/v2":
        raise ManifestError("Skill v2 content contract has unsupported schema")
    if value.get("identity_source") != "manifest.json":
        raise ManifestError("Skill v2 content contract must derive identity from manifest.json")
    return value


def _contract(manifest: Manifest) -> Mapping[str, Any]:
    path = manifest.root / _CONTRACT
    if not path.is_file():
        raise ManifestError("Skill v2 content contract is missing: {}".format(_CONTRACT))
    stat = path.stat()
    return _load_contract(str(path.resolve()), stat.st_mtime_ns, stat.st_size)


def _skill_entry(manifest: Manifest, skill_id: str) -> tuple[str, Mapping[str, Any]]:
    for scope, section in (("core", "skills"), ("optional", "optional_skills")):
        entries = manifest.data.get(section, [])
        if not isinstance(entries, list):
            raise ManifestError("manifest {} must be an array".format(section))
        for item in entries:
            if isinstance(item, dict) and item.get("name") == skill_id:
                return scope, item
    raise ManifestError("Skill v2 contract references unknown skill: {}".format(skill_id))


def resolve_skill_content(manifest: Manifest, skill_id: str) -> Dict[str, Any]:
    contract = _contract(manifest)
    scope, entry = _skill_entry(manifest, skill_id)
    derivation = contract.get("derivation", {})
    overrides = contract.get("overrides", {})
    if not isinstance(derivation, dict) or not isinstance(overrides, dict):
        raise ManifestError("Skill v2 derivation/overrides must be objects")
    override = overrides.get(skill_id, {})
    if not isinstance(override, dict):
        raise ManifestError("Skill v2 override must be an object: {}".format(skill_id))

    classes = derivation.get("capability_class_by_pattern", {})
    ceilings = derivation.get("effect_ceiling_by_category", {})
    scopes = derivation.get("effect_scope_by_ceiling", {})
    operations = derivation.get("effect_operation_by_ceiling", {})
    if not all(isinstance(value, dict) for value in (classes, ceilings, scopes, operations)):
        raise ManifestError("Skill v2 derivation maps are invalid")

    capability = override.get("capability_class", classes.get(entry.get("pattern")))
    effect = override.get("effect_ceiling", ceilings.get(entry.get("category")))
    effect_scope = override.get("effect_scope", scopes.get(effect))
    effect_operation = override.get("effect_operation", operations.get(effect))
    if "runtime_role" in override:
        role = override["runtime_role"]
    elif capability in ("support", "knowledge"):
        role = "supporting"
    elif capability == "guardrail":
        role = "governance"
    else:
        role = entry.get("activation_mode")
    selection_group = override.get("selection_group", entry.get("category"))
    implicit_policy = override.get("implicit_trigger_policy")
    if implicit_policy is None:
        if role == "primary":
            implicit_policy = "eligible"
        elif role == "supporting":
            implicit_policy = "promote-same-group"
        else:
            implicit_policy = "explicit-only"
    escalation_effects = override.get("escalation_effects", [])

    if capability not in {"task", "workflow", "support", "guardrail", "tool", "knowledge", "meta"}:
        raise ManifestError("Skill v2 capability_class unresolved: {}".format(skill_id))
    if role not in {"primary", "supporting", "governance", "fallback"}:
        raise ManifestError("Skill v2 runtime_role unresolved: {}".format(skill_id))
    if effect not in {
        "read-only",
        "diagnostic-execution",
        "workspace-write",
        "build-artifact-write",
        "release-preparation",
        "external-read",
    }:
        raise ManifestError("Skill v2 effect_ceiling unresolved: {}".format(skill_id))
    if effect_scope not in _ALLOWED_EFFECT_SCOPES:
        raise ManifestError("Skill v2 effect_scope unresolved: {}".format(skill_id))
    if effect_operation not in _ALLOWED_EFFECT_OPERATIONS:
        raise ManifestError("Skill v2 effect_operation unresolved: {}".format(skill_id))
    if not isinstance(selection_group, str) or not selection_group:
        raise ManifestError("Skill v2 selection_group unresolved: {}".format(skill_id))
    if implicit_policy not in _ALLOWED_IMPLICIT_POLICIES:
        raise ManifestError("Skill v2 implicit_trigger_policy unresolved: {}".format(skill_id))
    if not isinstance(escalation_effects, list) or any(
        not isinstance(item, str) or item not in _ALLOWED_ESCALATION_EFFECTS
        for item in escalation_effects
    ):
        raise ManifestError("Skill v2 escalation_effects invalid: {}".format(skill_id))
    if role == "primary" and implicit_policy != "eligible":
        raise ManifestError("Skill v2 primary must remain implicitly eligible: {}".format(skill_id))
    if role != "supporting" and implicit_policy == "promote-same-group":
        raise ManifestError("Only supporting skills may promote to a same-group primary: {}".format(skill_id))

    return {
        "scope": scope,
        "capability_class": str(capability),
        "runtime_role": str(role),
        "selection_group": selection_group,
        "effect_ceiling": str(effect),
        "effect_scope": str(effect_scope),
        "effect_operation": str(effect_operation),
        "implicit_trigger_policy": str(implicit_policy),
        "escalation_effects": tuple(escalation_effects),
    }


def _apply_contract(result: Mapping[str, Any], metadata: Mapping[str, Any]) -> Dict[str, Any]:
    constrained = dict(result)
    constrained["skill_runtime_role"] = metadata["runtime_role"]
    constrained["selection_group"] = metadata["selection_group"]
    constrained["effect_ceiling"] = metadata["effect_ceiling"]
    constrained["effect_scope"] = metadata["effect_scope"]
    constrained["effect_operation"] = metadata["effect_operation"]
    constrained["implicit_trigger_policy"] = metadata["implicit_trigger_policy"]
    escalation_effects = tuple(metadata.get("escalation_effects", ()))
    constrained["escalation_effects"] = ",".join(escalation_effects) if escalation_effects else "none"
    if any(item.startswith("live-device:") for item in escalation_effects):
        constrained["live_device_authorization"] = "explicit-required"
        constrained["live_device_authorization_requirements"] = (
            "target-identity,explicit-authorization,rollback-or-recovery,post-write-verification"
        )
    else:
        constrained["live_device_authorization"] = "not-required"
    if any(item.startswith("release-target:") for item in escalation_effects):
        constrained["release_target_authorization"] = "explicit-required"
    else:
        constrained["release_target_authorization"] = "not-required"

    # A ceiling may only remove write authority. It must never upgrade a deny or
    # explicit-approval result into a stronger permission. Escalation effects are
    # a second gate: workspace/release preparation authority never grants live
    # device or publish authority by itself.
    if metadata["effect_ceiling"] in _READONLY_CEILINGS:
        constrained["mutation_permission"] = "deny"
    return constrained


def _primary_in_group(manifest: Manifest, selection_group: str) -> Optional[tuple[str, str, Mapping[str, Any]]]:
    candidates = []
    for section, source in (("skills", "skill_trigger"), ("optional_skills", "optional_skill_trigger")):
        for name, _path in _managed_skill_entries(manifest, section):
            metadata = resolve_skill_content(manifest, name)
            if metadata["runtime_role"] == "primary" and metadata["selection_group"] == selection_group:
                candidates.append((name, source, metadata))
    if len(candidates) > 1:
        raise ManifestError(
            "Skill v2 selection group has multiple primary skills: {} -> {}".format(
                selection_group,
                ",".join(item[0] for item in candidates),
            )
        )
    return candidates[0] if candidates else None


def _next_primary_trigger(
    manifest: Manifest,
    text: str,
    preferred_group: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    routing = _routing_ir(manifest)
    markers = _routing_markers(routing) if routing else ()
    classified = _classify_task_mode(routing, text, markers) if routing else {
        "task_mode": "needs-triage",
        "mutation_permission": "deny",
        "explicit": False,
    }

    # A supporting Skill may provide the lexical trigger for its capability
    # family. Promote only the same-group unique primary. Falling through to an
    # unrelated primary would turn a content overlap into an authority/routing
    # bug, so absence of a same-group primary fails closed.
    if preferred_group:
        grouped = _primary_in_group(manifest, preferred_group)
        if grouped is None:
            return None
        name, source, metadata = grouped
        result: Dict[str, Any] = {
            "match": True,
            "source": source,
            "skill": name,
            "trigger": "selection-group:{}".format(preferred_group),
            "selection_group_promoted": True,
        }
        result.update(_resolved_policy(routing, classified))
        return _apply_contract(result, metadata)

    for section, source, scope in (
        ("skills", "skill_trigger", "skill"),
        ("optional_skills", "optional_skill_trigger", "optional-skill"),
    ):
        for name, _path in _managed_skill_entries(manifest, section):
            metadata = resolve_skill_content(manifest, name)
            if metadata["runtime_role"] != "primary":
                continue
            candidate = kernel_match_text(manifest, text, skill=name, scope=scope)
            if candidate.get("match") is not True:
                continue
            result = {
                "match": True,
                "source": source,
                "skill": name,
                "trigger": candidate.get("phrase", "explicit-trigger"),
            }
            result.update(_resolved_policy(routing, classified))
            return _apply_contract(result, metadata)
    return None


def match_text(
    manifest: Manifest,
    text: str,
    skill: Optional[str] = None,
    scope: str = "auto",
) -> Dict[str, Any]:
    result = kernel_match_text(manifest, text, skill=skill, scope=scope)
    if skill:
        # Explicit selection is allowed to load a supporting/governance Skill;
        # runtime_role only controls implicit primary eligibility.
        if result.get("match") is True:
            return _apply_contract(result, resolve_skill_content(manifest, skill))
        return dict(result)
    if result.get("match") is not True:
        return dict(result)

    selected = str(result.get("skill", ""))
    metadata = resolve_skill_content(manifest, selected)
    if result.get("source") == "routing":
        if metadata["runtime_role"] != "primary":
            raise ManifestError("routing primary must resolve Skill v2 runtime_role=primary: {}".format(selected))
        return _apply_contract(result, metadata)
    if result.get("source") in ("skill_trigger", "optional_skill_trigger"):
        if metadata["runtime_role"] == "primary":
            return _apply_contract(result, metadata)
        if metadata["implicit_trigger_policy"] == "explicit-only":
            routing = _routing_ir(manifest)
            markers = _routing_markers(routing) if routing else ()
            classified = _classify_task_mode(routing, text, markers) if routing else {
                "task_mode": "needs-triage",
                "mutation_permission": "deny",
                "explicit": False,
            }
            abstained = _abstain_result(routing, classified, [selected])
            abstained["reason"] = "supporting-skill-explicit-only"
            return abstained
        replacement = _next_primary_trigger(
            manifest,
            text,
            preferred_group=metadata["selection_group"],
        )
        if replacement is not None:
            return replacement
        routing = _routing_ir(manifest)
        markers = _routing_markers(routing) if routing else ()
        classified = _classify_task_mode(routing, text, markers) if routing else {
            "task_mode": "needs-triage",
            "mutation_permission": "deny",
            "explicit": False,
        }
        abstained = _abstain_result(routing, classified, [selected])
        abstained["reason"] = "no-primary-in-selection-group"
        return abstained
    return _apply_contract(result, metadata)


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
