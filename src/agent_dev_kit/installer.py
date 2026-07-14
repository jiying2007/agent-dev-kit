"""Plan/apply/rollback installer with ownership receipts."""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .locking import TargetLock
from .model import (
    Manifest,
    ManifestError,
    canonical_json_bytes,
    ensure_within,
    sha256_bytes,
    sha256_file,
    sha256_tree,
)
from .targets import RenderedBundle, TargetUsageError, render_selection


PLAN_SCHEMA = "adk-install-plan/v2"
LEGACY_RECEIPT_SCHEMA = "adk-install-receipt/v1"
PREVIOUS_RECEIPT_SCHEMA = "adk-install-receipt/v2"
RECEIPT_SCHEMA = "adk-install-receipt/v3"
RECEIPT_NAME = ".adk-install-receipt.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _expand_target(value: str) -> Path:
    if not value.strip():
        raise ManifestError("target path must be a non-empty string")
    expanded = os.path.expanduser(value)
    if "$" in expanded or "`" in expanded or "\x00" in expanded:
        raise ManifestError("dynamic target paths are forbidden: {}".format(value))
    return Path(expanded).resolve()


def _receipt_digest(data: Mapping[str, Any]) -> str:
    content = dict(data)
    content.pop("receipt_sha256", None)
    return sha256_bytes(canonical_json_bytes(content))


