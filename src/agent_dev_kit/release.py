"""Deterministic release assembly and explicit publishing."""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .compiler import export_assets
from .model import Manifest, ManifestError, sha256_file


def check_release(manifest: Manifest) -> Dict[str, Any]:
    failures = manifest.validate(strict=True)
    supported_adapters = {"claude-code", "hermes-agent", "opencode"}
    unsupported = sorted(set(manifest.direct_targets()).difference(supported_adapters))
    if unsupported:
        failures.append("missing compiler adapters: {}".format(", ".join(unsupported)))

    version_sources = {
        ".version-lock": (manifest.root / ".version-lock", "version"),
        "pyproject.toml": (manifest.root / "pyproject.toml", "version"),
        "src/agent_dev_kit/__init__.py": (manifest.root / "src" / "agent_dev_kit" / "__init__.py", "__version__"),
    }
    for label, (path, field) in version_sources.items():
        if not path.is_file() or not re.search(
            r"(?m)^{}\s*[:=]\s*[\"']?{}[\"']?\s*$".format(
                re.escape(field), re.escape(manifest.version)
            ),
            path.read_text(encoding="utf-8") if path.is_file() else "",
        ):
            failures.append("release version is not synchronized in {}".format(label))

    mirror_check = subprocess.run(
        [sys.executable, str(manifest.root / "tools" / "check_manifest_sync.py")],
        cwd=str(manifest.root),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if mirror_check.returncode != 0:
        failures.append("manifest JSON/YAML mirror is not synchronized")

    workflow = manifest.root / ".github" / "workflows" / "release.yml"
    if not workflow.is_file():
        failures.append("release workflow missing")
    else:
        content = workflow.read_text(encoding="utf-8")
        if "--target codex" in content:
            failures.append("release workflow treats external Codex handoff as direct target")
        if "release build" not in content:
            failures.append("release workflow does not use the release contract")

    return {
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "version": manifest.version,
        "direct_targets": sorted(manifest.direct_targets()),
        "external_targets": sorted(manifest.external_targets()),
        "failures": failures,
    }


def _tar_filter(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = "root"
    info.gname = "root"
    info.mtime = 0
    if info.isdir():
        info.mode = 0o755
    elif info.isfile():
        info.mode = 0o755 if info.mode & 0o111 else 0o644
    return info


def _write_deterministic_archive(source: Path, archive: Path) -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="adk-release-", suffix=".tar", delete=False) as temp:
        tar_path = Path(temp.name)
    try:
        with tarfile.open(str(tar_path), mode="w", format=tarfile.PAX_FORMAT) as tar:
            for child in sorted(source.rglob("*")):
                tar.add(str(child), arcname=child.relative_to(source).as_posix(), recursive=False, filter=_tar_filter)
        with tar_path.open("rb") as raw, archive.open("wb") as output:
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
                shutil.copyfileobj(raw, compressed)
    finally:
        tar_path.unlink(missing_ok=True)


def _copy_source_distribution(manifest: Manifest, destination: Path) -> int:
    directories = (
        "agents",
        "contexts",
        "docs",
        "manifests",
        "optional-skills",
        "scripts",
        "skills",
        "src",
        "templates",
        "tests",
        "tools",
        "workflows",
    )
    files = (
        ".version-lock",
        "AGENTS.md",
        "CONTEXT.md",
        "LICENSE",
        "NAVIGATION.md",
        "README.md",
        "manifest.json",
        "manifest.yaml",
        "pyproject.toml",
    )
    destination.mkdir(parents=True, exist_ok=True)
    ignored = shutil.ignore_patterns(
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    )
    for relative in directories:
        source = manifest.root / relative
        if source.is_dir():
            symlinks = [path for path in source.rglob("*") if path.is_symlink()]
            if symlinks:
                raise ManifestError(
                    "release source distribution does not allow symlinks: {}".format(
                        ", ".join(path.relative_to(manifest.root).as_posix() for path in symlinks[:5])
                    )
                )
            shutil.copytree(
                str(source),
                str(destination / relative),
                symlinks=False,
                ignore=ignored,
            )
    for relative in files:
        source = manifest.root / relative
        if source.is_file():
            shutil.copy2(str(source), str(destination / relative))
    return sum(1 for path in destination.rglob("*") if path.is_file() or path.is_symlink())


def build_release(manifest: Manifest, output: Path, version: Optional[str] = None) -> Dict[str, Any]:
    version = version or manifest.version
    if version != manifest.version:
        raise ManifestError("release version does not match manifest: {} != {}".format(version, manifest.version))
    gate = check_release(manifest)
    if gate["status"] != "pass":
        raise ManifestError("release check failed: {}".format("; ".join(gate["failures"])))

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="adk-release-"))
    package_root = staging / "agent-dev-kit-{}".format(version)
    bundles = package_root / "bundles"
    bundles.mkdir(parents=True)
    try:
        target_results: List[Dict[str, Any]] = []
        for target in sorted(manifest.direct_targets()):
            result = export_assets(
                manifest,
                target=target,
                output_root=bundles,
                profiles=["embedded-fullstack"],
                clean=True,
            )
            target_results.append({"target": target, "agents": result["agents"], "skills": result["skills"]})

        source_file_count = _copy_source_distribution(manifest, package_root / "source")

        handoff = {
            "schema_version": 1,
            "manifest_version": manifest.version,
            "targets": manifest.external_targets(),
            "note": "External handoff targets are not direct export bundles.",
        }
        (package_root / "external-handoff-targets.json").write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        shutil.copy2(str(manifest.source), str(package_root / "manifest.json"))
        shutil.copy2(str(manifest.root / "LICENSE"), str(package_root / "LICENSE"))

        sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "agent-dev-kit-{}".format(version),
            "documentNamespace": "https://agent-dev-kit.local/releases/{}".format(version),
            "creationInfo": {
                "created": "1970-01-01T00:00:00Z",
                "creators": ["Tool: agent-dev-kit-{}".format(version)],
            },
            "documentDescribes": ["SPDXRef-Package-agent-dev-kit"],
            "packages": [
                {
                    "name": "agent-dev-kit",
                    "SPDXID": "SPDXRef-Package-agent-dev-kit",
                    "versionInfo": version,
                    "downloadLocation": "NOASSERTION",
                    "licenseConcluded": "MIT",
                    "licenseDeclared": "MIT",
                    "filesAnalyzed": False,
                },
                {
                    "name": "PyYAML",
                    "SPDXID": "SPDXRef-Package-PyYAML",
                    "downloadLocation": "https://pypi.org/project/PyYAML/",
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": "MIT",
                    "filesAnalyzed": False,
                    "summary": "Declared runtime requirement: PyYAML>=5.3,<7",
                },
            ],
            "relationships": [
                {
                    "spdxElementId": "SPDXRef-Package-agent-dev-kit",
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": "SPDXRef-Package-PyYAML",
                }
            ],
        }
        (package_root / "sbom.spdx.json").write_text(
            json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        release_manifest = {
            "schema_version": 1,
            "version": version,
            "manifest_sha256": manifest.digest,
            "direct_targets": target_results,
            "external_targets": sorted(manifest.external_targets()),
            "source_distribution": True,
            "source_file_count": source_file_count,
            "reproducible": True,
        }
        (package_root / "release-manifest.json").write_text(
            json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        archive = output / "agent-dev-kit-{}.tar.gz".format(version)
        _write_deterministic_archive(package_root, archive)
        digest = sha256_file(archive)
        checksum = output / (archive.name + ".sha256")
        checksum.write_text("{}  {}\n".format(digest, archive.name), encoding="ascii")
        return {
            "schema_version": 1,
            "status": "pass",
            "version": version,
            "artifact": str(archive),
            "sha256": digest,
            "checksum": str(checksum),
            "direct_targets": target_results,
            "external_targets": sorted(manifest.external_targets()),
            "source_distribution": True,
            "source_file_count": source_file_count,
        }
    finally:
        shutil.rmtree(str(staging), ignore_errors=True)


def publish_release(
    version: str,
    backend: Optional[str],
    artifact: Optional[Path],
    repository: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise ManifestError("release version must be a semantic version")
    if backend != "github":
        raise ManifestError("release backend is not configured; use --backend github")
    if artifact is None or not artifact.is_file():
        raise ManifestError("release artifact is required and must exist")
    expected_name = "agent-dev-kit-{}.tar.gz".format(version)
    if artifact.name != expected_name:
        raise ManifestError("release artifact name does not match version: {}".format(artifact.name))
    checksum = artifact.with_name(artifact.name + ".sha256")
    if not checksum.is_file():
        raise ManifestError("release checksum is missing: {}".format(checksum))
    checksum_fields = checksum.read_text(encoding="ascii").strip().split()
    if len(checksum_fields) != 2 or checksum_fields[1].lstrip("*") != artifact.name:
        raise ManifestError("release checksum file has an invalid format")
    actual_digest = sha256_file(artifact)
    if checksum_fields[0].lower() != actual_digest:
        raise ManifestError("release checksum does not match artifact")
    gh = shutil.which("gh")
    if gh is None:
        raise ManifestError("GitHub CLI is required for the github release backend")
    command = [gh, "release", "create", "v{}".format(version), str(artifact), str(checksum), "--verify-tag"]
    if repository:
        command.extend(["--repo", repository])
    if dry_run:
        return {"status": "planned", "backend": backend, "command": command}
    completed = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise ManifestError("github release failed: {}".format(completed.stderr.strip()))
    return {"status": "pass", "backend": backend, "version": version, "output": completed.stdout.strip()}
