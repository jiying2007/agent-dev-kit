"""Deterministic release assembly and explicit publishing."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .compiler import export_assets
from .versioning import (
    VersioningError,
    validate_version,
    version_identity_failures,
    version_is_newer,
)
from .distribution import release_artifacts as _release_artifacts
from .installation_contract import RECEIPT_NAME
from .installation_plan import create_plan, write_plan
from .installation_transaction import apply_plan, rollback
from .model import Manifest, ManifestError, sha256_file, sha256_tree


def check_release(manifest: Manifest) -> Dict[str, Any]:
    failures = manifest.validate(strict=True)
    supported_adapters = {"claude-code", "opencode"}
    unsupported = sorted(set(manifest.direct_targets()).difference(supported_adapters))
    if unsupported:
        failures.append("missing compiler adapters: {}".format(", ".join(unsupported)))

    failures.extend(version_identity_failures(manifest.root))

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
            skill_version = _release_artifacts._skill_version(asset.path)
            relative = Path("skills") / asset.name / skill_version
            destination = package_root / relative
            file_count += _release_artifacts._copy_runtime_skill(asset.path, destination)
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
        _release_artifacts._write_runtime_checksums(package_root)

        archive = output / "adk-runtime-{}-{}.tar.gz".format(profile, version)
        _release_artifacts._write_deterministic_archive(package_root, archive)
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
    source_identity = _release_artifacts._release_source_identity(manifest.root, allow_unbound_snapshot)

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

        source_file_count = _release_artifacts._copy_source_distribution(manifest, package_root / "source")
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
        _release_artifacts._validate_sbom(sbom)
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
        _release_artifacts._write_deterministic_archive(package_root, archive)
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
    try:
        validate_version(version)
    except VersioningError as exc:
        raise ManifestError(str(exc)) from exc
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
    _release_artifacts._assert_publishable_release_artifact(artifact)
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

def rehearse_release(previous_artifact: Path, candidate_artifact: Path) -> Dict[str, Any]:
    previous_digest = _release_artifacts._verify_artifact_checksum(previous_artifact)
    candidate_digest = _release_artifacts._verify_artifact_checksum(candidate_artifact)
    workspace = Path(tempfile.mkdtemp(prefix="adk-release-rehearsal-"))
    try:
        previous_root = _release_artifacts._extract_release(previous_artifact.resolve(), workspace / "previous")
        candidate_root = _release_artifacts._extract_release(candidate_artifact.resolve(), workspace / "candidate")
        previous_manifest, previous_release_manifest = _release_artifacts._release_source_root(previous_root)
        candidate_manifest, candidate_release_manifest = _release_artifacts._release_source_root(candidate_root)
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
        try:
            candidate_is_newer = version_is_newer(previous_manifest.version, candidate_manifest.version)
        except VersioningError as exc:
            raise ManifestError(str(exc)) from exc
        if not candidate_is_newer:
            raise ManifestError("candidate release must be newer than previous release")

        target = workspace / "target"
        previous_plan_path = workspace / "previous-plan.json"
        previous_plan = create_plan(
            previous_manifest,
            "claude-code",
            str(target),
            [previous_manifest.default_profile],
            [],
            "copy",
        )
        if previous_plan["status"] != "ready":
            raise ManifestError("previous release install plan is not ready")
        write_plan(previous_plan, previous_plan_path)
        previous_apply = apply_plan(previous_manifest, previous_plan_path)
        previous_hashes = _release_artifacts._managed_hashes(target)

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
        restored_receipt = json.loads((target / RECEIPT_NAME).read_text(encoding="utf-8"))
        restored_hashes = _release_artifacts._managed_hashes(target)
        if restored_receipt.get("manifest_version") != previous_manifest.version:
            raise ManifestError("rollback did not restore the previous receipt")
        if restored_hashes != previous_hashes:
            raise ManifestError("rollback did not restore the previous managed asset hashes")
        result = {
            "schema_version": 3,
            "status": "pass",
            "previous_version": previous_manifest.version,
            "candidate_version": candidate_manifest.version,
            "previous_sha256": previous_digest,
            "candidate_sha256": candidate_digest,
            "previous_manifest_sha256": previous_release_manifest["manifest_sha256"],
            "candidate_manifest_sha256": candidate_release_manifest["manifest_sha256"],
            "previous_installed": previous_apply["installed"],
            "candidate_installed": candidate_apply["installed"],
            "rollback": {
                "status": rollback_result["status"],
                "removed": rollback_result["removed"],
                "restored": rollback_result["restored"],
            },
            "restored_assets": len(restored_hashes),
            "remote_publish": "not-in-scope",
        }
        result["report_sha256"] = _release_artifacts._report_digest(result)
        return result
    finally:
        shutil.rmtree(str(workspace), ignore_errors=True)
