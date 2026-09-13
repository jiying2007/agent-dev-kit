#!/usr/bin/env python3
"""Prove runtime-bundle reproducibility and emit provider-owned identity evidence."""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.distribution.release_artifacts import _release_source_identity
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.release import build_runtime_bundle

SCHEMA = "adk-runtime-bundle-identity/v1"


def _bundle_manifest(artifact: Path) -> dict[str, Any]:
    with tarfile.open(artifact, "r:gz") as archive:
        member = archive.extractfile("bundle-manifest.json")
        if member is None:
            raise ManifestError("runtime bundle is missing bundle-manifest.json")
        value = json.load(member)
    if not isinstance(value, dict):
        raise ManifestError("runtime bundle manifest must be an object")
    return value


def verify_runtime_bundle_identity(
    manifest: Manifest,
    profile: str,
    version: str | None = None,
    optional_skills: Sequence[str] = (),
) -> dict[str, Any]:
    """Build twice from one clean provider commit and bind that commit to one bundle SHA."""

    source = _release_source_identity(manifest.root, allow_unbound_snapshot=False)
    if (
        source.get("kind") != "git-clean-commit"
        or source.get("release_eligible") is not True
        or source.get("dirty") is not False
    ):
        raise ManifestError("runtime bundle identity requires a clean Git commit/tree")

    with tempfile.TemporaryDirectory(prefix="adk-runtime-identity-") as temp:
        root = Path(temp)
        first = build_runtime_bundle(
            manifest,
            root / "first",
            profile,
            version,
            optional_skills,
        )
        second = build_runtime_bundle(
            manifest,
            root / "second",
            profile,
            version,
            optional_skills,
        )
        if first["sha256"] != second["sha256"]:
            raise ManifestError("runtime bundle is not reproducible across independent builds")

        embedded = _bundle_manifest(Path(first["artifact"]))
        if embedded.get("schema") != "adk-runtime-bundle/v1":
            raise ManifestError("runtime bundle manifest schema is not adk-runtime-bundle/v1")
        if embedded.get("manifest_sha256") != manifest.digest:
            raise ManifestError("runtime bundle manifest digest does not match provider manifest")
        if embedded.get("profile") != profile:
            raise ManifestError("runtime bundle manifest profile does not match requested profile")
        if embedded.get("reproducible") is not True:
            raise ManifestError("runtime bundle manifest does not declare reproducibility")

        return {
            "schema": SCHEMA,
            "status": "pass",
            "profile": profile,
            "version": first["version"],
            "source_provenance": source,
            "manifest_sha256": manifest.digest,
            "bundle": {
                "schema": embedded["schema"],
                "artifact_name": Path(first["artifact"]).name,
                "sha256": first["sha256"],
                "skills": first["skills"],
                "files": first["files"],
                "source_distribution": first["source_distribution"],
            },
            "independent_builds": 2,
            "reproducible": True,
        }


def _write_result(value: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build one ADK runtime profile twice and emit exact source/artifact identity."
    )
    parser.add_argument("--profile", default="embedded-fullstack")
    parser.add_argument("--version")
    parser.add_argument("--with-optional-skill", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    try:
        value = verify_runtime_bundle_identity(
            Manifest.load(ROOT),
            args.profile,
            args.version,
            args.with_optional_skill,
        )
    except (ManifestError, OSError, json.JSONDecodeError, tarfile.TarError) as exc:
        _write_result(
            {
                "schema": SCHEMA,
                "status": "fail",
                "profile": args.profile,
                "failure": str(exc),
            },
            Path(args.output) if args.output else None,
        )
        return 1

    _write_result(value, Path(args.output) if args.output else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
