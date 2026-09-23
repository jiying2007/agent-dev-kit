"""Installation plan construction and validation."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from . import installation_contract as install_contract
from .model import Manifest, ManifestError, ensure_within, sha256_file, sha256_tree
from .targets import RenderedBundle, TargetUsageError, render_selection

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
    target = install_contract._expand_target(target_value)
    receipt_path = target / install_contract.RECEIPT_NAME
    existing_receipt = install_contract._load_receipt(target) if target.exists() else None
    active_receipt_sha256: Optional[str] = None
    managed: Dict[str, Mapping[str, Any]] = {}
    if existing_receipt:
        if existing_receipt.get("target") != str(target):
            raise ManifestError("existing install receipt target does not match its location")
        if existing_receipt.get("tool") != tool:
            raise ManifestError("existing install receipt tool does not match requested target")
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

    now = install_contract._utc_now()
    return {
        "schema": install_contract.PLAN_SCHEMA,
        "status": "needs-review" if conflicts else "ready",
        "plan_id": str(uuid.uuid4()),
        "created_at": install_contract._iso(now),
        "expires_at": install_contract._iso(now + timedelta(minutes=ttl_minutes)),
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


def validate_plan(manifest: Manifest, plan: Mapping[str, Any]) -> Tuple[Path, RenderedBundle]:
    if plan.get("schema") != install_contract.PLAN_SCHEMA:
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
        created = install_contract._parse_time(str(plan.get("created_at", "")))
        expires = install_contract._parse_time(str(plan.get("expires_at", "")))
    except (TypeError, ValueError) as exc:
        raise ManifestError("install plan has invalid timestamps") from exc
    now = install_contract._utc_now()
    if created > now + timedelta(minutes=5):
        raise ManifestError("install plan creation time is in the future")
    lifetime = expires - created
    if lifetime < timedelta(minutes=1) or lifetime > timedelta(minutes=1440):
        raise ManifestError("install plan lifetime must be between 1 and 1440 minutes")
    if now > expires:
        raise ManifestError("install plan expired")
    target = install_contract._expand_target(str(plan.get("target", "")))
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
    receipt_path = target / install_contract.RECEIPT_NAME
    receipt_exists = receipt_path.exists() or receipt_path.is_symlink()
    if active_receipt_sha256 is None:
        if receipt_exists:
            raise ManifestError("active install receipt appeared after plan creation")
    else:
        current_receipt = install_contract._read_receipt(receipt_path, "active install receipt")
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
