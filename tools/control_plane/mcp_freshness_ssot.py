#!/usr/bin/env python3
"""Fail-closed MCP dependency freshness authority validation.

The dependency manifest may retain compatibility snapshot fields for older
consumers, but review_source_ref is the sole freshness authority. Canonical
source metadata lives in the existing official/external source registries.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping


def _load(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _canonical_sources(root: Path) -> tuple[Dict[str, List[Mapping[str, Any]]], list[str]]:
    """Index canonical rows without inventing a cross-registry uniqueness rule.

    The two pre-existing registries intentionally overlap for some reviewed
    sources. A dependency ref is valid only when it resolves to exactly one
    row. Therefore an unused overlap is harmless, while a referenced overlap
    remains fail-closed as ambiguous.
    """

    official = _load(root / "manifests" / "official_docs_freshness_gates.json")
    external = _load(root / "manifests" / "external_agent_pattern_contracts.json")
    index: Dict[str, List[Mapping[str, Any]]] = {}
    failures: list[str] = []
    for registry_name, rows in (
        ("official_docs_freshness_gates.json#sources", official.get("sources", [])),
        ("external_agent_pattern_contracts.json#source_refs", external.get("source_refs", [])),
    ):
        if not isinstance(rows, list):
            failures.append(f"canonical registry is not an array: {registry_name}")
            continue
        seen_in_registry: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                failures.append(f"canonical registry row is not an object: {registry_name}")
                continue
            source_id = row.get("id")
            if not isinstance(source_id, str) or not source_id:
                failures.append(f"canonical registry row missing id: {registry_name}")
                continue
            if source_id in seen_in_registry:
                failures.append(f"canonical source id duplicated within registry: {registry_name}:{source_id}")
                continue
            seen_in_registry.add(source_id)
            index.setdefault(source_id, []).append(row)
    return index, failures


def validate(root: Path, as_of: date) -> Dict[str, Any]:
    root = root.resolve()
    manifest = _load(root / "manifests" / "skill_mcp_dependencies.json")
    policy = manifest.get("external_dependency_provenance_policy", {})
    authority = policy.get("freshness_authority", {}) if isinstance(policy, dict) else {}
    sources, failures = _canonical_sources(root)

    if authority.get("mode") != "canonical-source-ref":
        failures.append("freshness_authority.mode must be canonical-source-ref")
    if authority.get("compatibility_snapshots_authoritative") is not False:
        failures.append("compatibility freshness snapshots must be non-authoritative")
    if authority.get("source_id_collision_action") != "fail":
        failures.append("referenced source id ambiguity must fail closed")
    if authority.get("expired_source_action") != "fail":
        failures.append("expired canonical sources must fail closed")
    expected_registries = {
        "manifests/official_docs_freshness_gates.json#sources",
        "manifests/external_agent_pattern_contracts.json#source_refs",
    }
    if set(authority.get("registries", [])) != expected_registries:
        failures.append("freshness authority must use exactly the two canonical source registries")

    dependencies = manifest.get("dependencies", [])
    if not isinstance(dependencies, list) or not dependencies:
        failures.append("MCP dependencies must be a non-empty array")
        dependencies = []

    resolved = 0
    canonical_current = 0
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            failures.append("MCP dependency must be an object")
            continue
        server = str(dependency.get("mcp_server", "<missing>"))
        provenance = dependency.get("provenance", {})
        if not isinstance(provenance, dict):
            failures.append(f"{server}: provenance must be an object")
            continue
        source_ref = provenance.get("review_source_ref")
        mode = provenance.get("review_source_mode")
        if not isinstance(source_ref, str) or not source_ref:
            failures.append(f"{server}: review_source_ref is required")
            continue
        matches = sources.get(source_ref, [])
        if len(matches) != 1:
            failures.append(
                f"{server}: review_source_ref must resolve exactly once: {source_ref} matches={len(matches)}"
            )
            continue
        source = matches[0]
        resolved += 1

        for field in ("url", "retrieved_at", "review_status", "expires_at"):
            if not isinstance(source.get(field), str) or not source.get(field):
                failures.append(f"{server}: canonical source {source_ref} missing {field}")
        try:
            retrieved_at = date.fromisoformat(str(source.get("retrieved_at", "")))
            expires_at = date.fromisoformat(str(source.get("expires_at", "")))
        except ValueError:
            failures.append(f"{server}: canonical source {source_ref} has invalid freshness dates")
            continue
        if expires_at <= retrieved_at:
            failures.append(f"{server}: canonical source {source_ref} expires_at must follow retrieved_at")
        if expires_at < as_of:
            failures.append(
                f"{server}: canonical source {source_ref} expired at {expires_at.isoformat()} before {as_of.isoformat()}"
            )

        if mode == "canonical-current":
            canonical_current += 1
            compatibility = {
                "source_url": source.get("url"),
                "retrieved_at": source.get("retrieved_at"),
                "review_status": source.get("review_status"),
                "expires_at": source.get("expires_at"),
            }
            for field, expected in compatibility.items():
                if provenance.get(field) != expected:
                    failures.append(
                        f"{server}: compatibility snapshot {field} diverges from canonical source {source_ref}"
                    )
        elif mode == "template-reference":
            if dependency.get("required") is not False:
                failures.append(f"{server}: template-reference dependency must be optional")
            if dependency.get("enabled_tools") != []:
                failures.append(f"{server}: template-reference dependency must expose no tools")
            if not str(provenance.get("trust_decision", "")).startswith("deny"):
                failures.append(f"{server}: template-reference dependency must remain deny-by-default")
            for field in (
                "source_url",
                "registry_namespace",
                "namespace_verification",
                "package_version",
                "artifact_digest",
            ):
                if provenance.get(field) != "declare-before-enable":
                    failures.append(f"{server}: template-reference {field} must remain declare-before-enable")
        else:
            failures.append(f"{server}: unknown review_source_mode: {mode}")

    if canonical_current == 0:
        failures.append("at least one current MCP dependency must use canonical-current freshness")

    return {
        "schema": "adk-mcp-freshness-ssot/v1",
        "status": "pass" if not failures else "fail",
        "as_of": as_of.isoformat(),
        "dependencies": len(dependencies),
        "resolved_sources": resolved,
        "canonical_current_dependencies": canonical_current,
        "authority": "canonical-source-ref",
        "compatibility_snapshots_authoritative": False,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--as-of")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    try:
        report = validate(Path(args.root), as_of)
    except ValueError as exc:
        report = {
            "schema": "adk-mcp-freshness-ssot/v1",
            "status": "fail",
            "as_of": as_of.isoformat(),
            "failures": [str(exc)],
        }
    if args.summary_json:
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
