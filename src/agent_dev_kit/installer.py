"""Plan/apply/rollback installer with ownership receipts."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from .model import Manifest, ManifestError, ensure_within, sha256_tree


PLAN_SCHEMA = "adk-install-plan/v1"
RECEIPT_SCHEMA = "adk-install-receipt/v1"
RECEIPT_NAME = ".adk-install-receipt.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _expand_target(value: str) -> Path:
    expanded = os.path.expanduser(value)
    if "$" in expanded or "`" in expanded or "\x00" in expanded:
        raise ManifestError("dynamic target paths are forbidden: {}".format(value))
    return Path(expanded).resolve()


def _load_receipt(target: Path) -> Optional[Mapping[str, Any]]:
    path = target / RECEIPT_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != RECEIPT_SCHEMA:
        raise ManifestError("unsupported existing install receipt")
    return data


def create_plan(
    manifest: Manifest,
    tool: str,
    target_value: str,
    profiles: Sequence[str],
    optional_skills: Sequence[str],
    mode: str,
    ttl_minutes: int = 60,
) -> Dict[str, Any]:
    if mode not in ("copy", "symlink"):
        raise ManifestError("install mode must be copy or symlink")
    if ttl_minutes < 1 or ttl_minutes > 1440:
        raise ManifestError("install plan TTL must be between 1 and 1440 minutes")
    target_config = manifest.target(tool)
    target = _expand_target(target_value)
    resolution = manifest.resolve_profiles(profiles, optional_skills)
    agents_dir = str(target_config.get("agents_dir", "agents"))
    skills_dir = str(target_config.get("skills_dir", "skills"))
    existing_receipt = _load_receipt(target) if target.exists() else None
    managed: Dict[str, Mapping[str, Any]] = {}
    if existing_receipt:
        if existing_receipt.get("target") != str(target):
            raise ManifestError("existing install receipt target does not match its location")
        for item in existing_receipt.get("installed", []):
            if not isinstance(item, dict) or not item.get("destination"):
                raise ManifestError("existing install receipt contains an invalid asset")
            relative = str(item["destination"])
            ensure_within(target / relative, target, "managed destination")
            if relative in managed:
                raise ManifestError("existing install receipt contains duplicate destinations")
            managed[relative] = item

    operations: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, str]] = []
    assets = list(resolution.agents) + list(resolution.skills)
    for asset in assets:
        base = agents_dir if asset.kind == "agent" else skills_dir
        destination = ensure_within(target / base / asset.name, target, "install destination")
        relative = destination.relative_to(target).as_posix()
        action = "create"
        destination_sha256: Optional[str] = None
        if destination.exists() or destination.is_symlink():
            if relative not in managed:
                conflicts.append({"destination": relative, "reason": "unmanaged destination exists"})
                action = "conflict"
            elif sha256_tree(destination) != managed[relative].get("installed_sha256"):
                conflicts.append({"destination": relative, "reason": "managed destination drifted"})
                action = "conflict"
            else:
                action = "replace-managed"
                destination_sha256 = sha256_tree(destination)
        operations.append(
            {
                "kind": asset.kind,
                "name": asset.name,
                "source": asset.path.relative_to(manifest.root).as_posix(),
                "source_sha256": asset.digest,
                "destination": relative,
                "destination_sha256": destination_sha256,
                "action": action,
                "mode": mode,
            }
        )

    requested = {str(item["destination"]) for item in operations}
    for relative in sorted(set(managed).difference(requested)):
        conflicts.append(
            {
                "destination": relative,
                "reason": "managed destination is outside requested profile; rollback current install first",
            }
        )

    now = _utc_now()
    return {
        "schema": PLAN_SCHEMA,
        "status": "needs-review" if conflicts else "ready",
        "plan_id": str(uuid.uuid4()),
        "created_at": _iso(now),
        "expires_at": _iso(now + timedelta(minutes=ttl_minutes)),
        "manifest_version": manifest.version,
        "manifest_sha256": manifest.digest,
        "tool": tool,
        "target": str(target),
        "profiles": list(resolution.profiles),
        "optional_skills": list(optional_skills),
        "operations": operations,
        "conflicts": conflicts,
    }


def write_plan(plan: Mapping[str, Any], output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(temp), str(output))


def _validate_plan(manifest: Manifest, plan: Mapping[str, Any]) -> Path:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ManifestError("unsupported install plan schema")
    if plan.get("status") != "ready" or plan.get("conflicts"):
        raise ManifestError("install plan has unresolved conflicts")
    if plan.get("manifest_version") != manifest.version or plan.get("manifest_sha256") != manifest.digest:
        raise ManifestError("manifest changed after install plan creation")
    try:
        expires = _parse_time(str(plan.get("expires_at", "")))
    except (TypeError, ValueError) as exc:
        raise ManifestError("install plan has an invalid expiry") from exc
    if _utc_now() > expires:
        raise ManifestError("install plan expired")
    target = _expand_target(str(plan.get("target", "")))
    tool = plan.get("tool")
    profiles = plan.get("profiles")
    optional_skills = plan.get("optional_skills")
    operations = plan.get("operations")
    if not isinstance(tool, str):
        raise ManifestError("install plan tool must be a string")
    if not isinstance(profiles, list) or not profiles or not all(isinstance(item, str) for item in profiles):
        raise ManifestError("install plan profiles must be a non-empty string array")
    if not isinstance(optional_skills, list) or not all(isinstance(item, str) for item in optional_skills):
        raise ManifestError("install plan optional_skills must be a string array")
    if not isinstance(operations, list) or not operations:
        raise ManifestError("install plan operations must be a non-empty array")

    target_config = manifest.target(tool)
    resolution = manifest.resolve_profiles(profiles, optional_skills)
    expected: Dict[tuple, Dict[str, str]] = {}
    for asset in list(resolution.agents) + list(resolution.skills):
        base = str(target_config["agents_dir"] if asset.kind == "agent" else target_config["skills_dir"])
        destination = ensure_within(target / base / asset.name, target, "install destination")
        expected[(asset.kind, asset.name)] = {
            "source": asset.path.relative_to(manifest.root).as_posix(),
            "destination": destination.relative_to(target).as_posix(),
        }

    seen: Set[tuple] = set()
    for operation in operations:
        if not isinstance(operation, dict):
            raise ManifestError("install operation must be an object")
        key = (operation.get("kind"), operation.get("name"))
        if key not in expected or key in seen:
            raise ManifestError("install plan contains an unknown or duplicate asset: {}".format(key))
        seen.add(key)
        if operation.get("source") != expected[key]["source"]:
            raise ManifestError("install source does not match manifest asset: {}".format(key))
        if operation.get("destination") != expected[key]["destination"]:
            raise ManifestError("install destination does not match target adapter: {}".format(key))
        if operation.get("mode") not in ("copy", "symlink"):
            raise ManifestError("install operation has invalid mode: {}".format(operation.get("mode")))
        if operation.get("action") not in ("create", "replace-managed"):
            raise ManifestError("install operation has invalid action: {}".format(operation.get("action")))
        source = ensure_within(manifest.root / str(operation.get("source", "")), manifest.root, "install source")
        destination = ensure_within(target / str(operation.get("destination", "")), target, "install destination")
        if not source.exists():
            raise ManifestError("install source missing: {}".format(source))
        if sha256_tree(source) != operation.get("source_sha256"):
            raise ManifestError("install source changed: {}".format(source))
        if operation.get("action") == "create" and (destination.exists() or destination.is_symlink()):
            raise ManifestError("destination appeared after plan creation: {}".format(destination))
        if operation.get("action") == "replace-managed":
            if not destination.exists() and not destination.is_symlink():
                raise ManifestError("managed destination disappeared after plan creation: {}".format(destination))
            if sha256_tree(destination) != operation.get("destination_sha256"):
                raise ManifestError("managed destination changed after plan creation: {}".format(destination))
    if seen != set(expected):
        raise ManifestError("install plan does not contain the complete resolved asset set")
    return target


def apply_plan(manifest: Manifest, plan_path: Path) -> Dict[str, Any]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    target = _validate_plan(manifest, plan)
    target.mkdir(parents=True, exist_ok=True)
    run_id = _utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + str(plan["plan_id"])[:8]
    backup_root = ensure_within(target / ".adk-backups" / run_id, target, "backup root")
    staging_root = ensure_within(target / ".adk-staging" / run_id, target, "staging root")
    backup_root.mkdir(parents=True, exist_ok=False)
    staging_root.mkdir(parents=True, exist_ok=False)

    installed: List[Dict[str, Any]] = []
    deployed: List[str] = []
    moved_backups: List[Dict[str, str]] = []
    previous_receipt: Optional[str] = None
    try:
        receipt_path = target / RECEIPT_NAME
        if receipt_path.is_file():
            previous = backup_root / RECEIPT_NAME
            shutil.copy2(str(receipt_path), str(previous))
            previous_receipt = previous.relative_to(target).as_posix()
        for operation in plan["operations"]:
            source = manifest.root / operation["source"]
            destination = target / operation["destination"]
            staged = staging_root / operation["destination"]
            staged.parent.mkdir(parents=True, exist_ok=True)
            if operation["mode"] == "copy":
                shutil.copytree(str(source), str(staged), symlinks=True)
            else:
                os.symlink(str(source), str(staged), target_is_directory=True)

            backup_relative: Optional[str] = None
            if destination.exists() or destination.is_symlink():
                backup = backup_root / operation["destination"]
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(backup))
                backup_relative = backup.relative_to(target).as_posix()
                moved_backups.append({"destination": operation["destination"], "backup": backup_relative})
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(str(staged), str(destination))
            deployed.append(operation["destination"])
            installed.append(
                {
                    "kind": operation["kind"],
                    "name": operation["name"],
                    "destination": operation["destination"],
                    "source_sha256": operation["source_sha256"],
                    "installed_sha256": sha256_tree(destination),
                    "backup": backup_relative,
                }
            )

        receipt = {
            "schema": RECEIPT_SCHEMA,
            "receipt_id": run_id,
            "created_at": _iso(_utc_now()),
            "plan_id": plan["plan_id"],
            "manifest_version": manifest.version,
            "manifest_sha256": manifest.digest,
            "tool": plan["tool"],
            "target": str(target),
            "backup_root": backup_root.relative_to(target).as_posix(),
            "previous_receipt": previous_receipt,
            "installed": installed,
        }
        temp_receipt = target / (RECEIPT_NAME + ".tmp")
        temp_receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(str(temp_receipt), str(receipt_path))
        return {"status": "pass", "receipt": str(receipt_path), "installed": len(installed), "backup": str(backup_root)}
    except Exception:
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
        raise
    finally:
        shutil.rmtree(str(staging_root), ignore_errors=True)


def rollback(receipt_path: Path) -> Dict[str, Any]:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise ManifestError("unsupported rollback receipt schema")
    target = _expand_target(str(receipt.get("target", "")))
    resolved_receipt = ensure_within(receipt_path, target, "receipt path")
    expected_receipt = (target / RECEIPT_NAME).resolve(strict=False)
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

    previous_receipt_value = receipt.get("previous_receipt")
    previous_receipt: Optional[Path] = None
    if previous_receipt_value:
        previous_receipt = ensure_within(target / str(previous_receipt_value), target, "previous receipt")
        if not previous_receipt.is_file():
            raise ManifestError("previous install receipt is missing")

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
