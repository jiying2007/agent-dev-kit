"""Validation for the existing release-manifest schema v2.

The release builder remains responsible for assembly. This module is the
bounded contract verifier used after assembly and before provenance attestation.
It never extracts archive members to disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from agent_dev_kit.contracts.schema_loader import packaged_schema_bytes
from agent_dev_kit.model import canonical_json_bytes

from ..strict_json import StrictJSONError
from ..strict_json import loads as load_strict_json
from .archive_io import load_archive_snapshot

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


def validate_release_artifact(artifact: Path) -> dict[str, Any]:
    """Validate manifest, SBOM and source-manifest identities inside an archive."""

    raw, payloads = load_archive_snapshot(artifact)
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

    source_manifest_bytes = payloads["manifest.json"]
    source_manifest_sha = _canonical_manifest_sha256(source_manifest_bytes)
    if source_manifest_sha != release_manifest["manifest_sha256"]:
        raise ValueError("release manifest source manifest digest does not match archive")

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
