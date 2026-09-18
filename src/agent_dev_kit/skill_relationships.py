"""Typed Skill relationships and terminal delivery lifecycle resolution.

All Skill relationships are explicit typed edges in Skill Relationship v2.
Manifest asset identity remains authoritative, but manifest metadata carries no
parallel dependency graph.
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

from .matcher import resolve_skill_content
from .model import Manifest, ManifestError

_CONTRACT = "manifests/skill_relationship_contracts_v2.json"
_CONTRACT_SCHEMA = "schemas/skill-relationship-contract-v2.schema.json"
_SCHEMA = "adk-skill-relationship-contract/v2"
_RESOLUTION_SCHEMA = "adk-skill-relationship-resolution/v2"
_LIFECYCLE_SCHEMA = "adk-delivery-lifecycle-resolution/v2"
_EXPECTED_STAGES = ("review", "completion", "commit-pr", "closeout")
_ALLOWED_TYPES = {
    "context-prerequisite",
    "evidence-prerequisite",
    "handoff",
    "delivery-precedence",
}


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
        raise ManifestError(f"Skill relationship contract or schema is invalid: {exc}") from exc
    if not isinstance(value, dict) or not isinstance(schema, dict):
        raise ManifestError("Skill relationship contract and schema must be JSON objects")
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise ManifestError(
            f"Skill relationship schema is not valid Draft 2020-12: {exc.message}"
        ) from exc
    errors = sorted(
        Draft202012Validator(schema).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        rendered = []
        for error in errors:
            location = "/".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise ManifestError(
            "Skill relationship contract schema validation failed: " + "; ".join(rendered)
        )
    if value.get("schema_version") != _SCHEMA:
        raise ManifestError("Skill relationship contract has unsupported schema")
    if value.get("identity_source") != "manifest.json":
        raise ManifestError("Skill relationship identity_source must be manifest.json")
    if value.get("skill_semantics_source") != "manifests/skill_content_contracts_v2.json":
        raise ManifestError("Skill relationship semantics must come from Skill Content v2")
    types = value.get("relationship_types")
    if not isinstance(types, dict) or set(types) != _ALLOWED_TYPES:
        raise ManifestError("Skill relationship types must be the canonical four-type set")
    for name, spec in types.items():
        if not isinstance(spec, dict):
            raise ManifestError(f"Skill relationship type is malformed: {name}")
        expected = name == "delivery-precedence"
        if spec.get("sequencing_authority") is not expected:
            raise ManifestError(
                f"Only delivery-precedence may have sequencing authority: {name}"
            )
    return value


def _contract(manifest: Manifest) -> tuple[Mapping[str, Any], str]:
    path = manifest.root / _CONTRACT
    schema_path = manifest.root / _CONTRACT_SCHEMA
    if not path.is_file():
        raise ManifestError(f"Skill relationship contract is missing: {_CONTRACT}")
    if not schema_path.is_file():
        raise ManifestError(f"Skill relationship schema is missing: {_CONTRACT_SCHEMA}")
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
    return value, hashlib.sha256(path.read_bytes()).hexdigest()


def _entries(manifest: Manifest) -> Dict[str, Mapping[str, Any]]:
    rows: Dict[str, Mapping[str, Any]] = {}
    for section in ("skills", "optional_skills"):
        values = manifest.data.get(section, [])
        if not isinstance(values, list):
            raise ManifestError(f"manifest {section} must be an array")
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                continue
            name = str(item["name"])
            if name in rows:
                raise ManifestError(f"duplicate Skill identity in manifest: {name}")
            rows[name] = item
    return rows


def _assert_acyclic(graph: Mapping[str, Sequence[str]], label: str) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def walk(node: str, chain: tuple[str, ...]) -> None:
        if node in visited:
            return
        if node in visiting:
            raise ManifestError(f"{label} cycle: " + " -> ".join(chain + (node,)))
        visiting.add(node)
        for target in graph.get(node, ()):
            walk(target, chain + (node,))
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        walk(node, ())


def _explicit_relationships(
    contract: Mapping[str, Any],
    entries: Mapping[str, Mapping[str, Any]],
) -> list[Dict[str, Any]]:
    raw = contract.get("relationships")
    if not isinstance(raw, list):
        raise ManifestError("Skill relationship relationships must be an array")
    names = set(entries)
    seen: set[tuple[str, str, str]] = set()
    rows: list[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ManifestError("Skill relationship entry must be an object")
        source = item.get("from")
        target = item.get("to")
        relation = item.get("type")
        requirement = item.get("requirement")
        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or relation not in _ALLOWED_TYPES
            or requirement not in {"required", "when-applicable"}
        ):
            raise ManifestError("Skill relationship entry is malformed")
        if source not in names or target not in names:
            raise ManifestError(f"Skill relationship endpoint is unknown: {source} -> {target}")
        if source == target:
            raise ManifestError(f"Skill relationship self edge is forbidden: {source}")
        key = (source, target, str(relation))
        if key in seen:
            raise ManifestError(f"duplicate typed Skill relationship: {key}")
        seen.add(key)
        rows.append(
            {
                "from": source,
                "to": target,
                "type": relation,
                "requirement": requirement,
                "source": _CONTRACT,
            }
        )
    return rows


def _resolve_delivery_lifecycle(
    manifest: Manifest,
    contract: Mapping[str, Any],
    entries: Mapping[str, Mapping[str, Any]],
    relationships: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    lifecycle = contract.get("delivery_lifecycle")
    if not isinstance(lifecycle, dict):
        raise ManifestError("Skill relationship delivery_lifecycle is missing")
    requirements = lifecycle.get("pre_review_requirements")
    if requirements != ["verification-evidence"]:
        raise ManifestError("Delivery lifecycle must require verification evidence before review")
    steps = lifecycle.get("steps")
    if not isinstance(steps, list) or len(steps) != len(_EXPECTED_STAGES):
        raise ManifestError("Delivery lifecycle must define exactly four terminal stages")

    resolved: list[Dict[str, Any]] = []
    last_order = -1
    stages: list[str] = []
    for raw in steps:
        if not isinstance(raw, dict):
            raise ManifestError("Delivery lifecycle step must be an object")
        order = raw.get("order")
        stage = raw.get("stage")
        skill = raw.get("skill")
        expected_role = raw.get("expected_runtime_role")
        if (
            not isinstance(order, int)
            or not isinstance(stage, str)
            or not isinstance(skill, str)
            or not isinstance(expected_role, str)
        ):
            raise ManifestError("Delivery lifecycle step is malformed")
        if order <= last_order:
            raise ManifestError("Delivery lifecycle order must be strictly increasing")
        last_order = order
        stages.append(stage)
        if skill not in entries:
            raise ManifestError(f"Delivery lifecycle references unknown Skill: {skill}")
        metadata = resolve_skill_content(manifest, skill)
        if metadata["runtime_role"] != expected_role:
            raise ManifestError(
                f"Delivery lifecycle role drift: {skill} "
                f"expected={expected_role} actual={metadata['runtime_role']}"
            )
        resolved.append(
            {
                "order": order,
                "stage": stage,
                "name": skill,
                "path": entries[skill]["path"],
                "runtime_role": metadata["runtime_role"],
                "selection_group": metadata["selection_group"],
            }
        )

    if tuple(stages) != _EXPECTED_STAGES:
        raise ManifestError(
            "Delivery lifecycle stage order must be review -> completion -> commit-pr -> closeout"
        )

    adjacent = {
        (resolved[index]["name"], resolved[index + 1]["name"])
        for index in range(len(resolved) - 1)
    }
    precedence = {
        (str(row["from"]), str(row["to"]))
        for row in relationships
        if row["type"] == "delivery-precedence" and row["requirement"] == "required"
    }
    if precedence != adjacent:
        raise ManifestError(
            "Required delivery-precedence edges must exactly match adjacent terminal lifecycle steps"
        )
    graph: Dict[str, list[str]] = {name: [] for name in entries}
    for source, target in precedence:
        graph[source].append(target)
    _assert_acyclic(graph, "delivery precedence")

    return {
        "schema": _LIFECYCLE_SCHEMA,
        "status": "pass",
        "pre_review_requirements": requirements,
        "relationship_semantics_source": _CONTRACT,
        "steps": resolved,
    }


def resolve_skill_relationships(manifest: Manifest) -> Dict[str, Any]:
    contract, digest = _contract(manifest)
    entries = _entries(manifest)
    relationships = _explicit_relationships(contract, entries)
    lifecycle = _resolve_delivery_lifecycle(manifest, contract, entries, relationships)
    return {
        "schema": _RESOLUTION_SCHEMA,
        "status": "pass",
        "contract_path": _CONTRACT,
        "contract_sha256": digest,
        "identity_source": "manifest.json",
        "skill_semantics_source": "manifests/skill_content_contracts_v2.json",
        "relationship_count": len(relationships),
        "typed_relationships": relationships,
        "delivery_lifecycle": lifecycle,
    }


def resolve_delivery_lifecycle(manifest: Manifest) -> Dict[str, Any]:
    result = resolve_skill_relationships(manifest)
    lifecycle = dict(result["delivery_lifecycle"])
    lifecycle["contract_sha256"] = result["contract_sha256"]
    return lifecycle


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="skill-relationships")
    parser.add_argument("--root", default=None)
    parser.add_argument("--lifecycle", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path.cwd().resolve()
    try:
        manifest = Manifest.load(root)
        result = (
            resolve_delivery_lifecycle(manifest)
            if args.lifecycle
            else resolve_skill_relationships(manifest)
        )
    except ManifestError as exc:
        print(json.dumps({"schema": _RESOLUTION_SCHEMA, "status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.lifecycle:
        for item in result["steps"]:
            print(f"{item['order']}\t{item['stage']}\t{item['runtime_role']}\t{item['name']}\t{item['path']}")
    else:
        for item in result["typed_relationships"]:
            print(f"{item['type']}\t{item['requirement']}\t{item['from']}\t{item['to']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
