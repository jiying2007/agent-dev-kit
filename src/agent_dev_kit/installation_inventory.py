"""Trusted rendered asset inventory authority shared by install and rollback."""

from __future__ import annotations

from typing import Any, Mapping, Set

from .model import Manifest, ManifestError, sha256_file
from .targets import RenderedBundle, render_selection


def verify_receipt_inventory(manifest: Manifest, receipt: Mapping[str, Any]) -> RenderedBundle:
    """Authorize rollback files from trusted rendered assets, not mutable receipt paths.

    A receipt SHA-256 proves only that its local JSON has been consistently
    rewritten. It cannot authorize deletion of file paths named in that JSON.
    Operators must use the exact source version that produced the receipt.
    """
    if receipt.get("manifest_version") != manifest.version or receipt.get("manifest_sha256") != manifest.digest:
        raise ManifestError("rollback receipt does not match the trusted ADK manifest identity")
    tool = receipt.get("tool")
    profiles = receipt.get("profiles")
    optional_skills = receipt.get("optional_skills")
    asset_kind = receipt.get("asset_kind")
    if (
        not isinstance(tool, str) or not tool
        or not isinstance(profiles, list) or not profiles
        or any(not isinstance(p, str) for p in profiles)
        or not isinstance(optional_skills, list)
        or any(not isinstance(p, str) for p in optional_skills)
        or asset_kind not in (None, "agent", "skill")
    ):
        raise ManifestError("rollback receipt has invalid asset selection")
    bundle = render_selection(manifest, tool, profiles, optional_skills, asset_kind)
    if (
        receipt.get("contract_sha256") != bundle.contract.digest
        or receipt.get("profiles") != list(bundle.resolution.profiles)
        or receipt.get("optional_skills") != list(bundle.optional_skills)
    ):
        raise ManifestError("rollback receipt target selection differs from trusted ADK renderer")
    expected = {item.destination: item for item in bundle.files}
    installed = receipt.get("installed")
    if not isinstance(installed, list) or len(installed) != len(expected):
        raise ManifestError("rollback receipt inventory does not match trusted rendered assets")
    seen: Set[str] = set()
    for item in installed:
        if not isinstance(item, dict):
            raise ManifestError("rollback receipt contains an invalid installed asset")
        destination = item.get("destination")
        if not isinstance(destination, str) or destination in seen or destination not in expected:
            raise ManifestError("rollback receipt contains an unauthorized or duplicate destination")
        seen.add(destination)
        rendered = expected[destination]
        if (
            item.get("kind") != rendered.kind
            or item.get("name") != rendered.name
            or item.get("source") != rendered.source
            or item.get("source_sha256") != sha256_file(manifest.root / rendered.source)
            or item.get("rendered_sha256") != rendered.sha256
            or item.get("installed_sha256") != rendered.sha256
            or item.get("file_mode") != format(rendered.mode, "04o")
        ):
            raise ManifestError("rollback receipt asset differs from trusted renderer: {}".format(destination))
    return bundle
