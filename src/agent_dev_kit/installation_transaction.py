"""Transactional installation apply and rollback."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Set

from . import installation_contract as install_contract
from . import installation_plan
from .locking import TargetLock
from .model import Manifest, ManifestError, ensure_within, sha256_file, sha256_tree
from .targets import RenderedBundle

def apply_plan(manifest: Manifest, plan_path: Path, lock_timeout_seconds: float = 0.0) -> Dict[str, Any]:
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("install plan is invalid JSON: {}".format(plan_path)) from exc
    if not isinstance(plan, dict):
        raise ManifestError("install plan must be a JSON object")
    target_value = plan.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ManifestError("install plan target must be a non-empty string")
    target = install_contract._expand_target(target_value)
    with TargetLock(target, "install-apply", lock_timeout_seconds):
        validated_target, bundle = installation_plan.validate_plan(manifest, plan)
        return _apply_validated_plan(manifest, plan, validated_target, bundle)


def _apply_validated_plan(
    manifest: Manifest,
    plan: Mapping[str, Any],
    target: Path,
    bundle: RenderedBundle,
) -> Dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    run_id = install_contract._utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + str(plan["plan_id"])[:8]
    backup_root = ensure_within(target / ".adk-backups" / run_id, target, "backup root")
    staging_root = ensure_within(target / ".adk-staging" / run_id, target, "staging root")
    backup_root.mkdir(parents=True, exist_ok=False)
    try:
        staging_root.mkdir(parents=True, exist_ok=False)
    except Exception:
        shutil.rmtree(str(backup_root), ignore_errors=True)
        raise
    rendered_files = {item.destination: item for item in bundle.files}

    installed: List[Dict[str, Any]] = []
    deployed: List[str] = []
    moved_backups: List[Dict[str, str]] = []
    previous_receipt: Optional[str] = None
    previous_receipt_sha256: Optional[str] = None
    temp_receipt = target / (install_contract.RECEIPT_NAME + ".tmp")
    try:
        receipt_path = target / install_contract.RECEIPT_NAME
        if receipt_path.is_file():
            previous = backup_root / install_contract.RECEIPT_NAME
            shutil.copy2(str(receipt_path), str(previous))
            previous_receipt = previous.relative_to(target).as_posix()
            previous_receipt_sha256 = sha256_file(previous)
        for operation in plan["operations"]:
            rendered = rendered_files[str(operation["destination"])]
            destination = ensure_within(target / rendered.destination, target, "install destination")
            staged = ensure_within(staging_root / rendered.destination, staging_root, "staged install file")
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(rendered.content)
            staged.chmod(rendered.mode)

            backup_relative: Optional[str] = None
            backup_sha256: Optional[str] = None
            if destination.exists() or destination.is_symlink():
                backup = ensure_within(backup_root / rendered.destination, backup_root, "install backup")
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(backup))
                backup_relative = backup.relative_to(target).as_posix()
                backup_sha256 = sha256_tree(backup)
                moved_backups.append({"destination": rendered.destination, "backup": backup_relative})
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

        receipt = {
            "schema": install_contract.RECEIPT_SCHEMA,
            "receipt_id": run_id,
            "created_at": install_contract._iso(install_contract._utc_now()),
            "plan_id": plan["plan_id"],
            "manifest_version": manifest.version,
            "manifest_sha256": manifest.digest,
            "contract_sha256": bundle.contract.digest,
            "tool": plan["tool"],
            "target": str(target),
            "profiles": list(bundle.resolution.profiles),
            "optional_skills": list(bundle.optional_skills),
            "asset_kind": bundle.asset_kind,
            "backup_root": backup_root.relative_to(target).as_posix(),
            "previous_receipt": previous_receipt,
            "previous_receipt_sha256": previous_receipt_sha256,
            "installed": installed,
        }
        receipt["receipt_sha256"] = install_contract._receipt_digest(receipt)
        temp_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(str(temp_receipt), str(receipt_path))
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
                if backup.exists() or backup.is_symlink():
                    shutil.move(str(backup), str(destination))
            recovery_complete = True
        finally:
            temp_receipt.unlink(missing_ok=True)
            if recovery_complete:
                shutil.rmtree(str(backup_root), ignore_errors=True)
        raise
    finally:
        shutil.rmtree(str(staging_root), ignore_errors=True)


def rollback(receipt_path: Path, lock_timeout_seconds: float = 0.0) -> Dict[str, Any]:
    initial = install_contract._read_receipt(receipt_path, "rollback receipt")
    target_value = initial.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ManifestError("rollback receipt target must be a non-empty string")
    target = install_contract._expand_target(target_value)
    with TargetLock(target, "install-rollback", lock_timeout_seconds):
        return _rollback_locked(receipt_path)


def _rollback_locked(receipt_path: Path) -> Dict[str, Any]:
    receipt = install_contract._read_receipt(receipt_path, "rollback receipt")
    target = install_contract._expand_target(str(receipt.get("target", "")))
    resolved_receipt = ensure_within(receipt_path, target, "receipt path")
    expected_receipt = (target / install_contract.RECEIPT_NAME).resolve(strict=False)
    if resolved_receipt != expected_receipt:
        raise ManifestError("rollback receipt must be the active target receipt")
    installed = receipt.get("installed")
    if not isinstance(installed, list) or not installed:
        raise ManifestError("rollback receipt contains no installed assets")

    seen: Set[str] = set()
    for item in installed:
        if not isinstance(item, dict) or not item.get("destination"):
            raise ManifestError("rollback receipt contains an invalid asset")
        relative = str(item["destination"])
        if relative in seen:
            raise ManifestError("rollback receipt contains duplicate destinations")
        seen.add(relative)
        destination = ensure_within(target / relative, target, "rollback destination")
        if not destination.exists() and not destination.is_symlink():
            raise ManifestError("installed asset is missing; refusing rollback: {}".format(destination))
        if sha256_tree(destination) != item.get("installed_sha256"):
            raise ManifestError("installed asset changed; refusing rollback: {}".format(destination))
        backup_value = item.get("backup")
        if backup_value:
            backup = ensure_within(target / str(backup_value), target, "rollback backup")
            if not backup.exists() and not backup.is_symlink():
                raise ManifestError("rollback backup missing: {}".format(backup))
            backup_sha256 = item.get("backup_sha256")
            if not isinstance(backup_sha256, str) or sha256_tree(backup) != backup_sha256:
                raise ManifestError("rollback backup changed; refusing rollback: {}".format(backup))
        elif item.get("backup_sha256") is not None:
            raise ManifestError("rollback receipt has a backup digest without a backup")

    previous_receipt_value = receipt.get("previous_receipt")
    previous_receipt: Optional[Path] = None
    if previous_receipt_value:
        previous_receipt = ensure_within(target / str(previous_receipt_value), target, "previous receipt")
        if not previous_receipt.is_file() or previous_receipt.is_symlink():
            raise ManifestError("previous install receipt is missing")
        previous_receipt_sha256 = receipt.get("previous_receipt_sha256")
        if not isinstance(previous_receipt_sha256, str) or sha256_file(previous_receipt) != previous_receipt_sha256:
            raise ManifestError("previous install receipt changed; refusing rollback")
    elif receipt.get("previous_receipt_sha256") is not None:
        raise ManifestError("rollback receipt has a previous receipt digest without a previous receipt")

    receipt_id = str(receipt.get("receipt_id", ""))
    if not receipt_id:
        raise ManifestError("rollback receipt is missing receipt_id")
    rollback_staging = ensure_within(
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
            destination = ensure_within(target / str(item["destination"]), target, "rollback destination")
            staged = ensure_within(
                rollback_staging / str(item["destination"]), rollback_staging, "staged installed asset"
            )
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(staged))
            staged_installed.append({"destination": destination, "staged": staged})
            removed += 1
            backup_value = item.get("backup")
            if backup_value:
                backup = ensure_within(target / str(backup_value), target, "rollback backup")
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(backup), str(destination))
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
        for moved in reversed(restored_backups):
            moved["backup"].parent.mkdir(parents=True, exist_ok=True)
            if moved["destination"].exists() or moved["destination"].is_symlink():
                shutil.move(str(moved["destination"]), str(moved["backup"]))
        for moved in reversed(staged_installed):
            moved["destination"].parent.mkdir(parents=True, exist_ok=True)
            if moved["staged"].exists() or moved["staged"].is_symlink():
                shutil.move(str(moved["staged"]), str(moved["destination"]))
        raise
    finally:
        shutil.rmtree(str(rollback_staging), ignore_errors=True)

    backup_root_value = receipt.get("backup_root")
    if backup_root_value:
        backup_root = ensure_within(target / str(backup_root_value), target, "backup root")
        shutil.rmtree(str(backup_root), ignore_errors=True)
    return {"status": "pass", "removed": removed, "restored": restored, "target": str(target)}
