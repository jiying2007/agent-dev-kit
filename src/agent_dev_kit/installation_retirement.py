"""Source- and receipt-bound retirement helpers for governed install upgrades.

This module has no independent destructive entrypoint. Its callers hold the
install target lock and validate plans against the exact previous renderer.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Set

from . import installation_contract as install_contract
from .installation_inventory import verify_managed_file_mode
from .model import ManifestError, sha256_tree


def preview_retirements(plan: Mapping[str, Any], backup_root: Path, target: Path) -> List[Dict[str, Any]]:
    return [{
        "destination": row["destination"],
        "installed_sha256": row["installed_sha256"],
        "file_mode": row["file_mode"],
        "backup": (backup_root / row["destination"]).relative_to(target).as_posix(),
        "backup_sha256": "0" * 64,
    } for row in plan.get("retirements", [])]


def move_retirements(
    plan: Mapping[str, Any], target: Path, backup_root: Path,
    moved_backups: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    """Move only validated obsolete managed files; record moves before hashing.

    The parent transaction compensates every recorded move on any failure.
    """
    retired: List[Dict[str, Any]] = []
    for row in plan.get("retirements", []):
        relative = row["destination"]
        destination = install_contract._regular_install_path(
            target / relative, target, "retired managed destination"
        )
        backup = install_contract._regular_install_path(
            backup_root / relative, backup_root, "retired managed backup"
        )
        # Recheck immediately before moving: validation occurred under the
        # advisory lock, but an independent writer may still mutate a file
        # while the new bundle is being staged.
        if (not destination.is_file() or destination.is_symlink()
                or sha256_tree(destination) != row["installed_sha256"]):
            raise ManifestError("retired managed destination drifted before move")
        verify_managed_file_mode(destination, row["file_mode"], "retired managed destination")
        backup.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(destination), str(backup))
        moved_backups.append({
            "destination": relative,
            "backup": backup.relative_to(target).as_posix(),
        })
        retired.append({
            "destination": relative,
            "installed_sha256": row["installed_sha256"],
            "file_mode": row["file_mode"],
            "backup": backup.relative_to(target).as_posix(),
            "backup_sha256": sha256_tree(backup),
        })
    return retired


def verify_retired_rollback(
    retired: List[Mapping[str, Any]],
    previous_installed: Mapping[str, Mapping[str, Any]],
    installed_destinations: Set[str],
    target: Path, backup_root: Path,
) -> Set[str]:
    """Never let a local receipt digest authorize arbitrary file restoration."""
    expected = set(previous_installed).difference(installed_destinations)
    seen: Set[str] = set()
    for row in retired:
        if not isinstance(row, dict) or set(row) != {
            "destination", "installed_sha256", "file_mode", "backup", "backup_sha256"
        }:
            raise ManifestError("rollback has malformed retired managed asset")
        relative = row["destination"]
        if not isinstance(relative, str) or relative not in expected or relative in seen:
            raise ManifestError("rollback retirement is not in trusted previous inventory")
        seen.add(relative)
        old = previous_installed[relative]
        if row["installed_sha256"] != old["installed_sha256"] or row["file_mode"] != old["file_mode"]:
            raise ManifestError("rollback retired asset differs from trusted previous receipt")
        expected_backup = (backup_root / relative).relative_to(target).as_posix()
        if row["backup"] != expected_backup:
            raise ManifestError("rollback retired backup path is not canonical")
        destination = install_contract._regular_install_path(
            target / relative, target, "rollback retired destination"
        )
        if destination.exists() or destination.is_symlink():
            raise ManifestError("rollback retired destination is no longer absent")
        backup = install_contract._regular_install_path(
            target / expected_backup, target, "rollback retired backup"
        )
        if not backup.is_file() or backup.is_symlink() or sha256_tree(backup) != row["backup_sha256"]:
            raise ManifestError("rollback retired backup is missing or changed")
        if row["backup_sha256"] != old["installed_sha256"]:
            raise ManifestError("rollback retired backup differs from trusted previous asset")
        verify_managed_file_mode(backup, old["file_mode"], "rollback retired backup")
    if seen != expected:
        raise ManifestError("rollback omitted obsolete managed assets")
    return seen
