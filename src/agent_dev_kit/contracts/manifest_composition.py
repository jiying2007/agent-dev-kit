"""Pure in-memory composition primitives for the canonical ADK manifest.

These helpers deliberately perform no file I/O. Runtime consumers continue to load
``manifest.json`` directly; this module only proves that bounded-context authoring
can be composed deterministically before any physical split is introduced.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any


class ManifestCompositionError(ValueError):
    """Raised when an owned-section partition cannot compose one manifest."""


def _validated_owners(section_owners: Mapping[str, str]) -> dict[str, str]:
    owners = dict(section_owners)
    if not owners:
        raise ManifestCompositionError("section ownership must not be empty")
    for section, owner in owners.items():
        if not section:
            raise ManifestCompositionError("section ownership contains an invalid section name")
        if not owner:
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
        if not owner:
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



def _expected_migration_gate() -> dict[str, Any]:
    return {
        "state": "blocked",
        "change_id": "manifest-build-time-split",
        "required_change_stage": "review-passed",
        "authoring_root": "manifests/manifest-sections",
        "generator_path": "tools/compose_manifest.py",
        "target_authoring_mode": "deterministic-build-time",
        "required_evidence": [
            "change-governance-pass",
            "executable-rollback-plan",
            "deterministic-double-generation",
            "strict-generated-output-validation",
            "canonical-digest-equivalence",
            "canonical-consumer-boundary-pass",
        ],
        "activation_invariants": {
            "canonical_output": "manifest.json",
            "runtime_fragment_loading": False,
            "parallel_ssot_allowed": False,
            "generated_output_must_validate_before_consume": True,
            "generated_output_must_preserve_manifest_digest_semantics": True,
        },
    }


def split_migration_readiness(
    policy: Mapping[str, Any],
    *,
    change_stage: str | None,
    authoring_root_present: bool,
    generator_path_present: bool,
) -> dict[str, Any]:
    """Report whether the current contract authorizes a physical manifest split."""

    expected = _expected_migration_gate()
    gate = policy.get("migration_gate")
    if gate != expected:
        return {
            "schema": "adk-manifest-split-readiness/v1",
            "status": "invalid",
            "failures": ["migration_gate contract drift; deliberate contract migration is required"],
        }

    blockers = ["manifest split migration authorization is blocked by current contract"]
    if change_stage != expected["required_change_stage"]:
        blockers.append(
            f"migration change {expected['change_id']} must reach {expected['required_change_stage']}"
        )
    if policy.get("authoring_mode") != expected["target_authoring_mode"]:
        blockers.append(
            f"authoring_mode must migrate to {expected['target_authoring_mode']} before physical split"
        )
    if policy.get("composition_generator") != expected["generator_path"]:
        blockers.append("composition_generator must be explicitly declared before physical split")
    if not authoring_root_present:
        blockers.append(f"authoring root is absent: {expected['authoring_root']}")
    else:
        blockers.append("physical authoring root is present while migration authorization is blocked")
    if not generator_path_present:
        blockers.append(f"generator path is absent: {expected['generator_path']}")
    else:
        blockers.append("generator path is present while migration authorization is blocked")

    return {
        "schema": "adk-manifest-split-readiness/v1",
        "status": "blocked",
        "authorization_state": expected["state"],
        "change_id": expected["change_id"],
        "change_stage": change_stage,
        "required_change_stage": expected["required_change_stage"],
        "authoring_root": expected["authoring_root"],
        "authoring_root_present": authoring_root_present,
        "generator_path": expected["generator_path"],
        "generator_path_present": generator_path_present,
        "target_authoring_mode": expected["target_authoring_mode"],
        "required_evidence": list(expected["required_evidence"]),
        "activation_invariants": dict(expected["activation_invariants"]),
        "blockers": blockers,
    }


def composition_check(
    manifest: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    source_digest: str,
    source_is_canonical: bool,
    digest: Callable[[Mapping[str, Any]], str],
) -> dict[str, Any]:
    """Return a read-only fail-closed composition governance report."""

    failures: list[str] = []
    if policy.get("canonical_source") != "manifest.json":
        failures.append("canonical_source must remain manifest.json")
    if policy.get("runtime_consumer_mode") != "canonical-json-only":
        failures.append("runtime_consumer_mode must remain canonical-json-only")
    if policy.get("authoring_mode") != "single-canonical-json":
        failures.append("authoring_mode must remain single-canonical-json")
    if policy.get("composition_generator") is not None:
        failures.append("composition_generator must remain null before physical split")

    expected_reference: dict[str, Any] = {
        "module": "agent_dev_kit.contracts.manifest_composition",
        "partition_function": "partition_by_owner",
        "compose_function": "compose_owned_sections",
        "mode": "pure-in-memory-only",
        "file_io": False,
        "runtime_enabled": False,
        "extension_owner": "extension-governance",
    }
    if policy.get("reference_composer") != expected_reference:
        failures.append(
            "reference_composer must remain pure-in-memory with file_io=false and runtime_enabled=false"
        )

    expected_operational: dict[str, Any] = {
        "command": "manifest composition-check",
        "mode": "read-only-gate",
        "writes": False,
        "runtime_enabled": False,
    }
    if policy.get("operational_check") != expected_operational:
        failures.append(
            "operational_check must remain read-only with writes=false and runtime_enabled=false"
        )

    future_raw = policy.get("future_split_contract")
    future: Mapping[str, Any]
    if isinstance(future_raw, Mapping):
        future = future_raw
    else:
        failures.append("future_split_contract must be an object")
        future = {}
    if future.get("canonical_output") != "manifest.json":
        failures.append("future canonical output must remain manifest.json")
    if future.get("runtime_fragment_loading") is not False:
        failures.append("runtime_fragment_loading must remain false")
    if future.get("parallel_ssot_allowed") is not False:
        failures.append("parallel_ssot_allowed must remain false")

    if policy.get("migration_gate") != _expected_migration_gate():
        failures.append("migration_gate must remain blocked until deliberate contract migration")

    owners_raw = policy.get("section_owners")
    owners: dict[str, str] = {}
    if isinstance(owners_raw, Mapping):
        for section, owner in owners_raw.items():
            if isinstance(section, str) and isinstance(owner, str):
                owners[section] = owner
            else:
                failures.append("section_owners must map strings to strings")
                owners = {}
                break
    if not owners:
        failures.append("section_owners must be a non-empty object")

    if not source_is_canonical:
        failures.append("Manifest.load must remain bound to canonical manifest.json")

    round_trip_digest = ""
    if owners:
        try:
            partitions = partition_by_owner(
                manifest,
                owners,
                extension_owner=str(expected_reference["extension_owner"]),
            )
            recomposed = compose_owned_sections(
                partitions,
                owners,
                extension_owner=str(expected_reference["extension_owner"]),
            )
            round_trip_digest = digest(recomposed)
            if recomposed != manifest:
                failures.append("round-trip composition changed manifest semantics")
            if round_trip_digest != source_digest:
                failures.append("round-trip composition changed canonical manifest digest")
        except ManifestCompositionError as exc:
            failures.append(str(exc))

    result: dict[str, Any] = {
        "schema": "adk-manifest-composition-check/v1",
        "status": "fail" if failures else "pass",
        "canonical_source": policy.get("canonical_source"),
        "source_digest": source_digest,
        "round_trip_digest": round_trip_digest,
        "owner_domain_count": len(set(owners.values())) if owners else 0,
        "reference_composer_mode": expected_reference["mode"],
        "runtime_enabled": expected_reference["runtime_enabled"],
        "writes": expected_operational["writes"],
        "parallel_ssot_allowed": future.get("parallel_ssot_allowed"),
        "runtime_fragment_loading": future.get("runtime_fragment_loading"),
        "composition_generator": policy.get("composition_generator"),
    }
    if failures:
        result["failures"] = failures
    return result
