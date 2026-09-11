"""Validation for the existing release-manifest schema v2.

The release builder remains responsible for assembly.  This module is the
bounded contract verifier used after assembly and before provenance attestation.
It never extracts archive members to disk.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

from agent_dev_kit.contracts.schema_loader import packaged_schema_bytes

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
    if isinstance(provenance, Mapping):
        if value.get("release_eligible") != provenance.get("release_eligible"):
            failures.append("release_eligible must match source_provenance.release_eligible")
    if value.get("reproducible") != value.get("release_eligible"):
        failures.append("reproducible must match release_eligible")

    return {
        "schema": "adk-release-manifest-validation/v1",
        "status": "pass" if not failures else "fail",
        "version": value.get("version"),
        "failures": sorted(set(failures)),
    }


def _safe_regular_member(archive: tarfile.TarFile, name: str) -> tarfile.TarInfo:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or len(path.parts) < 2:
        raise ValueError(f"unsafe release archive member path: {name}")
    matches = [member for member in archive.getmembers() if member.name == name]
    if len(matches) != 1 or not matches[0].isreg():
        raise ValueError(f"release archive member must be one regular file: {name}")
    if matches[0].size > _MAX_JSON_BYTES:
        raise ValueError(f"release archive member exceeds size limit: {name}")
    return matches[0]


def _read_regular_member(archive: tarfile.TarFile, name: str) -> bytes:
    member = _safe_regular_member(archive, name)
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError(f"cannot read release archive member: {name}")
    value = stream.read(_MAX_JSON_BYTES + 1)
    if len(value) > _MAX_JSON_BYTES:
        raise ValueError(f"release archive member exceeds size limit: {name}")
    return value


def validate_release_artifact(artifact: Path) -> dict[str, Any]:
    """Validate manifest, SBOM and source-manifest identities inside an archive."""

    artifact = artifact.resolve()
    if not artifact.is_file():
        raise ValueError(f"release artifact does not exist: {artifact}")

    with tarfile.open(artifact, mode="r:gz") as archive:
        manifest_members = [
            member
            for member in archive.getmembers()
            if member.isreg() and member.name.endswith("/release-manifest.json")
        ]
        if len(manifest_members) != 1:
            raise ValueError("release archive must contain exactly one release-manifest.json")
        release_member = manifest_members[0]
        release_path = PurePosixPath(release_member.name)
        if release_path.is_absolute() or ".." in release_path.parts or len(release_path.parts) != 2:
            raise ValueError("release-manifest.json must be directly below the package root")
        package_root = release_path.parts[0]
        release_bytes = _read_regular_member(archive, release_member.name)
        try:
            release_manifest = json.loads(release_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("release-manifest.json is not valid UTF-8 JSON") from exc
        if not isinstance(release_manifest, dict):
            raise ValueError("release-manifest.json root must be an object")

        validation = validate_release_manifest(release_manifest)
        if validation["status"] != "pass":
            raise ValueError("release manifest validation failed: " + "; ".join(validation["failures"]))

        version = str(release_manifest["version"])
        expected_root = f"agent-dev-kit-{version}"
        if package_root != expected_root:
            raise ValueError(f"release package root mismatch: {package_root} != {expected_root}")
        if artifact.name != f"{expected_root}.tar.gz":
            raise ValueError("release artifact filename does not match manifest version")

        sbom_name = f"{package_root}/{release_manifest['sbom']['path']}"
        sbom_bytes = _read_regular_member(archive, sbom_name)
        sbom_sha = _sha256(sbom_bytes)
        if sbom_sha != release_manifest["sbom"]["sha256"]:
            raise ValueError("release SBOM digest does not match release manifest")

        source_manifest_name = f"{package_root}/manifest.json"
        source_manifest_bytes = _read_regular_member(archive, source_manifest_name)
        source_manifest_sha = _sha256(source_manifest_bytes)
        if source_manifest_sha != release_manifest["manifest_sha256"]:
            raise ValueError("release manifest source manifest digest does not match archive")

    return {
        "schema": "adk-release-artifact-contract/v1",
        "status": "pass",
        "version": version,
        "artifact": artifact.name,
        "artifact_sha256": _sha256(artifact.read_bytes()),
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
    print(json.dumps({"schema": "adk-release-artifact-contract-set/v1", "status": "pass", "artifacts": results}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
