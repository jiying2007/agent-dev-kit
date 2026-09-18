"""Semantic phase-context and delivery-lifecycle resolution.

Phase loading resolves semantic selectors from the Phase Context v2 contract.
Manifest asset identity and Skill Content v2 semantics are authoritative; no
parallel phase-to-path mirror exists in the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .matcher_vnext import resolve_skill_content
from .model import Manifest, ManifestError, ensure_within
from .skill_relationships import resolve_delivery_lifecycle as _resolve_delivery_lifecycle

_CONTRACT = "manifests/phase_context_contract_v2.json"
_CONTRACT_SCHEMA = "schemas/phase-context-contract-v2.schema.json"
_SCHEMA = "adk-phase-context-contract/v2"
_RESOLUTION_SCHEMA = "adk-phase-context-resolution/v2"
_LIFECYCLE_RESOLUTION_SCHEMA = "adk-delivery-lifecycle-resolution/v2"
_ROLE_ORDER = {"primary": 0, "supporting": 1, "governance": 2, "fallback": 3}


@lru_cache(maxsize=8)
def _load_contract(
    path_value: str,
    path_mtime_ns: int,
    path_size: int,
    schema_value: str,
    schema_mtime_ns: int,
    schema_size: int,
) -> Mapping[str, Any]:
    del path_mtime_ns, path_size, schema_mtime_ns, schema_size
    path = Path(path_value)
    schema_path = Path(schema_value)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"Phase context contract or schema is invalid: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(schema, dict):
        raise ManifestError("Phase context contract and schema must be JSON objects")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ManifestError(f"Phase context schema is not valid Draft 2020-12: {exc.message}") from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            location = "/".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise ManifestError("Phase context contract schema validation failed: " + "; ".join(rendered))
    if value.get("schema_version") != _SCHEMA:
        raise ManifestError("Phase context contract has unsupported schema")
    if value.get("identity_source") != "manifest.json":
        raise ManifestError("Phase context identity_source must be manifest.json")
    if value.get("skill_semantics_source") != "manifests/skill_content_contracts_v2.json":
        raise ManifestError("Phase context skill semantics must come from Skill Content v2")
    if value.get("relationship_semantics_source") != "manifests/skill_relationship_contracts_v2.json":
        raise ManifestError("Phase context relationship semantics must come from Skill Relationship v2")
    return value


def _contract(manifest: Manifest) -> tuple[Mapping[str, Any], str]:
    path = manifest.root / _CONTRACT
    schema_path = manifest.root / _CONTRACT_SCHEMA
    if not path.is_file():
        raise ManifestError(f"Phase context contract is missing: {_CONTRACT}")
    if not schema_path.is_file():
        raise ManifestError(f"Phase context schema is missing: {_CONTRACT_SCHEMA}")
    stat = path.stat()
    schema_stat = schema_path.stat()
    value = _load_contract(
        str(path.resolve()),
        stat.st_mtime_ns,
        stat.st_size,
        str(schema_path.resolve()),
        schema_stat.st_mtime_ns,
        schema_stat.st_size,
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return value, digest


def _skill_entries(manifest: Manifest) -> Dict[str, Mapping[str, Any]]:
    entries: Dict[str, Mapping[str, Any]] = {}
    for section in ("skills", "optional_skills"):
        values = manifest.data.get(section, [])
        if not isinstance(values, list):
            raise ManifestError(f"manifest {section} must be an array")
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            name = str(item["name"])
            if name in entries:
                raise ManifestError(f"duplicate Skill identity in manifest: {name}")
            entries[name] = item
    return entries


def _resolved_skill(manifest: Manifest, entries: Mapping[str, Mapping[str, Any]], name: str) -> Dict[str, Any]:
    entry = entries.get(name)
    if entry is None:
        raise ManifestError(f"Phase context references unknown Skill: {name}")
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise ManifestError(f"Phase context Skill has no manifest path: {name}")
    source = manifest.root / path
    if not source.is_file():
        raise ManifestError(f"Phase context Skill source is missing: {name} -> {path}")
    metadata = resolve_skill_content(manifest, name)
    return {
        "name": name,
        "path": path,
        "runtime_role": metadata["runtime_role"],
        "selection_group": metadata["selection_group"],
        "effect_ceiling": metadata["effect_ceiling"],
        "effect_scope": metadata["effect_scope"],
        "effect_operation": metadata["effect_operation"],
    }


def _resolve_selector(
    manifest: Manifest,
    entries: Mapping[str, Mapping[str, Any]],
    selector: Mapping[str, Any],
) -> list[Dict[str, Any]]:
    kind = selector.get("kind")
    if kind == "skill":
        name = selector.get("skill")
        expected = selector.get("expected_runtime_role")
        if not isinstance(name, str) or not isinstance(expected, str):
            raise ManifestError("Phase Skill selector is malformed")
        item = _resolved_skill(manifest, entries, name)
        if item["runtime_role"] != expected:
            raise ManifestError(
                f"Phase Skill selector role drift: {name} expected={expected} actual={item['runtime_role']}"
            )
        return [item]

    if kind == "selection-group":
        group = selector.get("selection_group")
        roles = selector.get("include_runtime_roles")
        cardinality = selector.get("primary_cardinality")
        if not isinstance(group, str) or not isinstance(roles, list) or not roles:
            raise ManifestError("Phase selection-group selector is malformed")
        selected: list[Dict[str, Any]] = []
        for name in sorted(entries):
            item = _resolved_skill(manifest, entries, name)
            if item["selection_group"] == group and item["runtime_role"] in roles:
                selected.append(item)
        if not selected:
            raise ManifestError(f"Phase selection group resolved no Skills: {group}")
        primary_count = sum(item["runtime_role"] == "primary" for item in selected)
        if cardinality == "exactly-one" and primary_count != 1:
            raise ManifestError(
                f"Phase selection group requires exactly one primary: {group} -> {primary_count}"
            )
        if cardinality == "zero-or-one" and primary_count > 1:
            raise ManifestError(
                f"Phase selection group allows at most one primary: {group} -> {primary_count}"
            )
        if cardinality not in {"exactly-one", "zero-or-one", "not-required"}:
            raise ManifestError(f"Phase selection group has invalid primary_cardinality: {group}")
        return sorted(selected, key=lambda item: (_ROLE_ORDER[item["runtime_role"]], item["name"]))

    raise ManifestError(f"Unsupported phase selector kind: {kind}")


def resolve_phase_context(manifest: Manifest, domain: str, phase: str) -> Dict[str, Any]:
    contract, contract_digest = _contract(manifest)
    domains = contract.get("domains")
    if not isinstance(domains, dict) or domain not in domains:
        raise ManifestError(f"Unknown phase context domain: {domain}")
    phases = domains[domain]
    if not isinstance(phases, dict) or phase not in phases:
        raise ManifestError(f"Unknown phase context phase: {domain}/{phase}")
    spec = phases[phase]
    if not isinstance(spec, dict):
        raise ManifestError(f"Phase context spec must be an object: {domain}/{phase}")
    selectors = spec.get("selectors")
    resources = spec.get("resources")
    if not isinstance(selectors, list) or not selectors or not isinstance(resources, list):
        raise ManifestError(f"Phase context spec is malformed: {domain}/{phase}")

    entries = _skill_entries(manifest)
    resolved: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for selector in selectors:
        if not isinstance(selector, dict):
            raise ManifestError(f"Phase selector must be an object: {domain}/{phase}")
        for item in _resolve_selector(manifest, entries, selector):
            if item["name"] in seen:
                continue
            seen.add(item["name"])
            resolved.append(item)

    resolved.sort(key=lambda item: (_ROLE_ORDER[item["runtime_role"]], item["name"]))
    resource_rows = []
    for value in resources:
        if not isinstance(value, str) or not value:
            raise ManifestError(f"Phase resource must be a non-empty path: {domain}/{phase}")
        path = ensure_within(manifest.root / value, manifest.root, "phase resource")
        if not path.exists():
            raise ManifestError(f"Phase resource does not exist: {value}")
        resource_rows.append(value)

    return {
        "schema": _RESOLUTION_SCHEMA,
        "status": "pass",
        "domain": domain,
        "phase": phase,
        "contract_path": _CONTRACT,
        "contract_sha256": contract_digest,
        "identity_source": "manifest.json",
        "skill_semantics_source": "manifests/skill_content_contracts_v2.json",
        "skills": resolved,
        "resources": resource_rows,
    }


def resolve_delivery_lifecycle(manifest: Manifest) -> Dict[str, Any]:
    """Delegate lifecycle sequencing to Skill Relationship v2."""
    return _resolve_delivery_lifecycle(manifest)

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="phase-context")
    parser.add_argument("--domain")
    parser.add_argument("--phase")
    parser.add_argument("--lifecycle", action="store_true")
    parser.add_argument("--root", default=None)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    try:
        manifest = Manifest.load(root)
        if args.lifecycle:
            if args.domain or args.phase:
                raise ManifestError("--lifecycle cannot be combined with --domain/--phase")
            result = resolve_delivery_lifecycle(manifest)
        else:
            if not args.domain or not args.phase:
                raise ManifestError("--domain and --phase are required unless --lifecycle is used")
            result = resolve_phase_context(manifest, args.domain, args.phase)
    except ManifestError as exc:
        failure_schema = _LIFECYCLE_RESOLUTION_SCHEMA if args.lifecycle else _RESOLUTION_SCHEMA
        print(json.dumps({"schema": failure_schema, "status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.lifecycle:
        for item in result["steps"]:
            print(f"{item['order']}\t{item['stage']}\t{item['runtime_role']}\t{item['name']}\t{item['path']}")
    else:
        for item in result["skills"]:
            print(f"{item['runtime_role']}\t{item['name']}\t{item['path']}")
        for resource in result["resources"]:
            print(f"resource\t{resource}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
