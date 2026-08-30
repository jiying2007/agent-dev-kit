"""Deterministic release assembly and explicit publishing."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .compiler import export_assets
from .installer import (
    PREVIOUS_RECEIPT_SCHEMA,
    RECEIPT_NAME,
    _receipt_digest,
    apply_plan,
    create_plan,
    rollback,
    write_plan,
)
from .model import Manifest, ManifestError, sha256_file, sha256_tree


SOURCE_DISTRIBUTION_DIRECTORIES = (
    ".github", "agents", "contexts", "docs", "manifests", "optional-skills",
    "scripts", "schemas", "skills", "src", "templates", "tests", "tools", "workflows",
)
SOURCE_DISTRIBUTION_FILES = (
    ".version-lock", ".adk/harness-readiness.json", "AGENTS.md", "CONTEXT.md",
    "LICENSE", "NAVIGATION.md", "OWNERS", "README.md", "manifest.json", "manifest.yaml",
    "pyproject.toml",
)


def _report_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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

    try:
        mirror_check = subprocess.run(
            [sys.executable, str(manifest.root / "tools" / "check_manifest_sync.py")],
            cwd=str(manifest.root),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        mirror_check = None
    if mirror_check is None or mirror_check.returncode != 0:
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
        if not re.search(r"actions/attest@[0-9a-f]{40}", content):
            failures.append("release workflow does not create SHA-pinned provenance attestation")
        for permission in ("id-token: write", "attestations: write", "artifact-metadata: write"):
            if permission not in content:
                failures.append("release workflow missing attestation permission: {}".format(permission))

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
    with tempfile.NamedTemporaryFile(
        prefix="." + archive.name + ".",
        suffix=".tmp",
        dir=str(archive.parent),
        delete=False,
    ) as temp:
        archive_temp = Path(temp.name)
    try:
        with tarfile.open(str(tar_path), mode="w", format=tarfile.PAX_FORMAT) as tar:
            for child in sorted(source.rglob("*")):
                tar.add(str(child), arcname=child.relative_to(source).as_posix(), recursive=False, filter=_tar_filter)
        with tar_path.open("rb") as raw, archive_temp.open("wb") as output:
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
                shutil.copyfileobj(raw, compressed)
        archive_temp.chmod(0o644)
        os.replace(str(archive_temp), str(archive))
    finally:
        tar_path.unlink(missing_ok=True)
        archive_temp.unlink(missing_ok=True)


def _skill_version(skill_root: Path) -> str:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file():
        raise ManifestError("runtime bundle skill is missing SKILL.md: {}".format(skill_root))
    match = re.search(
        r"(?m)^version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)[\"']?\s*$",
        skill_file.read_text(encoding="utf-8"),
    )
    if match is None:
        raise ManifestError("runtime bundle skill has no semantic version: {}".format(skill_root))
    return match.group(1)


def _copy_runtime_skill(source: Path, destination: Path) -> int:
    members = [source] + sorted(source.rglob("*"))
    unsafe = [path for path in members if path.is_symlink() or not (path.is_dir() or path.is_file())]
    if unsafe:
        raise ManifestError(
            "runtime bundle does not allow links or special files: {}".format(
                ", ".join(path.as_posix() for path in unsafe[:5])
            )
        )
    shutil.copytree(str(source), str(destination), symlinks=False)
    return sum(1 for path in destination.rglob("*") if path.is_file())


def _write_runtime_checksums(package_root: Path) -> Path:
    checksum = package_root / "checksums.sha256"
    lines = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file() and path != checksum:
            lines.append("{}  {}".format(sha256_file(path), path.relative_to(package_root).as_posix()))
    checksum.write_text("\n".join(lines) + "\n", encoding="ascii")
    return checksum


def build_runtime_bundle(
    manifest: Manifest,
    output: Path,
    profile: str,
    version: Optional[str] = None,
    optional_skills: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a deterministic, implementation-free Skill bundle for external runtimes."""

    version = version or manifest.version
    if version != manifest.version:
        raise ManifestError("runtime bundle version does not match manifest: {} != {}".format(version, manifest.version))
    failures = manifest.validate(strict=True)
    if failures:
        raise ManifestError("runtime bundle validation failed: {}".format("; ".join(failures)))
    resolution = manifest.resolve_profiles([profile], optional_skills=optional_skills)
    if not resolution.skills:
        raise ManifestError("runtime bundle profile resolves to zero skills: {}".format(profile))

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="adk-runtime-bundle-"))
    package_root = staging / "package"
    package_root.mkdir()
    try:
        assets: List[Dict[str, Any]] = []
        file_count = 0
        for asset in resolution.skills:
            skill_version = _skill_version(asset.path)
            relative = Path("skills") / asset.name / skill_version
            destination = package_root / relative
            file_count += _copy_runtime_skill(asset.path, destination)
            digest = sha256_tree(destination)
            if digest != asset.digest:
                raise ManifestError("runtime bundle skill digest changed during copy: {}".format(asset.name))
            record = manifest.asset_record(asset)
            assets.append(
                {
                    "kind": "skill",
                    "name": asset.name,
                    "version": skill_version,
                    "path": relative.as_posix(),
                    "sha256": digest,
                    "source_path": str(record.get("path", "")),
                    "optional": asset.optional,
                }
            )

        bundle_manifest = {
            "schema": "adk-runtime-bundle/v1",
            "adk_version": version,
            "manifest_sha256": manifest.digest,
            "profile": profile,
            "resolved_profiles": list(resolution.profiles),
            "optional_skills": sorted(optional_skills),
            "asset_kinds": ["skill"],
            "assets": assets,
            "source_distribution": False,
            "reproducible": True,
        }
        (package_root / "bundle-manifest.json").write_text(
            json.dumps(bundle_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        shutil.copy2(str(manifest.root / "LICENSE"), str(package_root / "LICENSE"))
        sbom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": "adk-runtime-{}-{}".format(profile, version),
            "documentNamespace": "https://agent-dev-kit.local/runtime/{}/{}".format(version, profile),
            "creationInfo": {
                "created": "1970-01-01T00:00:00Z",
                "creators": ["Tool: agent-dev-kit-{}".format(version)],
            },
            "documentDescribes": ["SPDXRef-Skill-{}".format(item["name"]) for item in assets],
            "packages": [
                {
                    "name": item["name"],
                    "SPDXID": "SPDXRef-Skill-{}".format(item["name"]),
                    "versionInfo": item["version"],
                    "downloadLocation": "NOASSERTION",
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": "NOASSERTION",
                    "filesAnalyzed": False,
                    "checksums": [{"algorithm": "SHA256", "checksumValue": item["sha256"]}],
                }
                for item in assets
            ],
            "relationships": [],
        }
        (package_root / "sbom.spdx.json").write_text(
            json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        _write_runtime_checksums(package_root)

        archive = output / "adk-runtime-{}-{}.tar.gz".format(profile, version)
        _write_deterministic_archive(package_root, archive)
        digest = sha256_file(archive)
        checksum = output / (archive.name + ".sha256")
        checksum.write_text("{}  {}\n".format(digest, archive.name), encoding="ascii")
        return {
            "schema": "adk-runtime-bundle-result/v1",
            "status": "pass",
            "version": version,
            "profile": profile,
            "artifact": str(archive),
            "sha256": digest,
            "checksum": str(checksum),
            "skills": len(assets),
            "files": file_count,
            "source_distribution": False,
        }
    finally:
        shutil.rmtree(str(staging), ignore_errors=True)


def _copy_source_distribution(manifest: Manifest, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    ignored = shutil.ignore_patterns(
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.log",
        "*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "release-rehearsal.json",
        "codex-runtime-smoke.json",
        "full-test-timing.json",
        "software-m5-campaign-plan.json",
        "software-m5-campaign-state",
    )
    for relative in SOURCE_DISTRIBUTION_DIRECTORIES:
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
    for relative in SOURCE_DISTRIBUTION_FILES:
        source = manifest.root / relative
        if source.is_file():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(source), str(target))
    return sum(1 for path in destination.rglob("*") if path.is_file() or path.is_symlink())


def _release_source_identity(root: Path, allow_unbound_snapshot: bool) -> Dict[str, Any]:
    root = root.resolve()
    git_dir = root / ".git"
    if not git_dir.exists():
        if not allow_unbound_snapshot:
            raise ManifestError(
                "release build requires a native Git checkout; use --allow-unbound-snapshot only for non-release validation"
            )
        return {
            "kind": "unbound-snapshot",
            "release_eligible": False,
            "commit": None,
            "tree": None,
            "dirty": None,
        }

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise ManifestError("release build root is not the native Git repository root")
    commit_result = git("rev-parse", "HEAD")
    tree_result = git("rev-parse", "HEAD^{tree}")
    if commit_result.returncode != 0 or tree_result.returncode != 0:
        raise ManifestError("release build cannot resolve source commit/tree identity")
    status = git(
        "status", "--porcelain=v1", "--untracked-files=all", "--",
        *SOURCE_DISTRIBUTION_DIRECTORIES, *SOURCE_DISTRIBUTION_FILES,
    )
    if status.returncode != 0:
        raise ManifestError("release build cannot inspect source worktree state")
    dirty = bool(status.stdout.strip())
    if dirty and not allow_unbound_snapshot:
        raise ManifestError("release build requires a clean source distribution worktree")
    return {
        "kind": "git-clean-commit" if not dirty else "git-working-tree-snapshot",
        "release_eligible": not dirty,
        "commit": commit_result.stdout.strip(),
        "tree": tree_result.stdout.strip(),
        "dirty": dirty,
    }


def _validate_sbom(sbom: Mapping[str, Any]) -> None:
    failures: List[str] = []
    if sbom.get("spdxVersion") != "SPDX-2.3":
        failures.append("spdxVersion must be SPDX-2.3")
    packages = sbom.get("packages")
    relationships = sbom.get("relationships")
    if not isinstance(packages, list) or not packages:
        failures.append("packages must be a non-empty array")
        packages = []
    if not isinstance(relationships, list):
        failures.append("relationships must be an array")
        relationships = []
    package_ids = [item.get("SPDXID") for item in packages if isinstance(item, dict)]
    if len(package_ids) != len(set(package_ids)) or any(not item for item in package_ids):
        failures.append("package SPDXIDs must be present and unique")
    described = sbom.get("documentDescribes")
    if not isinstance(described, list) or any(item not in package_ids for item in described):
        failures.append("documentDescribes must reference declared packages")
    names = {item.get("name") for item in packages if isinstance(item, dict)}
    dependency_ids = {
        item.get("relatedSpdxElement")
        for item in relationships
        if isinstance(item, dict)
        and item.get("spdxElementId") == "SPDXRef-Package-agent-dev-kit"
        and item.get("relationshipType") == "DEPENDS_ON"
    }
    for name, package_id in (
        ("PyYAML", "SPDXRef-Package-PyYAML"),
        ("jsonschema", "SPDXRef-Package-jsonschema"),
    ):
        if name not in names:
            failures.append("runtime dependency missing from SBOM: {}".format(name))
        if package_id not in dependency_ids:
            failures.append("runtime dependency relationship missing from SBOM: {}".format(name))
    known_ids = set(package_ids)
    for item in relationships:
        if not isinstance(item, dict):
            failures.append("relationship entries must be objects")
            continue
        if item.get("spdxElementId") not in known_ids or item.get("relatedSpdxElement") not in known_ids:
            failures.append("relationship references an unknown SPDXID")
    if failures:
        raise ManifestError("release SBOM validation failed: {}".format("; ".join(sorted(set(failures)))))


def build_release(
    manifest: Manifest,
    output: Path,
    version: Optional[str] = None,
    allow_unbound_snapshot: bool = False,
) -> Dict[str, Any]:
    version = version or manifest.version
    if version != manifest.version:
        raise ManifestError("release version does not match manifest: {} != {}".format(version, manifest.version))
    gate = check_release(manifest)
    if gate["status"] != "pass":
        raise ManifestError("release check failed: {}".format("; ".join(gate["failures"])))
    source_identity = _release_source_identity(manifest.root, allow_unbound_snapshot)

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="adk-release-"))
    package_root = staging / "agent-dev-kit-{}".format(version)
    bundles = package_root / "bundles"
    bundles.mkdir(parents=True)
    try:
        target_results: List[Dict[str, Any]] = []
        for target in sorted(manifest.direct_targets()):
            target_config = manifest.target(target)
            supported_kinds = target_config.get("supported_asset_kinds", [])
            asset_kind = supported_kinds[0] if isinstance(supported_kinds, list) and len(supported_kinds) == 1 else None
            result = export_assets(
                manifest,
                target=target,
                output_root=bundles,
                profiles=["embedded-fullstack"],
                asset_kind=asset_kind,
                clean=True,
            )
            target_results.append({"target": target, "agents": result["agents"], "skills": result["skills"]})

        source_file_count = _copy_source_distribution(manifest, package_root / "source")
        source_distribution_sha256 = sha256_tree(package_root / "source")

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
                    "summary": "Declared runtime requirement: PyYAML==6.0.3",
                },
                {
                    "name": "jsonschema",
                    "SPDXID": "SPDXRef-Package-jsonschema",
                    "downloadLocation": "https://pypi.org/project/jsonschema/",
                    "licenseConcluded": "NOASSERTION",
                    "licenseDeclared": "MIT",
                    "filesAnalyzed": False,
                    "summary": "Declared runtime requirement: jsonschema==4.26.0",
                },
            ],
            "relationships": [
                {
                    "spdxElementId": "SPDXRef-Package-agent-dev-kit",
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": "SPDXRef-Package-PyYAML",
                },
                {
                    "spdxElementId": "SPDXRef-Package-agent-dev-kit",
                    "relationshipType": "DEPENDS_ON",
                    "relatedSpdxElement": "SPDXRef-Package-jsonschema",
                },
            ],
        }
        _validate_sbom(sbom)
        sbom_path = package_root / "sbom.spdx.json"
        sbom_path.write_text(
            json.dumps(sbom, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        sbom_digest = sha256_file(sbom_path)
        release_manifest = {
            "schema_version": 2,
            "version": version,
            "manifest_sha256": manifest.digest,
            "direct_targets": target_results,
            "external_targets": sorted(manifest.external_targets()),
            "source_distribution": True,
            "source_file_count": source_file_count,
            "reproducible": source_identity["release_eligible"],
            "release_eligible": source_identity["release_eligible"],
            "source_provenance": {
                **source_identity,
                "source_distribution_sha256": source_distribution_sha256,
            },
            "sbom": {
                "path": "sbom.spdx.json",
                "sha256": sbom_digest,
                "validated": True,
            },
        }
        (package_root / "release-manifest.json").write_text(
            json.dumps(release_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        archive = output / "agent-dev-kit-{}.tar.gz".format(version)
        _write_deterministic_archive(package_root, archive)
        digest = sha256_file(archive)
        checksum = output / (archive.name + ".sha256")
        checksum_temp = checksum.with_name("." + checksum.name + ".tmp")
        try:
            checksum_temp.write_text("{}  {}\n".format(digest, archive.name), encoding="ascii")
            checksum_temp.chmod(0o644)
            os.replace(str(checksum_temp), str(checksum))
        finally:
            checksum_temp.unlink(missing_ok=True)
        result = {
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
            "release_eligible": source_identity["release_eligible"],
            "source_provenance": {
                **source_identity,
                "source_distribution_sha256": source_distribution_sha256,
            },
        }
        return result
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
    _assert_publishable_release_artifact(artifact)
    gh = shutil.which("gh")
    if gh is None:
        raise ManifestError("GitHub CLI is required for the github release backend")
    command = [gh, "release", "create", "v{}".format(version), str(artifact), str(checksum), "--verify-tag"]
    if repository:
        command.extend(["--repo", repository])
    if dry_run:
        return {"status": "planned", "backend": backend, "command": command}
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise ManifestError("github release timed out after 300 seconds") from exc
    except OSError as exc:
        raise ManifestError("github release could not start: {}".format(exc)) from exc
    if completed.returncode != 0:
        raise ManifestError("github release failed: {}".format(completed.stderr.strip()))
    return {"status": "pass", "backend": backend, "version": version, "output": completed.stdout.strip()}


def _verify_artifact_checksum(artifact: Path) -> str:
    artifact = artifact.resolve()
    if not artifact.is_file():
        raise ManifestError("release artifact is missing: {}".format(artifact))
    checksum = artifact.with_name(artifact.name + ".sha256")
    if not checksum.is_file():
        raise ManifestError("release checksum is missing: {}".format(checksum))
    fields = checksum.read_text(encoding="ascii").strip().split()
    if len(fields) != 2 or fields[1].lstrip("*") != artifact.name:
        raise ManifestError("release checksum file has an invalid format")
    digest = sha256_file(artifact)
    if fields[0].lower() != digest:
        raise ManifestError("release checksum does not match artifact")
    return digest


def _assert_publishable_release_artifact(artifact: Path) -> Mapping[str, Any]:
    workspace = Path(tempfile.mkdtemp(prefix="adk-release-publish-check-"))
    try:
        release_root = _extract_release(artifact.resolve(), workspace / "artifact")
        _, release_manifest = _release_source_root(release_root)
        provenance = release_manifest.get("source_provenance")
        if (
            release_manifest.get("schema_version") != 2
            or release_manifest.get("release_eligible") is not True
            or release_manifest.get("reproducible") is not True
            or not isinstance(provenance, dict)
            or provenance.get("kind") != "git-clean-commit"
            or provenance.get("dirty") is not False
        ):
            raise ManifestError("release artifact is not bound to a clean Git commit/tree")
        return release_manifest
    finally:
        shutil.rmtree(str(workspace), ignore_errors=True)


def _extract_release(artifact: Path, destination: Path, member_limit: int = 5000) -> Path:
    destination.mkdir(parents=True, exist_ok=False)
    roots = set()
    members = []
    names = set()
    total_size = 0
    destination_root = destination.resolve()
    with tarfile.open(str(artifact), mode="r:gz") as archive:
        for member in archive:
            if len(members) >= member_limit:
                raise ManifestError("release archive exceeds member limit")
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or len(member.name) > 512:
                raise ManifestError("release archive contains an unsafe path")
            if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
                raise ManifestError("release archive contains an unsupported member")
            if member.name in names:
                raise ManifestError("release archive contains a duplicate member")
            names.add(member.name)
            total_size += member.size
            if member.size > 128 * 1024 * 1024 or total_size > 512 * 1024 * 1024:
                raise ManifestError("release archive exceeds extraction size limits")
            roots.add(path.parts[0])
            resolved = (destination / path).resolve()
            try:
                resolved.relative_to(destination_root)
            except ValueError as exc:
                raise ManifestError("release archive escapes extraction root") from exc
            members.append(member)
        for member in members:
            archive.extract(member, path=str(destination), set_attrs=True)
    if "manifest.json" in names:
        return destination
    if len(roots) == 1:
        root = destination / next(iter(roots))
        if (root / "manifest.json").is_file():
            return root
    raise ManifestError("release archive does not contain a supported ADK root layout")


def _release_source_root(
    release_root: Path,
    *,
    enforce_current_contract: bool = True,
) -> Tuple[Manifest, Mapping[str, Any]]:
    source_root = release_root / "source"
    release_manifest_path = release_root / "release-manifest.json"
    if not source_root.is_dir() or not (source_root / "manifest.json").is_file():
        raise ManifestError("release archive does not contain its source distribution")
    try:
        release_manifest = json.loads(release_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("release archive has an invalid release manifest") from exc
    if not isinstance(release_manifest, dict) or release_manifest.get("schema_version") not in {1, 2}:
        raise ManifestError("release archive has an unsupported release manifest")
    top_manifest = Manifest.load(release_root)
    source_manifest = Manifest.load(source_root)
    if top_manifest.digest != source_manifest.digest:
        raise ManifestError("release top-level and source manifests differ")
    if release_manifest.get("manifest_sha256") != source_manifest.digest:
        raise ManifestError("release manifest digest does not match source manifest")
    if release_manifest.get("version") != source_manifest.version:
        raise ManifestError("release manifest version does not match source manifest")
    if enforce_current_contract:
        failures = source_manifest.validate(strict=True)
        if failures:
            raise ManifestError("release source manifest is invalid: {}".format("; ".join(failures)))
    return source_manifest, release_manifest


def _prerelease_is_newer(previous: str, candidate: str) -> bool:
    pattern = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")
    previous_match = pattern.fullmatch(previous)
    candidate_match = pattern.fullmatch(candidate)
    if previous_match is None or candidate_match is None:
        raise ManifestError("release rehearsal versions must be semantic versions")
    previous_core = tuple(int(value) for value in previous_match.groups()[:3])
    candidate_core = tuple(int(value) for value in candidate_match.groups()[:3])
    if previous_core != candidate_core:
        return candidate_core > previous_core
    previous_pre = previous_match.group(4)
    candidate_pre = candidate_match.group(4)
    if previous_pre is None or candidate_pre is None:
        return previous_pre is not None and candidate_pre is None
    previous_parts = previous_pre.split(".")
    candidate_parts = candidate_pre.split(".")
    for previous_part, candidate_part in zip(previous_parts, candidate_parts):
        if previous_part == candidate_part:
            continue
        previous_numeric = previous_part.isdigit()
        candidate_numeric = candidate_part.isdigit()
        if previous_numeric and candidate_numeric:
            return int(candidate_part) > int(previous_part)
        if previous_numeric != candidate_numeric:
            return not candidate_numeric
        return candidate_part > previous_part
    return len(candidate_parts) > len(previous_parts)


def _managed_hashes(target: Path) -> Dict[str, str]:
    receipt_path = target / RECEIPT_NAME
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("release rehearsal receipt is invalid") from exc
    installed = receipt.get("installed")
    if not isinstance(installed, list) or not installed:
        raise ManifestError("release rehearsal receipt has no installed assets")
    hashes: Dict[str, str] = {}
    for item in installed:
        if not isinstance(item, dict) or not isinstance(item.get("destination"), str):
            raise ManifestError("release rehearsal receipt contains an invalid asset")
        destination = str(item["destination"])
        if destination in hashes:
            raise ManifestError("release rehearsal receipt contains duplicate assets")
        path = (target / destination).resolve()
        try:
            path.relative_to(target.resolve())
        except ValueError as exc:
            raise ManifestError("release rehearsal asset escapes target") from exc
        if not path.exists() and not path.is_symlink():
            raise ManifestError("release rehearsal managed asset is missing")
        hashes[destination] = sha256_tree(path)
    return hashes


def _install_legacy_release_bundle(
    release_root: Path,
    manifest: Manifest,
    target: Path,
    migration: str = "legacy-bundle-v2",
) -> Dict[str, Any]:
    """Stage a pre-contract release as a digest-protected v2 rollback fixture."""

    bundle = release_root / "bundles" / "claude-code"
    if not bundle.is_dir() or bundle.is_symlink():
        raise ManifestError("legacy release does not contain a safe Claude Code bundle")
    files = sorted(path for path in bundle.rglob("*") if path.is_file() or path.is_symlink())
    if not files or any(path.is_symlink() for path in files):
        raise ManifestError("legacy release bundle is empty or contains symlinks")
    target.mkdir(parents=True, exist_ok=True)
    receipt_id = "legacy-{}".format(manifest.version.replace("/", "-"))
    backup_root = target / ".adk-backups" / receipt_id
    backup_root.mkdir(parents=True, exist_ok=False)
    installed: List[Dict[str, Any]] = []
    for source in files:
        relative = source.relative_to(bundle).as_posix()
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(destination))
        kind = relative.split("/", 1)[0].rstrip("s")
        name = source.stem
        installed.append(
            {
                "kind": kind,
                "name": name,
                "destination": relative,
                "source_sha256": sha256_file(source),
                "installed_sha256": sha256_tree(destination),
                "backup": None,
                "backup_sha256": None,
            }
        )
    receipt = {
        "schema": PREVIOUS_RECEIPT_SCHEMA,
        "receipt_id": receipt_id,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "plan_id": "legacy-bundle-migration",
        "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest,
        "tool": "claude-code",
        "target": str(target),
        "backup_root": backup_root.relative_to(target).as_posix(),
        "previous_receipt": None,
        "previous_receipt_sha256": None,
        "installed": installed,
    }
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    receipt_path = target / RECEIPT_NAME
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "pass",
        "installed": len(installed),
        "receipt": str(receipt_path),
        "migration": migration,
    }


def _previous_release_migration(error: ManifestError) -> Optional[str]:
    message = str(error)
    if "target_contract_missing" in message:
        return "legacy-bundle-v2"
    if "target_contract_incompatible" in message or "target_contract_invalid" in message:
        return "target-contract-hard-cut"
    return None


def rehearse_release(previous_artifact: Path, candidate_artifact: Path) -> Dict[str, Any]:
    previous_digest = _verify_artifact_checksum(previous_artifact)
    candidate_digest = _verify_artifact_checksum(candidate_artifact)
    workspace = Path(tempfile.mkdtemp(prefix="adk-release-rehearsal-"))
    try:
        previous_root = _extract_release(previous_artifact.resolve(), workspace / "previous")
        candidate_root = _extract_release(candidate_artifact.resolve(), workspace / "candidate")
        previous_manifest, previous_release_manifest = _release_source_root(
            previous_root,
            enforce_current_contract=False,
        )
        candidate_manifest, candidate_release_manifest = _release_source_root(candidate_root)
        if (
            candidate_release_manifest.get("schema_version") != 2
            or candidate_release_manifest.get("release_eligible") is not True
            or candidate_release_manifest.get("reproducible") is not True
        ):
            raise ManifestError("candidate release is not bound to a clean Git commit/tree")
        candidate_provenance = candidate_release_manifest.get("source_provenance")
        if (
            not isinstance(candidate_provenance, dict)
            or candidate_provenance.get("kind") != "git-clean-commit"
            or candidate_provenance.get("dirty") is not False
            or not re.fullmatch(r"[0-9a-f]{40}", str(candidate_provenance.get("commit", "")))
            or not re.fullmatch(r"[0-9a-f]{40}", str(candidate_provenance.get("tree", "")))
            or not re.fullmatch(
                r"[0-9a-f]{64}", str(candidate_provenance.get("source_distribution_sha256", ""))
            )
        ):
            raise ManifestError("candidate release source provenance is incomplete")
        if not _prerelease_is_newer(previous_manifest.version, candidate_manifest.version):
            raise ManifestError("candidate release must be newer than previous release")

        target = workspace / "target"
        previous_plan_path = workspace / "previous-plan.json"
        try:
            previous_plan = create_plan(
                previous_manifest,
                "claude-code",
                str(target),
                [previous_manifest.default_profile],
                [],
                "copy",
            )
        except ManifestError as exc:
            previous_migration = _previous_release_migration(exc)
            if previous_migration is None:
                raise
            previous_apply = _install_legacy_release_bundle(
                previous_root,
                previous_manifest,
                target,
                migration=previous_migration,
            )
        else:
            if previous_plan["status"] != "ready":
                raise ManifestError("previous release install plan is not ready")
            write_plan(previous_plan, previous_plan_path)
            previous_apply = apply_plan(previous_manifest, previous_plan_path)
        previous_hashes = _managed_hashes(target)

        migration_mode = "in-place-replacement"
        legacy_rollback: Optional[Dict[str, Any]] = None
        previous_migration = previous_apply.get("migration")
        if previous_migration in ("legacy-bundle-v2", "target-contract-hard-cut"):
            migration_mode = "rollback-before-install"
            legacy_rollback = rollback(target / RECEIPT_NAME)
            if (target / RECEIPT_NAME).exists():
                raise ManifestError("legacy receipt remained after migration rollback")

        candidate_plan_path = workspace / "candidate-plan.json"
        candidate_plan = create_plan(
            candidate_manifest,
            "claude-code",
            str(target),
            [candidate_manifest.default_profile],
            [],
            "copy",
        )
        if candidate_plan["status"] != "ready":
            raise ManifestError("candidate release upgrade plan is not ready")
        write_plan(candidate_plan, candidate_plan_path)
        candidate_apply = apply_plan(candidate_manifest, candidate_plan_path)
        candidate_receipt = json.loads((target / RECEIPT_NAME).read_text(encoding="utf-8"))
        if candidate_receipt.get("manifest_version") != candidate_manifest.version:
            raise ManifestError("candidate receipt version does not match release")

        rollback_result = rollback(target / RECEIPT_NAME)
        fallback_restore: Optional[Dict[str, Any]] = None
        if migration_mode == "in-place-replacement":
            restored_receipt = json.loads((target / RECEIPT_NAME).read_text(encoding="utf-8"))
            restored_hashes = _managed_hashes(target)
            if restored_receipt.get("manifest_version") != previous_manifest.version:
                raise ManifestError("rollback did not restore the previous receipt")
            if restored_hashes != previous_hashes:
                raise ManifestError("rollback did not restore the previous managed asset hashes")
        else:
            if (target / RECEIPT_NAME).exists():
                raise ManifestError("candidate receipt remained after rollback")
            fallback_apply = _install_legacy_release_bundle(
                previous_root,
                previous_manifest,
                target,
                migration=str(previous_migration),
            )
            restored_hashes = _managed_hashes(target)
            if restored_hashes != previous_hashes:
                raise ManifestError("previous legacy artifact reinstall did not restore managed hashes")
            fallback_cleanup = rollback(target / RECEIPT_NAME)
            if (target / RECEIPT_NAME).exists():
                raise ManifestError("fallback receipt remained after rehearsal cleanup")
            fallback_restore = {
                "status": "pass",
                "strategy": "reinstall-previous-artifact",
                "installed": fallback_apply["installed"],
                "cleanup_removed": fallback_cleanup["removed"],
            }
        result = {
            "schema_version": 2,
            "status": "pass",
            "previous_version": previous_manifest.version,
            "candidate_version": candidate_manifest.version,
            "previous_sha256": previous_digest,
            "candidate_sha256": candidate_digest,
            "previous_manifest_sha256": previous_release_manifest["manifest_sha256"],
            "candidate_manifest_sha256": candidate_release_manifest["manifest_sha256"],
            "previous_installed": previous_apply["installed"],
            "candidate_installed": candidate_apply["installed"],
            "migration_mode": migration_mode,
            "previous_install_migration": previous_migration,
            "legacy_rollback": legacy_rollback,
            "fallback_restore": fallback_restore,
            "rollback": {
                "status": rollback_result["status"],
                "removed": rollback_result["removed"],
                "restored": rollback_result["restored"],
            },
            "restored_assets": len(restored_hashes),
            "remote_publish": "not-in-scope",
        }
        result["report_sha256"] = _report_digest(result)
        return result
    finally:
        shutil.rmtree(str(workspace), ignore_errors=True)
