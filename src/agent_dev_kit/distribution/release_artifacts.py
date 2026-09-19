"""Release artifact domain: deterministic archives, source identity, SBOM, and validation."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..installer import RECEIPT_NAME
from ..model import Manifest, ManifestError, sha256_file, sha256_tree

SOURCE_DISTRIBUTION_DIRECTORIES = (
    ".github", "agents", "docs", "manifests", "optional-skills",
    "scripts", "schemas", "skills", "src", "templates", "tests", "tools", "workflows",
)

SOURCE_DISTRIBUTION_FILES = (
    ".version-lock", ".adk/harness-readiness.json", "AGENTS.md", "CONTEXT.md",
    "LICENSE", "OWNERS", "README.md", "manifest.json",
    "pyproject.toml",
)


def _report_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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
        with (
            tar_path.open("rb") as raw,
            archive_temp.open("wb") as output,
            gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed,
        ):
            shutil.copyfileobj(raw, compressed)
        archive_temp.chmod(0o644)
        os.replace(str(archive_temp), str(archive))
    finally:
        tar_path.unlink(missing_ok=True)
        archive_temp.unlink(missing_ok=True)


def _skill_version(skill_root: Path) -> str:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file():
        raise ManifestError(f"runtime bundle skill is missing SKILL.md: {skill_root}")
    match = re.search(
        r"(?m)^version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)[\"']?\s*$",
        skill_file.read_text(encoding="utf-8"),
    )
    if match is None:
        raise ManifestError(f"runtime bundle skill has no semantic version: {skill_root}")
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
            lines.append(f"{sha256_file(path)}  {path.relative_to(package_root).as_posix()}")
    checksum.write_text("\n".join(lines) + "\n", encoding="ascii")
    return checksum


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
        if not source.is_dir():
            raise ManifestError(f"release source directory is missing: {relative}")
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
        if not source.is_file():
            raise ManifestError(f"release source file is missing: {relative}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(target))
    return sum(1 for path in destination.rglob("*") if path.is_file() or path.is_symlink())


def _release_source_identity(root: Path, allow_unbound_snapshot: bool) -> dict[str, Any]:
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
            capture_output=True,
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
    failures: list[str] = []
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
            failures.append(f"runtime dependency missing from SBOM: {name}")
        if package_id not in dependency_ids:
            failures.append(f"runtime dependency relationship missing from SBOM: {name}")
    known_ids = set(package_ids)
    for item in relationships:
        if not isinstance(item, dict):
            failures.append("relationship entries must be objects")
            continue
        if item.get("spdxElementId") not in known_ids or item.get("relatedSpdxElement") not in known_ids:
            failures.append("relationship references an unknown SPDXID")
    if failures:
        raise ManifestError("release SBOM validation failed: {}".format("; ".join(sorted(set(failures)))))


def _verify_artifact_checksum(artifact: Path) -> str:
    artifact = artifact.resolve()
    if not artifact.is_file():
        raise ManifestError(f"release artifact is missing: {artifact}")
    checksum = artifact.with_name(artifact.name + ".sha256")
    if not checksum.is_file():
        raise ManifestError(f"release checksum is missing: {checksum}")
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
    members: list[tarfile.TarInfo] = []
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


def _release_source_root(release_root: Path) -> tuple[Manifest, Mapping[str, Any]]:
    source_root = release_root / "source"
    release_manifest_path = release_root / "release-manifest.json"
    if not source_root.is_dir() or not (source_root / "manifest.json").is_file():
        raise ManifestError("release archive does not contain its source distribution")
    try:
        release_manifest = json.loads(release_manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("release archive has an invalid release manifest") from exc
    if not isinstance(release_manifest, dict) or release_manifest.get("schema_version") != 2:
        raise ManifestError("release archive requires release manifest schema_version=2")
    top_manifest = Manifest.load(release_root)
    source_manifest = Manifest.load(source_root)
    if top_manifest.digest != source_manifest.digest:
        raise ManifestError("release top-level and source manifests differ")
    if release_manifest.get("manifest_sha256") != source_manifest.digest:
        raise ManifestError("release manifest digest does not match source manifest")
    if release_manifest.get("version") != source_manifest.version:
        raise ManifestError("release manifest version does not match source manifest")
    failures = source_manifest.validate(strict=True)
    if failures:
        raise ManifestError("release source manifest is invalid: {}".format("; ".join(failures)))
    return source_manifest, release_manifest



def _managed_hashes(target: Path) -> dict[str, str]:
    receipt_path = target / RECEIPT_NAME
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("release rehearsal receipt is invalid") from exc
    installed = receipt.get("installed")
    if not isinstance(installed, list) or not installed:
        raise ManifestError("release rehearsal receipt has no installed assets")
    hashes: dict[str, str] = {}
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

