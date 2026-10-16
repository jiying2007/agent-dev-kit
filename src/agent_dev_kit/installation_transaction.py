"""Transactional installation apply and rollback."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set

from . import installation_contract as install_contract
from . import installation_plan
from .installation_inventory import verify_managed_file_mode, verify_receipt_inventory
from .locking import TargetLock
from .model import Manifest, ManifestError, sha256_file, sha256_tree
from .targets import RenderedBundle
from .strict_json import StrictJSONError, read as read_strict_json


def _refuse_incomplete_transactions(target: Path) -> None:
    """Fail closed if a previous interrupted apply/rollback retained evidence.

    Successful transactions remove their run-specific staging directories. A
    retained directory is recovery material, even when all of its staged files
    were moved before the failure; do not overwrite the still-active receipt.
    """
    for name in (".adk-staging", ".adk-rollback-staging"):
        staging = target / name
        if staging.is_symlink():
            raise ManifestError("install recovery staging is a symlink: {}".format(staging))
        if not staging.exists():
            continue
        if not staging.is_dir() or any(staging.iterdir()):
            raise ManifestError(
                "unresolved ADK transaction staging; preserve for recovery: {}".format(staging)
            )

def apply_plan(manifest: Manifest, plan_path: Path, lock_timeout_seconds: float = 0.0) -> Dict[str, Any]:
    try:
        if plan_path.is_symlink() or not plan_path.is_file():
            raise StrictJSONError("install plan must be a regular file")
        plan = read_strict_json(plan_path, regular_only=True)
    except StrictJSONError as exc:
        raise ManifestError("install plan is invalid JSON: {}".format(plan_path)) from exc
    if not isinstance(plan, dict):
        raise ManifestError("install plan must be a JSON object")
    target_value = plan.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ManifestError("install plan target must be a non-empty string")
    target = install_contract._expand_target(target_value)
    with TargetLock(target, "install-apply", lock_timeout_seconds):
        _refuse_incomplete_transactions(target)
        validated_target, bundle = installation_plan.validate_plan(manifest, plan)
        return _apply_validated_plan(manifest, plan, validated_target, bundle)


def _apply_validated_plan(
    manifest: Manifest,
    plan: Mapping[str, Any],
    target: Path,
    bundle: RenderedBundle,
) -> Dict[str, Any]:
    run_id = install_contract._utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + str(plan["plan_id"])[:8]
    backup_root = install_contract._regular_install_path(target / ".adk-backups" / run_id, target, "backup root")
    staging_root = install_contract._regular_install_path(target / ".adk-staging" / run_id, target, "staging root")
    rendered_files = {item.destination: item for item in bundle.files}
    # Conservative replacement preview: backup paths/digests are longer than
    # nulls for new assets. Reject before creating transaction directories or
    # moving assets, then check the actual document again before publication.
    preview = []
    for operation in plan["operations"]:
        rendered = rendered_files[str(operation["destination"])]
        preview.append({
            "kind": rendered.kind, "name": rendered.name, "source": rendered.source,
            "destination": rendered.destination, "source_sha256": operation["source_sha256"],
            "rendered_sha256": rendered.sha256, "installed_sha256": "0" * 64,
            "file_mode": format(rendered.mode, "04o"),
            "backup": (backup_root / rendered.destination).relative_to(target).as_posix(),
            "backup_sha256": "0" * 64,
        })
    receipt = {
        "schema": install_contract.RECEIPT_SCHEMA,
        "receipt_id": run_id,
        "created_at": install_contract._iso(install_contract._utc_now()),
        "plan_id": plan["plan_id"], "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest, "contract_sha256": bundle.contract.digest,
        "tool": plan["tool"], "target": str(target),
        "profiles": list(bundle.resolution.profiles), "optional_skills": list(bundle.optional_skills),
        "asset_kind": bundle.asset_kind,
        "backup_root": backup_root.relative_to(target).as_posix(),
        "previous_receipt": (backup_root / install_contract.RECEIPT_NAME).relative_to(target).as_posix(),
        "previous_receipt_sha256": "0" * 64, "installed": preview,
        "receipt_sha256": "0" * 64,
    }
    install_contract._encode_document(receipt, "install receipt preview")
    target.mkdir(parents=True, exist_ok=True)
    backup_root.mkdir(parents=True, exist_ok=False)
    try:
        staging_root.mkdir(parents=True, exist_ok=False)
    except Exception:
        shutil.rmtree(str(backup_root), ignore_errors=True)
        raise

    installed: List[Dict[str, Any]] = []
    deployed: List[str] = []
    moved_backups: List[Dict[str, str]] = []
    previous_receipt: Optional[str] = None
    previous_receipt_sha256: Optional[str] = None
    preserve_staging = False
    try:
        receipt_path = target / install_contract.RECEIPT_NAME
        if receipt_path.is_file():
            previous = backup_root / install_contract.RECEIPT_NAME
            shutil.copy2(str(receipt_path), str(previous))
            previous_receipt = previous.relative_to(target).as_posix()
            previous_receipt_sha256 = sha256_file(previous)
        for operation in plan["operations"]:
            rendered = rendered_files[str(operation["destination"])]
            destination = install_contract._regular_install_path(target / rendered.destination, target, "install destination")
            staged = install_contract._regular_install_path(staging_root / rendered.destination, staging_root, "staged install file")
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(rendered.content)
            staged.chmod(rendered.mode)

            backup_relative: Optional[str] = None
            backup_sha256: Optional[str] = None
            if destination.exists() or destination.is_symlink():
                backup = install_contract._regular_install_path(backup_root / rendered.destination, backup_root, "install backup")
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup_relative = backup.relative_to(target).as_posix()
                # Fail atomically on cross-filesystem targets instead of letting
                # shutil.move perform a partially completed copy/delete.
                os.replace(str(destination), str(backup))
                # Register the successfully moved asset BEFORE the next I/O:
                # digest reads may fail and must not orphan the only copy.
                moved_backups.append({"destination": rendered.destination, "backup": backup_relative})
                backup_sha256 = sha256_tree(backup)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(staged), str(destination))
            deployed.append(rendered.destination)
            installed.append(
                {
                    "kind": rendered.kind,
                    "name": rendered.name,
                    "source": rendered.source,
                    "destination": rendered.destination,
                    "source_sha256": operation["source_sha256"],
                    "rendered_sha256": rendered.sha256,
                    "installed_sha256": sha256_tree(destination),
                    "file_mode": format(rendered.mode, "04o"),
                    "backup": backup_relative,
                    "backup_sha256": backup_sha256,
                }
            )

        receipt.update(installed=installed, previous_receipt=previous_receipt,
                       previous_receipt_sha256=previous_receipt_sha256)
        receipt["receipt_sha256"] = install_contract._receipt_digest(receipt)
        text = install_contract._encode_document(receipt, "install receipt")
        install_contract._write_document(text, receipt_path)
        return {
            "schema": "adk-install-result/v2",
            "status": "pass",
            "receipt": str(receipt_path),
            "installed": len(installed),
            "backup": str(backup_root),
        }
    except Exception:
        recovery_complete = False
        try:
            for relative in reversed(deployed):
                destination = target / relative
                if destination.is_symlink() or destination.is_file():
                    destination.unlink()
                elif destination.is_dir():
                    shutil.rmtree(str(destination))
            for item in reversed(moved_backups):
                destination = target / item["destination"]
                backup = target / item["backup"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not (backup.exists() or backup.is_symlink()):
                    raise ManifestError("install recovery backup missing: {}".format(backup))
                os.replace(str(backup), str(destination))
            recovery_complete = True
        finally:
            if recovery_complete:
                shutil.rmtree(str(backup_root), ignore_errors=True)
            else:
                # The only recoverable snapshot may be in backups/staging.
                # A retained run directory also blocks later apply/rollback.
                preserve_staging = True
        raise
    finally:
        if not preserve_staging:
            shutil.rmtree(str(staging_root), ignore_errors=True)


_RECEIPT_RUN_ID = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")


def _rollback_backup_root(receipt: Mapping[str, Any], target: Path) -> Path:
    """Bind destructive rollback cleanup to the directory created by apply.

    A receipt SHA-256 proves content consistency, not that its path fields
    authorize deletion of an arbitrary directory inside the install target.
    Validate identity before staging/moving any managed files.
    """
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or _RECEIPT_RUN_ID.fullmatch(receipt_id) is None:
        raise ManifestError("rollback receipt_id is not a canonical install run identifier")
    relative = ".adk-backups/" + receipt_id
    if receipt.get("backup_root") != relative:
        raise ManifestError("rollback backup root does not match receipt identity")
    root = install_contract._regular_install_path(target / relative, target, "rollback backup root")
    if not root.is_dir():
        raise ManifestError("rollback backup root is missing or invalid: {}".format(root))
    return root


def _verify_backup_inventory(receipt: Mapping[str, Any], backup_root: Path) -> None:
    """Reject omitted/extra backup files before destructive directory cleanup."""
    expected: Set[str] = {
        str(item["destination"]) for item in receipt["installed"] if item.get("backup") is not None
    }
    if receipt.get("previous_receipt") is not None:
        expected.add(install_contract.RECEIPT_NAME)
    actual: Set[str] = set()
    limit = max(32, len(expected) * 8 + 16)
    for count, candidate in enumerate(backup_root.rglob("*"), 1):
        if count > limit:
            raise ManifestError("rollback backup inventory exceeds entry budget")
        relative = candidate.relative_to(backup_root).as_posix()
        if candidate.is_symlink():
            raise ManifestError("rollback backup inventory contains a symlink")
        if candidate.is_file():
            actual.add(relative)
        elif candidate.is_dir():
            if not any(path.startswith(relative + "/") for path in expected):
                raise ManifestError("rollback backup inventory contains an unlisted directory")
        else:
            raise ManifestError("rollback backup inventory contains a non-regular entry")
    if actual != expected:
        raise ManifestError("rollback backup inventory differs from receipt references")


def rollback(receipt_path: Path, lock_timeout_seconds: float = 0.0, *, manifest: Manifest) -> Dict[str, Any]:
    initial = install_contract._read_receipt(receipt_path, "rollback receipt")
    target_value = initial.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ManifestError("rollback receipt target must be a non-empty string")
    target = install_contract._expand_target(target_value)
    with TargetLock(target, "install-rollback", lock_timeout_seconds):
        _refuse_incomplete_transactions(target)
        return _rollback_locked(receipt_path, manifest, locked_target=target)


def _rollback_locked(receipt_path: Path, manifest: Manifest, *, locked_target: Path) -> Dict[str, Any]:
    receipt = install_contract._read_receipt(receipt_path, "rollback receipt")
    target = install_contract._expand_target(str(receipt.get("target", "")))
    if target != locked_target:
        raise ManifestError("rollback receipt target changed after acquiring target lock")
    resolved_receipt = install_contract._regular_install_path(receipt_path, target, "receipt path")
    expected_receipt = (target / install_contract.RECEIPT_NAME).resolve(strict=False)
    if resolved_receipt != expected_receipt:
        raise ManifestError("rollback receipt must be the active target receipt")
    backup_root = _rollback_backup_root(receipt, target)
    verify_receipt_inventory(manifest, receipt)
    installed = receipt.get("installed")
    if not isinstance(installed, list) or not installed:
        raise ManifestError("rollback receipt contains no installed assets")

    seen: Set[str] = set()
    for item in installed:
        if not isinstance(item, dict) or not isinstance(item.get("destination"), str):
            raise ManifestError("rollback receipt contains an invalid asset")
        relative = item["destination"]
        segments = relative.split("/")
        if (
            not relative or "\\" in relative or any(seg in ("", ".", "..") for seg in segments)
            or segments[0] in (".adk-backups", ".adk-staging", ".adk-rollback-staging", install_contract.RECEIPT_NAME)
        ):
            raise ManifestError("rollback destination is not a canonical managed asset path: {}".format(relative))
        if relative in seen:
            raise ManifestError("rollback receipt contains duplicate destinations")
        seen.add(relative)
        destination = install_contract._regular_install_path(target / relative, target, "rollback destination")
        if not destination.exists() and not destination.is_symlink():
            raise ManifestError("installed asset is missing; refusing rollback: {}".format(destination))
        if sha256_tree(destination) != item.get("installed_sha256"):
            raise ManifestError("installed asset changed; refusing rollback: {}".format(destination))
        verify_managed_file_mode(destination, item.get("file_mode"), "rollback installed asset")
        backup_value = item.get("backup")
        if backup_value is not None:
            expected_backup = (backup_root / relative).relative_to(target).as_posix()
            if backup_value != expected_backup:
                raise ManifestError("rollback backup path does not match managed asset identity: {}".format(relative))
            backup = install_contract._regular_install_path(target / backup_value, target, "rollback backup")
            if not backup.exists() and not backup.is_symlink():
                raise ManifestError("rollback backup missing: {}".format(backup))
            backup_sha256 = item.get("backup_sha256")
            if not isinstance(backup_sha256, str) or sha256_tree(backup) != backup_sha256:
                raise ManifestError("rollback backup changed; refusing rollback: {}".format(backup))
            verify_managed_file_mode(backup, item.get("file_mode"), "rollback managed backup")
        elif item.get("backup_sha256") is not None:
            raise ManifestError("rollback receipt has a backup digest without a backup")

    previous_receipt_value = receipt.get("previous_receipt")
    previous_receipt: Optional[Path] = None
    if previous_receipt_value is not None:
        expected_previous = (backup_root / install_contract.RECEIPT_NAME).relative_to(target).as_posix()
        if previous_receipt_value != expected_previous:
            raise ManifestError("rollback previous receipt path does not match run identity")
        previous_receipt = install_contract._regular_install_path(target / previous_receipt_value, target, "previous receipt")
        if not previous_receipt.is_file() or previous_receipt.is_symlink():
            raise ManifestError("previous install receipt is missing")
        previous_receipt_sha256 = receipt.get("previous_receipt_sha256")
        if not isinstance(previous_receipt_sha256, str) or sha256_file(previous_receipt) != previous_receipt_sha256:
            raise ManifestError("previous install receipt changed; refusing rollback")
    elif receipt.get("previous_receipt_sha256") is not None:
        raise ManifestError("rollback receipt has a previous receipt digest without a previous receipt")

    _verify_backup_inventory(receipt, backup_root)
    receipt_id = backup_root.name
    rollback_staging = install_contract._regular_install_path(
        target / ".adk-rollback-staging" / receipt_id,
        target,
        "rollback staging",
    )
    rollback_staging.mkdir(parents=True, exist_ok=False)
    restored = 0
    removed = 0
    staged_installed: List[Dict[str, Path]] = []
    restored_backups: List[Dict[str, Path]] = []
    try:
        for item in reversed(installed):
            destination = install_contract._regular_install_path(target / str(item["destination"]), target, "rollback destination")
            staged = install_contract._regular_install_path(
                rollback_staging / str(item["destination"]), rollback_staging, "staged installed asset"
            )
            staged.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(destination), str(staged))
            staged_installed.append({"destination": destination, "staged": staged})
            removed += 1
            backup_value = item.get("backup")
            if backup_value:
                backup = install_contract._regular_install_path(target / str(backup_value), target, "rollback backup")
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(str(backup), str(destination))
                restored_backups.append({"destination": destination, "backup": backup})
                restored += 1
        if previous_receipt is not None:
            os.replace(str(previous_receipt), str(receipt_path))
        else:
            receipt_path.unlink()
        for item in installed:
            current = (target / str(item["destination"])).parent
            while current != target and not current.name.startswith(".adk-"):
                try:
                    current.rmdir()
                except OSError:
                    break
                current = current.parent
    except Exception:
        recovery_complete = False
        try:
            for moved in reversed(restored_backups):
                moved["backup"].parent.mkdir(parents=True, exist_ok=True)
                if not (moved["destination"].exists() or moved["destination"].is_symlink()):
                    raise ManifestError("rollback compensation source missing: {}".format(moved["destination"]))
                os.replace(str(moved["destination"]), str(moved["backup"]))
            for moved in reversed(staged_installed):
                moved["destination"].parent.mkdir(parents=True, exist_ok=True)
                if not (moved["staged"].exists() or moved["staged"].is_symlink()):
                    raise ManifestError("rollback compensation staged asset missing: {}".format(moved["staged"]))
                os.replace(str(moved["staged"]), str(moved["destination"]))
            recovery_complete = True
        finally:
            # A second failure MUST retain the staged installed assets; deleting
            # them would destroy the only remaining recoverable copy.
            if recovery_complete:
                shutil.rmtree(str(rollback_staging), ignore_errors=True)
        raise
    else:
        shutil.rmtree(str(rollback_staging), ignore_errors=True)

    shutil.rmtree(str(backup_root), ignore_errors=True)
    return {"status": "pass", "removed": removed, "restored": restored, "target": str(target)}
