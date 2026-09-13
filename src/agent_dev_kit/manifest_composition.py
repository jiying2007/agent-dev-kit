"""Pure in-memory composition primitives for the canonical ADK manifest.

These helpers deliberately perform no file I/O. Runtime consumers continue to load
``manifest.json`` directly; this module only proves that bounded-context authoring
can be composed deterministically before any physical split is introduced.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class ManifestCompositionError(ValueError):
    """Raised when an owned-section partition cannot compose one manifest."""


def _validated_owners(section_owners: Mapping[str, str]) -> dict[str, str]:
    owners = dict(section_owners)
    if not owners:
        raise ManifestCompositionError("section ownership must not be empty")
    for section, owner in owners.items():
        if not isinstance(section, str) or not section:
            raise ManifestCompositionError("section ownership contains an invalid section name")
        if not isinstance(owner, str) or not owner:
            raise ManifestCompositionError(f"section {section} has an invalid owner")
    return owners


def partition_by_owner(
    manifest: Mapping[str, Any],
    section_owners: Mapping[str, str],
    *,
    extension_owner: str = "extension-governance",
) -> dict[str, dict[str, Any]]:
    """Partition one canonical manifest into owner-scoped in-memory mappings."""

    owners = _validated_owners(section_owners)
    if not extension_owner:
        raise ManifestCompositionError("extension owner must not be empty")

    manifest_keys = set(manifest)
    missing = set(owners) - manifest_keys
    unknown = {key for key in manifest_keys - set(owners) if not key.startswith("x-")}
    if missing:
        raise ManifestCompositionError(f"manifest is missing owned sections: {sorted(missing)}")
    if unknown:
        raise ManifestCompositionError(f"manifest contains unowned sections: {sorted(unknown)}")

    partitions: dict[str, dict[str, Any]] = {}
    for section, value in manifest.items():
        owner = extension_owner if section.startswith("x-") else owners[section]
        partitions.setdefault(owner, {})[section] = deepcopy(value)
    return partitions


def compose_owned_sections(
    partitions: Mapping[str, Mapping[str, Any]],
    section_owners: Mapping[str, str],
    *,
    extension_owner: str = "extension-governance",
) -> dict[str, Any]:
    """Compose owner-scoped mappings into exactly one canonical manifest object."""

    owners = _validated_owners(section_owners)
    if not extension_owner:
        raise ManifestCompositionError("extension owner must not be empty")

    composed: dict[str, Any] = {}
    seen: dict[str, str] = {}
    for owner, sections in partitions.items():
        if not isinstance(owner, str) or not owner:
            raise ManifestCompositionError("partition contains an invalid owner")
        for section, value in sections.items():
            if section in seen:
                raise ManifestCompositionError(
                    f"section {section} is duplicated across owners {seen[section]} and {owner}"
                )
            expected_owner = extension_owner if section.startswith("x-") else owners.get(section)
            if expected_owner is None:
                raise ManifestCompositionError(f"section {section} has no declared owner")
            if owner != expected_owner:
                raise ManifestCompositionError(f"section {section} is owned by {expected_owner}, not {owner}")
            seen[section] = owner
            composed[section] = deepcopy(value)

    missing = set(owners) - set(composed)
    if missing:
        raise ManifestCompositionError(f"composition is missing owned sections: {sorted(missing)}")
    return composed