def _read_receipt(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink():
        raise ManifestError("{} must not be a symlink: {}".format(label, path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid JSON: {}".format(label, path)) from exc
    if not isinstance(data, dict):
        raise ManifestError("{} must be a JSON object".format(label))
    schema = data.get("schema")
    if schema not in (LEGACY_RECEIPT_SCHEMA, PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA):
        raise ManifestError("unsupported {} schema".format(label))
    if schema in (PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA):
        stored_digest = data.get("receipt_sha256")
        if not isinstance(stored_digest, str) or stored_digest != _receipt_digest(data):
            raise ManifestError("{} digest does not match content".format(label))
    return data


def _load_receipt(target: Path) -> Optional[Mapping[str, Any]]:
    path = target / RECEIPT_NAME
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink() or not path.is_file():
        raise ManifestError("existing install receipt must be a regular file: {}".format(path))
    return _read_receipt(path, "existing install receipt")


def create_plan(
    manifest: Manifest,
    tool: str,
    target_value: str,
    profiles: Sequence[str],
    optional_skills: Sequence[str],
    mode: str,
    ttl_minutes: int = 60,
    asset_kind: Optional[str] = None,
) -> Dict[str, Any]:
    if mode != "copy":
        if mode == "symlink":
            raise TargetUsageError("unsupported_install_mode: symlink; use --mode copy")
        raise TargetUsageError("unsupported_install_mode: {}; use --mode copy".format(mode))
    if ttl_minutes < 1 or ttl_minutes > 1440:
        raise ManifestError("install plan TTL must be between 1 and 1440 minutes")
    bundle = render_selection(manifest, tool, profiles, optional_skills, asset_kind)
    target = _expand_target(target_value)
    receipt_path = target / RECEIPT_NAME
    existing_receipt = _load_receipt(target) if target.exists() else None
    active_receipt_sha256: Optional[str] = None
    managed: Dict[str, Mapping[str, Any]] = {}
    if existing_receipt:
        if existing_receipt.get("target") != str(target):
            raise ManifestError("existing install receipt target does not match its location")
        if existing_receipt.get("tool") != tool:
            raise ManifestError("existing install receipt tool does not match requested target")
        if existing_receipt.get("schema") != RECEIPT_SCHEMA:
            raise TargetUsageError(
                "legacy_receipt_requires_rollback: rollback the active v1/v2 receipt before creating a v2 plan"
            )
        active_receipt_sha256 = sha256_file(receipt_path)
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
    for rendered in bundle.files:
        destination = ensure_within(target / rendered.destination, target, "install destination")
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
                "kind": rendered.kind,
                "name": rendered.name,
                "source": rendered.source,
                "source_sha256": sha256_file(manifest.root / rendered.source),
                "rendered_sha256": rendered.sha256,
                "destination": relative,
                "destination_sha256": destination_sha256,
                "action": action,
                "mode": "copy",
                "file_mode": format(rendered.mode, "04o"),
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
        "contract_sha256": bundle.contract.digest,
        "active_receipt_sha256": active_receipt_sha256,
        "tool": tool,
        "target": str(target),
        "profiles": list(bundle.resolution.profiles),
        "optional_skills": list(optional_skills),
        "asset_kind": asset_kind,
        "operations": operations,
        "conflicts": conflicts,
    }


def write_plan(plan: Mapping[str, Any], output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    temp.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(temp), str(output))


def _validate_plan(manifest: Manifest, plan: Mapping[str, Any]) -> Tuple[Path, RenderedBundle]:
    if plan.get("schema") != PLAN_SCHEMA:
        raise ManifestError(
            "unsupported install plan schema: {}; regenerate with install plan".format(
                plan.get("schema")
            )
        )
    if plan.get("status") != "ready" or plan.get("conflicts"):
        raise ManifestError("install plan has unresolved conflicts")
    if plan.get("manifest_version") != manifest.version or plan.get("manifest_sha256") != manifest.digest:
        raise ManifestError("manifest changed after install plan creation")
    plan_id = plan.get("plan_id")
    try:
        parsed_plan_id = uuid.UUID(str(plan_id))
    except (ValueError, AttributeError) as exc:
        raise ManifestError("install plan has an invalid plan_id") from exc
    if not isinstance(plan_id, str) or str(parsed_plan_id) != plan_id or parsed_plan_id.version != 4:
        raise ManifestError("install plan has an invalid plan_id")
    try:
        created = _parse_time(str(plan.get("created_at", "")))
        expires = _parse_time(str(plan.get("expires_at", "")))
    except (TypeError, ValueError) as exc:
        raise ManifestError("install plan has invalid timestamps") from exc
    now = _utc_now()
    if created > now + timedelta(minutes=5):
        raise ManifestError("install plan creation time is in the future")
    lifetime = expires - created
    if lifetime < timedelta(minutes=1) or lifetime > timedelta(minutes=1440):
        raise ManifestError("install plan lifetime must be between 1 and 1440 minutes")
    if now > expires:
        raise ManifestError("install plan expired")
    target = _expand_target(str(plan.get("target", "")))
    tool = plan.get("tool")
    profiles = plan.get("profiles")
    optional_skills = plan.get("optional_skills")
    asset_kind = plan.get("asset_kind")
    operations = plan.get("operations")
    if not isinstance(tool, str):
        raise ManifestError("install plan tool must be a string")
    if not isinstance(profiles, list) or not profiles or not all(isinstance(item, str) for item in profiles):
        raise ManifestError("install plan profiles must be a non-empty string array")
    if not isinstance(optional_skills, list) or not all(isinstance(item, str) for item in optional_skills):
        raise ManifestError("install plan optional_skills must be a string array")
    if asset_kind is not None and asset_kind not in ("agent", "skill"):
        raise ManifestError("install plan asset_kind must be agent, skill, or null")
    if not isinstance(operations, list) or not operations:
        raise ManifestError("install plan operations must be a non-empty array")

    active_receipt_sha256 = plan.get("active_receipt_sha256")
    if active_receipt_sha256 is not None and (
        not isinstance(active_receipt_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", active_receipt_sha256)
    ):
        raise ManifestError("install plan active_receipt_sha256 is invalid")
    receipt_path = target / RECEIPT_NAME
    receipt_exists = receipt_path.exists() or receipt_path.is_symlink()
    if active_receipt_sha256 is None:
        if receipt_exists:
            raise ManifestError("active install receipt appeared after plan creation")
    else:
        current_receipt = _read_receipt(receipt_path, "active install receipt")
        if current_receipt.get("target") != str(target) or current_receipt.get("tool") != tool:
            raise ManifestError("active install receipt identity changed after plan creation")
        if sha256_file(receipt_path) != active_receipt_sha256:
            raise ManifestError("active install receipt changed after plan creation")

    bundle = render_selection(manifest, tool, profiles, optional_skills, asset_kind)
    if plan.get("contract_sha256") != bundle.contract.digest:
        raise ManifestError("target contract changed after install plan creation")
    expected = {item.destination: item for item in bundle.files}
    seen: Set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict):
            raise ManifestError("install operation must be an object")
        relative = operation.get("destination")
        if not isinstance(relative, str) or relative not in expected or relative in seen:
            raise ManifestError("install plan contains an unknown or duplicate destination: {}".format(relative))
        seen.add(relative)
        rendered = expected[relative]
        if operation.get("kind") != rendered.kind or operation.get("name") != rendered.name:
            raise ManifestError("install asset identity does not match renderer: {}".format(relative))
        if operation.get("source") != rendered.source:
            raise ManifestError("install source does not match renderer: {}".format(relative))
        if operation.get("rendered_sha256") != rendered.sha256:
            raise ManifestError("install rendered content changed: {}".format(relative))
        if operation.get("file_mode") != format(rendered.mode, "04o"):
            raise ManifestError("install file mode changed: {}".format(relative))
        if operation.get("mode") != "copy":
            raise ManifestError("install operation has invalid mode: {}".format(operation.get("mode")))
        if operation.get("action") not in ("create", "replace-managed"):
            raise ManifestError("install operation has invalid action: {}".format(operation.get("action")))
        source = ensure_within(manifest.root / rendered.source, manifest.root, "install source")
        destination = ensure_within(target / relative, target, "install destination")
        if not source.is_file() or source.is_symlink():
            raise ManifestError("install source missing or unsafe: {}".format(source))
        if sha256_file(source) != operation.get("source_sha256"):
            raise ManifestError("install source changed: {}".format(source))
        if operation.get("action") == "create" and (destination.exists() or destination.is_symlink()):
            raise ManifestError("destination appeared after plan creation: {}".format(destination))
        if operation.get("action") == "replace-managed":
            if not destination.exists() and not destination.is_symlink():
                raise ManifestError("managed destination disappeared after plan creation: {}".format(destination))
            if sha256_tree(destination) != operation.get("destination_sha256"):
                raise ManifestError("managed destination changed after plan creation: {}".format(destination))
    if seen != set(expected):
        raise ManifestError("install plan does not contain the complete rendered file set")
    return target, bundle


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
    target = _expand_target(target_value)
    with TargetLock(target, "install-apply", lock_timeout_seconds):
        validated_target, bundle = _validate_plan(manifest, plan)
        return _apply_validated_plan(manifest, plan, validated_target, bundle)


def _apply_validated_plan(
    manifest: Manifest,
    plan: Mapping[str, Any],
    target: Path,
    bundle: RenderedBundle,
) -> Dict[str, Any]:
    target.mkdir(parents=True, exist_ok=True)
    run_id = _utc_now().strftime("%Y%m%dT%H%M%SZ") + "-" + str(plan["plan_id"])[:8]
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
    temp_receipt = target / (RECEIPT_NAME + ".tmp")
    try:
        receipt_path = target / RECEIPT_NAME
        if receipt_path.is_file():
            previous = backup_root / RECEIPT_NAME
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
            "schema": RECEIPT_SCHEMA,
            "receipt_id": run_id,
            "created_at": _iso(_utc_now()),
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
        receipt["receipt_sha256"] = _receipt_digest(receipt)
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
    initial = _read_receipt(receipt_path, "rollback receipt")
    target_value = initial.get("target")
    if not isinstance(target_value, str) or not target_value:
        raise ManifestError("rollback receipt target must be a non-empty string")
    target = _expand_target(target_value)
    with TargetLock(target, "install-rollback", lock_timeout_seconds):
        return _rollback_locked(receipt_path)


def _rollback_locked(receipt_path: Path) -> Dict[str, Any]:
    receipt = _read_receipt(receipt_path, "rollback receipt")
    receipt_schema = receipt.get("schema")
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
            if receipt_schema in (PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA):
                backup_sha256 = item.get("backup_sha256")
                if not isinstance(backup_sha256, str) or sha256_tree(backup) != backup_sha256:
                    raise ManifestError("rollback backup changed; refusing rollback: {}".format(backup))
        elif receipt_schema in (PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA) and item.get("backup_sha256") is not None:
            raise ManifestError("rollback receipt has a backup digest without a backup")

    previous_receipt_value = receipt.get("previous_receipt")
    previous_receipt: Optional[Path] = None
    if previous_receipt_value:
        previous_receipt = ensure_within(target / str(previous_receipt_value), target, "previous receipt")
        if not previous_receipt.is_file() or previous_receipt.is_symlink():
            raise ManifestError("previous install receipt is missing")
        if receipt_schema in (PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA):
            previous_receipt_sha256 = receipt.get("previous_receipt_sha256")
            if not isinstance(previous_receipt_sha256, str) or sha256_file(previous_receipt) != previous_receipt_sha256:
                raise ManifestError("previous install receipt changed; refusing rollback")
    elif receipt_schema in (PREVIOUS_RECEIPT_SCHEMA, RECEIPT_SCHEMA) and receipt.get("previous_receipt_sha256") is not None:
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
