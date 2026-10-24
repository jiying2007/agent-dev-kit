"""Validation for the existing release-manifest schema v2.

The release builder remains responsible for assembly. This module is the
bounded contract verifier used after assembly and before provenance attestation.
After source verification, a private temporary source copy is rendered by the
already-loaded compiler; archive Python code is never imported or executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from jsonschema import Draft202012Validator

from agent_dev_kit.compiler import export_manifest
from agent_dev_kit.contracts.schema_loader import packaged_schema_bytes
from agent_dev_kit.model import Manifest, canonical_json_bytes
from agent_dev_kit.targets import RenderBudget, _render_historical_selection

from ..strict_json import StrictJSONError
from ..strict_json import loads as load_strict_json
from ..strict_json import read as read_strict_json
from . import archive_io
from .archive_io import inspect_archive_snapshot, load_archive_snapshot

_SCHEMA_NAME = "release-manifest-v2.schema.json"
_MAX_JSON_BYTES = 8 * 1024 * 1024


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _format_error(error: Any) -> str:
    path = ".".join(str(item) for item in error.absolute_path)
    return f"{path}: {error.message}" if path else str(error.message)


def validate_release_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate release-manifest/v2 structure and cross-field invariants."""

    schema = json.loads(packaged_schema_bytes(_SCHEMA_NAME).decode("utf-8"))
    validator = Draft202012Validator(schema)
    failures = sorted(_format_error(item) for item in validator.iter_errors(dict(value)))

    provenance = value.get("source_provenance")
    if isinstance(provenance, Mapping) and value.get("release_eligible") != provenance.get("release_eligible"):
        failures.append("release_eligible must match source_provenance.release_eligible")
    if value.get("reproducible") != value.get("release_eligible"):
        failures.append("reproducible must match release_eligible")

    return {
        "schema": "adk-release-manifest-validation/v1",
        "status": "pass" if not failures else "fail",
        "version": value.get("version"),
        "failures": sorted(set(failures)),
    }


def _canonical_manifest_sha256(raw: bytes) -> str:
    try:
        value = load_strict_json(raw, max_bytes=_MAX_JSON_BYTES)
    except StrictJSONError as exc:
        raise ValueError("manifest.json is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest.json root must be an object")
    return _sha256(canonical_json_bytes(value))


def _offline_render_schema(path: Path) -> None:
    """Do not allow archived schema data to initiate reference network requests."""
    schema = read_strict_json(path, regular_only=True)
    pending = [schema]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if value is not schema and ("$id" in value or isinstance(value.get("id"), str)):
                raise ValueError("release bundle source schema has a nested reference scope")
            for key in ("$ref", "$dynamicRef", "$recursiveRef"):
                reference = value.get(key)
                if reference is not None and (not isinstance(reference, str) or not reference.startswith("#")):
                    raise ValueError("release bundle source schema must use local references")
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)


