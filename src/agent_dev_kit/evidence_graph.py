"""Strict, sanitized evidence graph validation for ADK lifecycle provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Set

from jsonschema import Draft202012Validator, FormatChecker

from .model import ManifestError
from .privacy_ref import (
    validate_evidence_ref,
    validate_identifier,
    validate_no_secrets,
    validate_sha256,
)


CONTRACT_SCHEMA = "adk-evidence-graph-contract/v1"
GRAPH_SCHEMA = "adk-evidence-graph/v1"
NODE_CLAIM_SCHEMA = "adk-evidence-node-claim/v1"
GRAPH_FIELDS = {
    "schema_version",
    "graph_id",
    "graph_kind",
    "generated_at",
    "nodes",
    "edges",
    "raw_content_stored",
}
NODE_FIELDS = {
    "node_id",
    "node_type",
    "content_sha256",
    "evidence_ref",
    "evidence_layer",
    "owner",
    "verified_at",
    "expires_at",
    "sensitivity",
    "retention",
    "attributes",
}
EDGE_FIELDS = {"from", "to", "relation"}
DEFAULT_GRAPH_SCHEMA_PACKAGE = "agent_dev_kit.schema_resources"
DEFAULT_GRAPH_SCHEMA_NAME = "evidence-graph-v1.schema.json"
DEFAULT_NODE_CLAIM_SCHEMA_NAME = "evidence-node-claim-v1.schema.json"


def _load(path: Path, label: str) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid: {}".format(label, exc)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} must be an object".format(label))
    return dict(value)


def load_contract(path: Path) -> Dict[str, Any]:
    value = _load(path, "evidence graph contract")
    required = {
        "schema_version",
        "graph_schema_version",
        "graph_schema_path",
        "last_updated",
        "boundary",
        "allowed_graph_kinds",
        "allowed_node_types",
        "allowed_evidence_layers",
        "node_layer_map",
        "allowed_sensitivity",
        "allowed_retention",
        "allowed_edges",
        "required_outcome_metrics",
        "must_not",
    }
    if set(value) != required or value.get("schema_version") != CONTRACT_SCHEMA:
        raise ManifestError("evidence graph contract fields or schema are invalid")
    if value.get("graph_schema_version") != GRAPH_SCHEMA:
        raise ManifestError("evidence graph contract must target {}".format(GRAPH_SCHEMA))
    if value.get("graph_schema_path") != "schemas/evidence-graph-v1.schema.json":
        raise ManifestError("evidence graph contract schema path is invalid")
    for field in (
        "allowed_node_types",
        "allowed_graph_kinds",
        "allowed_evidence_layers",
        "allowed_sensitivity",
        "allowed_retention",
        "required_outcome_metrics",
        "must_not",
    ):
        items = value.get(field)
        if not isinstance(items, list) or not items or any(not isinstance(item, str) or not item for item in items):
            raise ManifestError("{} must be a non-empty string array".format(field))
        if len(items) != len(set(items)):
            raise ManifestError("{} must not contain duplicates".format(field))
    edges = value.get("allowed_edges")
    if not isinstance(edges, list) or not edges:
        raise ManifestError("allowed_edges must be a non-empty array")
    known_types = set(value["allowed_node_types"])
    seen_edges = set()
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != EDGE_FIELDS:
            raise ManifestError("allowed edge fields are invalid")
        signature = (edge["from"], edge["to"], edge["relation"])
        if edge["from"] not in known_types or edge["to"] not in known_types or signature in seen_edges:
            raise ManifestError("allowed edge is invalid or duplicated")
        seen_edges.add(signature)
    layer_map = value.get("node_layer_map")
    if not isinstance(layer_map, dict) or set(layer_map) != known_types:
        raise ManifestError("node_layer_map must define every node type")
    allowed_layers = set(value["allowed_evidence_layers"])
    for node_type, layers in layer_map.items():
        if (
            not isinstance(layers, list)
            or not layers
            or any(layer not in allowed_layers for layer in layers)
            or len(layers) != len(set(layers))
        ):
            raise ManifestError("node_layer_map entry is invalid: {}".format(node_type))
    return value


def _timestamp(value: Any, label: str, *, nullable: bool = False) -> Optional[datetime]:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ManifestError("{} must be an ISO timestamp".format(label))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ManifestError("{} must be an ISO timestamp".format(label)) from exc
    if parsed.tzinfo is None:
        raise ManifestError("{} must include a timezone".format(label))
    return parsed


def _validate_schema(value: Any, schema_path: Optional[Path]) -> None:
    try:
        raw = (
            schema_path.read_text(encoding="utf-8")
            if schema_path is not None
            else resources.read_text(
                DEFAULT_GRAPH_SCHEMA_PACKAGE,
                DEFAULT_GRAPH_SCHEMA_NAME,
                encoding="utf-8",
            )
        )
        schema = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("evidence graph schema is invalid: {}".format(exc)) from exc
    if not isinstance(schema, dict):
        raise ManifestError("evidence graph schema must be an object")
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ManifestError("evidence graph schema failed at {}: {}".format(location, errors[0].message))


def _node_claim_schema() -> Dict[str, Any]:
    try:
        value = json.loads(
            resources.read_text(
                DEFAULT_GRAPH_SCHEMA_PACKAGE,
                DEFAULT_NODE_CLAIM_SCHEMA_NAME,
                encoding="utf-8",
            )
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("evidence node claim schema is invalid: {}".format(exc)) from exc
    if not isinstance(value, dict):
        raise ManifestError("evidence node claim schema must be an object")
    return value


def _validate_node_claim(
    claim_path: Path,
    node: Mapping[str, Any],
    evidence_root: Path,
    *,
    verified_at: datetime,
    evaluated_at: datetime,
) -> None:
    claim = _load(claim_path, "evidence node claim")
    validate_no_secrets(claim, "evidence node claim")
    errors = sorted(
        Draft202012Validator(
            _node_claim_schema(), format_checker=FormatChecker()
        ).iter_errors(claim),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        location = "/".join(str(part) for part in errors[0].absolute_path) or "<root>"
        raise ManifestError(
            "evidence node claim schema failed at {}: {}".format(location, errors[0].message)
        )
    if (
        claim.get("schema_version") != NODE_CLAIM_SCHEMA
        or claim.get("node_id") != node.get("node_id")
        or claim.get("node_type") != node.get("node_type")
        or claim.get("evidence_layer") != node.get("evidence_layer")
    ):
        raise ManifestError("evidence node claim identity does not match its graph node")
    generated_at = _timestamp(claim.get("generated_at"), "evidence node claim generated_at")
    if generated_at is None or generated_at > verified_at or generated_at > evaluated_at:
        raise ManifestError("evidence node claim must exist before node verification")
    subject_path = validate_evidence_ref(
        claim.get("subject_ref"),
        evidence_root,
        "evidence node claim subject_ref",
    )
    if subject_path == claim_path or subject_path.suffix != ".json":
        raise ManifestError("evidence node claim must reference a separate typed JSON subject")
    subject = _load(subject_path, "evidence node claim subject")
    validate_no_secrets(subject, "evidence node claim subject")


def _ensure_acyclic(adjacency: Mapping[str, Set[str]]) -> None:
    visiting: Set[str] = set()
    visited: Set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ManifestError("evidence graph must be acyclic")
        if node in visited:
            return
        visiting.add(node)
        for target in adjacency.get(node, set()):
            visit(target)
        visiting.remove(node)
        visited.add(node)

    for node in adjacency:
        visit(node)


def _has_path(adjacency: Mapping[str, Set[str]], starts: Set[str], targets: Set[str]) -> bool:
    pending = list(starts)
    visited: Set[str] = set()
    while pending:
        node = pending.pop()
        if node in targets:
            return True
        if node in visited:
            continue
        visited.add(node)
        pending.extend(adjacency.get(node, set()) - visited)
    return False


def _validate_attributes(node_id: str, node_type: str, attributes: Any, contract: Mapping[str, Any]) -> None:
    if not isinstance(attributes, dict):
        raise ManifestError("node {} attributes must be an object".format(node_id))
    if node_type != "outcome":
        if attributes:
            raise ManifestError("node {} attributes are not allowed for node_type {}".format(node_id, node_type))
        return
    required = set(contract["required_outcome_metrics"])
    if set(attributes) != required:
        raise ManifestError("outcome node {} metrics must match the strict contract".format(node_id))
    boolean_fields = {"task_success", "first_pass_success", "wrong_skill", "abstained"}
    integer_fields = required - boolean_fields
    for field in boolean_fields:
        if not isinstance(attributes[field], bool):
            raise ManifestError("outcome node {} {} must be boolean".format(node_id, field))
    for field in integer_fields:
        value = attributes[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ManifestError("outcome node {} {} must be a non-negative integer".format(node_id, field))


def validate_graph(
    value: Any,
    contract: Mapping[str, Any],
    evidence_root: Path,
    *,
    as_of: Optional[datetime] = None,
    schema_path: Optional[Path] = None,
) -> Dict[str, Any]:
    _validate_schema(value, schema_path)
    if not isinstance(value, dict) or set(value) != GRAPH_FIELDS:
        raise ManifestError("evidence graph fields are invalid")
    validate_no_secrets(value, "evidence graph")
    evidence_root = evidence_root.resolve()
    if not evidence_root.is_dir():
        raise ManifestError("evidence root must be an existing directory")
    evaluated_at = as_of or datetime.now(timezone.utc)
    if evaluated_at.tzinfo is None:
        raise ManifestError("as_of must include a timezone")
    if value.get("schema_version") != GRAPH_SCHEMA:
        raise ManifestError("unsupported evidence graph schema")
    graph_id = validate_identifier(value.get("graph_id"), "graph_id")
    generated_at = _timestamp(value.get("generated_at"), "generated_at")
    if generated_at is None or generated_at > evaluated_at:
        raise ManifestError("generated_at must not be in the future")
    graph_kind = value.get("graph_kind")
    if graph_kind not in contract["allowed_graph_kinds"]:
        raise ManifestError("evidence graph graph_kind is invalid")
    if value.get("raw_content_stored") is not False:
        raise ManifestError("evidence graph must not store raw content")
    nodes = value.get("nodes")
    edges = value.get("edges")
    if not isinstance(nodes, list) or not nodes or not isinstance(edges, list):
        raise ManifestError("evidence graph nodes must be non-empty and edges must be an array")

    allowed_types = set(contract["allowed_node_types"])
    allowed_layers = set(contract["allowed_evidence_layers"])
    allowed_sensitivity = set(contract["allowed_sensitivity"])
    allowed_retention = set(contract["allowed_retention"])
    node_types: Dict[str, str] = {}
    node_retentions: Dict[str, str] = {}
    claim_paths: Set[Path] = set()
    for node in nodes:
        if not isinstance(node, dict) or set(node) != NODE_FIELDS:
            raise ManifestError("evidence graph node fields are invalid")
        node_id = validate_identifier(node.get("node_id"), "node_id")
        if node_id in node_types:
            raise ManifestError("duplicate evidence graph node_id")
        node_type = node.get("node_type")
        if node_type not in allowed_types:
            raise ManifestError("node {} has an invalid node_type".format(node_id))
        digest = validate_sha256(node.get("content_sha256"), "node {} content_sha256".format(node_id))
        if node.get("evidence_layer") not in allowed_layers:
            raise ManifestError("node {} evidence_layer is invalid".format(node_id))
        if node.get("evidence_layer") not in contract["node_layer_map"][node_type]:
            raise ManifestError("node {} evidence_layer is invalid for node_type {}".format(node_id, node_type))
        validate_identifier(node.get("owner"), "node {} owner".format(node_id))
        verified_at = _timestamp(node.get("verified_at"), "node {} verified_at".format(node_id))
        expires_at = _timestamp(node.get("expires_at"), "node {} expires_at".format(node_id), nullable=True)
        if verified_at is None or verified_at > evaluated_at:
            raise ManifestError("node {} verified_at must not be in the future".format(node_id))
        if expires_at is not None and verified_at > expires_at:
            raise ManifestError("node {} verified_at must not exceed expires_at".format(node_id))
        if node.get("sensitivity") not in allowed_sensitivity:
            raise ManifestError("node {} sensitivity is invalid".format(node_id))
        if node.get("retention") not in allowed_retention:
            raise ManifestError("node {} retention is invalid".format(node_id))
        if node.get("retention") == "expire" and (expires_at is None or expires_at <= evaluated_at):
            raise ManifestError("node {} expire retention requires a future expires_at".format(node_id))
        claim_path = validate_evidence_ref(
            node.get("evidence_ref"),
            evidence_root,
            "node {} evidence_ref".format(node_id),
            expected_sha256=digest,
        )
        if claim_path in claim_paths:
            raise ManifestError("evidence graph nodes require independent typed claim files")
        claim_paths.add(claim_path)
        _validate_node_claim(
            claim_path,
            node,
            evidence_root,
            verified_at=verified_at,
            evaluated_at=evaluated_at,
        )
        _validate_attributes(node_id, node_type, node.get("attributes"), contract)
        node_types[node_id] = node_type
        node_retentions[node_id] = str(node["retention"])

    allowed_edges = {
        (item["from"], item["to"], item["relation"])
        for item in contract["allowed_edges"]
    }
    adjacency: Dict[str, Set[str]] = {node_id: set() for node_id in node_types}
    seen_edges = set()
    relations_by_source: Dict[str, Set[str]] = {node_id: set() for node_id in node_types}
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != EDGE_FIELDS:
            raise ManifestError("evidence graph edge fields are invalid")
        source = edge.get("from")
        target = edge.get("to")
        relation = edge.get("relation")
        if source not in node_types or target not in node_types:
            raise ManifestError("evidence graph contains a dangling edge")
        signature = (source, target, relation)
        if signature in seen_edges:
            raise ManifestError("evidence graph contains a duplicate edge")
        seen_edges.add(signature)
        type_signature = (node_types[source], node_types[target], relation)
        if type_signature not in allowed_edges:
            raise ManifestError("evidence graph edge type is not allowed")
        adjacency[source].add(target)
        relations_by_source[source].add(str(relation))
    _ensure_acyclic(adjacency)
    for node_id, retention in node_retentions.items():
        required_relation = {"supersede": "superseded-by", "retire": "retired-by"}.get(retention)
        if required_relation is not None and required_relation not in relations_by_source[node_id]:
            raise ManifestError(
                "node {} retention {} requires {} edge".format(node_id, retention, required_relation)
            )
    if graph_kind == "release-evidence":
        required_types = {"source", "decision", "asset", "bundle", "runtime", "trace", "outcome", "release"}
        missing_types = required_types - set(node_types.values())
        if missing_types:
            raise ManifestError("release evidence graph is missing required node types")
        source_nodes = {node_id for node_id, node_type in node_types.items() if node_type == "source"}
        release_nodes = {node_id for node_id, node_type in node_types.items() if node_type == "release"}
        if not edges or not _has_path(adjacency, source_nodes, release_nodes):
            raise ManifestError("release evidence graph requires a source-to-release path")

    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": GRAPH_SCHEMA,
        "status": "pass" if graph_kind == "release-evidence" else "partial",
        "graph_id": graph_id,
        "graph_kind": graph_kind,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "graph_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "raw_content_stored": False,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="evidence-graph")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--as-of")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        as_of = _timestamp(args.as_of, "as_of") if args.as_of else None
        result = validate_graph(
            _load(args.input, "evidence graph"),
            load_contract(args.contract),
            args.evidence_root,
            as_of=as_of,
        )
    except ManifestError as exc:
        print("[FAIL] {}".format(exc))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")) if args.summary_json else json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