def _validate_bundles(
    raw: bytes,
    release_manifest: Mapping[str, Any],
    actual: Mapping[str, tuple[str | None, int]],
) -> None:
    """Reproduce bundle bytes from the verified source, never its declared hashes."""
    expected: dict[str, tuple[str, int]] = {}
    targets = []
    budget = RenderBudget(max_bytes=archive_io.MAX_DECODED_BYTES,
                          max_file_bytes=archive_io.MAX_MEMBER_BYTES,
                          max_files=archive_io.MAX_MEMBERS,
                          max_name_bytes=archive_io.MAX_NAME_BYTES)
    with tempfile.TemporaryDirectory(prefix="adk-release-bundles-") as temporary:
        source_root = Path(temporary) / "source"
        inspect_archive_snapshot(raw, source_directory=source_root)
        for name in ("manifest.schema.json", "target-contract.schema.json"):
            _offline_render_schema(source_root / "manifests" / name)
        native_schema = source_root / "schemas" / "native-target-conformance-receipt-v2.schema.json"
        if native_schema.exists():
            _offline_render_schema(native_schema)
        manifest = Manifest.load(source_root)
        for target in sorted(manifest.direct_targets()):
            prefix = "bundles/" + target + "/"
            budget.check_name(prefix)
            config = manifest.target(target)
            kinds = config.get("supported_asset_kinds", [])
            kind = kinds[0] if isinstance(kinds, list) and len(kinds) == 1 else None
            bundle = _render_historical_selection(
                manifest, target, ["embedded-fullstack"], (), kind, budget=budget, allow_native_verifier=False,
            )
            for rendered in bundle.files:
                name = prefix + rendered.destination
                budget.check_name(name)
                expected[name] = (rendered.sha256, rendered.mode)
            inventory = budget.file_buffer()
            for chunk in json.JSONEncoder(ensure_ascii=False, indent=2).iterencode(export_manifest(manifest, bundle)):
                inventory.write(chunk)
            inventory.write("\n")
            inventory_name = prefix + "adk-export-manifest.json"
            budget.check_name(inventory_name)
            expected[inventory_name] = (_sha256(inventory.finish()), 0o644)
            targets.append({"target": target, "agents": bundle.agent_count, "skills": bundle.skill_count})
        if sorted(release_manifest["direct_targets"], key=lambda value: value["target"]) != targets:
            raise ValueError("release bundle target counts differ from source renderer")
    directories = {
        parent.as_posix() for name in expected for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    files = {name: value for name, value in actual.items() if value[0] is not None}
    if files != expected:
        raise ValueError("release bundle files, bytes or modes differ from source renderer")
    if any(name not in directories or value != (None, 0o755)
           for name, value in actual.items() if value[0] is None):
        raise ValueError("release bundle directories differ from source renderer")


def validate_release_artifact(artifact: Path, *, raw_snapshot: bytes | None = None) -> dict[str, Any]:
    """Validate archive identities and every bundle against its verified source."""

    source_inventory: dict[str, Any] = {}
    bundle_inventory: dict[str, tuple[str | None, int]] = {}
    if raw_snapshot is None:
        raw, payloads = load_archive_snapshot(artifact, source_inventory=source_inventory,
                                             bundle_inventory=bundle_inventory)
    else:
        raw = raw_snapshot
        payloads = inspect_archive_snapshot(raw, source_inventory=source_inventory,
                                            bundle_inventory=bundle_inventory)
    release_bytes = payloads["release-manifest.json"]
    try:
        release_manifest = load_strict_json(release_bytes, max_bytes=_MAX_JSON_BYTES)
    except StrictJSONError as exc:
        raise ValueError("release-manifest.json is not valid UTF-8 JSON") from exc
    if not isinstance(release_manifest, dict):
        raise ValueError("release-manifest.json root must be an object")

    validation = validate_release_manifest(release_manifest)
    if validation["status"] != "pass":
        raise ValueError("release manifest validation failed: " + "; ".join(validation["failures"]))

    version = str(release_manifest["version"])
    if artifact.name != f"agent-dev-kit-{version}.tar.gz":
        raise ValueError("release artifact filename does not match manifest version")

    sbom_name = str(release_manifest["sbom"]["path"])
    sbom_bytes = payloads[sbom_name]
    sbom_sha = _sha256(sbom_bytes)
    if sbom_sha != release_manifest["sbom"]["sha256"]:
        raise ValueError("release SBOM digest does not match release manifest")

    source_manifest_bytes = payloads.get("source/manifest.json")
    if source_manifest_bytes is None:
        raise ValueError("release archive is missing its source manifest")
    source_manifest_sha = _canonical_manifest_sha256(source_manifest_bytes)
    if source_manifest_sha != _canonical_manifest_sha256(payloads["manifest.json"]):
        raise ValueError("release top-level and source manifests differ")
    if load_strict_json(source_manifest_bytes, max_bytes=_MAX_JSON_BYTES).get("version") != version:
        raise ValueError("release source manifest version does not match release version")
    if source_manifest_sha != release_manifest["manifest_sha256"]:
        raise ValueError("release manifest source manifest digest does not match archive")
    if source_inventory["file_count"] != release_manifest["source_file_count"]:
        raise ValueError("release source file count does not match archive")
    if source_inventory["sha256"] != release_manifest["source_provenance"]["source_distribution_sha256"]:
        raise ValueError("release source distribution digest does not match archive")
    try:
        _validate_bundles(raw, release_manifest, bundle_inventory)
    except (OSError, ValueError):
        raise
    except Exception as exc:
        # Archive-controlled schemas can raise reference-library exceptions or
        # recursion errors. Keep these at the public malformed-input boundary,
        # retaining the original cause for programmatic diagnostics.
        raise ValueError("release bundle source could not be rendered safely") from exc

    return {
        "schema": "adk-release-artifact-contract/v1",
        "status": "pass",
        "version": version,
        "artifact": artifact.name,
        "artifact_sha256": _sha256(raw),
        "release_manifest_sha256": _sha256(release_bytes),
        "manifest_sha256": source_manifest_sha,
        "sbom_sha256": sbom_sha,
        "release_eligible": bool(release_manifest["release_eligible"]),
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an agent-dev-kit release artifact")
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    results = []
    try:
        for artifact in args.artifacts:
            results.append(validate_release_artifact(artifact))
    except (OSError, tarfile.TarError, ValueError) as exc:
        print(json.dumps({"schema": "adk-release-artifact-contract/v1", "status": "fail", "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {"schema": "adk-release-artifact-contract-set/v1", "status": "pass", "artifacts": results},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
