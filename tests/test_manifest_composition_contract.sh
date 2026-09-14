#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python3 - "$ROOT" <<'PY'
from copy import deepcopy
import json
import re
import sys
from pathlib import Path

from agent_dev_kit.contracts.manifest_composition import (
    ManifestCompositionError,
    compose_owned_sections,
    partition_by_owner,
)
from agent_dev_kit.model import Manifest, canonical_json_bytes, sha256_bytes

root = Path(sys.argv[1]).resolve()
policy_path = root / "manifests" / "manifest_composition_policy.json"
manifest_path = root / "manifest.json"
schema_path = root / "manifests" / "manifest.schema.json"

policy = json.loads(policy_path.read_text(encoding="utf-8"))
manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
schema = json.loads(schema_path.read_text(encoding="utf-8"))

assert policy.get("schema") == "adk-manifest-composition-policy/v1", policy
assert policy.get("canonical_source") == "manifest.json", policy
assert policy.get("runtime_consumer_mode") == "canonical-json-only", policy
assert policy.get("authoring_mode") == "single-canonical-json", policy
assert policy.get("digest_semantics") == "canonical-output-json", policy
assert policy.get("composition_generator") is None, policy

reference = policy.get("reference_composer")
assert reference == {
    "module": "agent_dev_kit.contracts.manifest_composition",
    "partition_function": "partition_by_owner",
    "compose_function": "compose_owned_sections",
    "mode": "pure-in-memory-only",
    "file_io": False,
    "runtime_enabled": False,
    "extension_owner": "extension-governance",
}, reference
extension_owner = reference["extension_owner"]

future = policy.get("future_split_contract")
assert isinstance(future, dict), policy
assert future == {
    "mode": "deterministic-build-time-only",
    "canonical_output": "manifest.json",
    "runtime_fragment_loading": False,
    "parallel_ssot_allowed": False,
    "generated_output_must_validate_before_consume": True,
    "generated_output_must_preserve_manifest_digest_semantics": True,
}, future

migration_gate = policy.get("migration_gate")
assert migration_gate == {
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
}, migration_gate

prohibited = policy.get("prohibited_runtime_composition_keys")
assert prohibited == ["$include", "include", "includes", "fragments", "imports"], prohibited
for key in prohibited:
    assert key not in manifest_data, f"runtime composition key is forbidden in canonical manifest: {key}"

required = schema.get("required")
assert isinstance(required, list) and required, schema
required_set = set(required)
assert len(required_set) == len(required), "manifest schema required keys contain duplicates"

owners = policy.get("section_owners")
assert isinstance(owners, dict) and owners, policy
assert set(owners) == required_set, (
    "section ownership must exactly cover schema-required top-level sections: "
    f"missing={sorted(required_set - set(owners))} extra={sorted(set(owners) - required_set)}"
)
for section, owner in owners.items():
    assert isinstance(owner, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", owner), (
        f"invalid bounded-context owner for {section}: {owner!r}"
    )

# The current runtime contract has one canonical, directly consumable JSON object.
# x-* extension keys remain schema-governed extensions and do not create a second SSOT.
canonical_sections = {key for key in manifest_data if not key.startswith("x-")}
assert canonical_sections == required_set, (
    "canonical manifest top-level contract drifted from schema-required ownership: "
    f"missing={sorted(required_set - canonical_sections)} extra={sorted(canonical_sections - required_set)}"
)

manifest = Manifest.load(root)
assert manifest.source == manifest_path.resolve(), manifest.source
assert manifest.data == manifest_data, "Manifest.load must consume canonical manifest.json without projection"
expected_bytes = canonical_json_bytes(manifest_data)
expected_digest = sha256_bytes(expected_bytes)
assert manifest.digest == expected_digest, (manifest.digest, expected_digest)
assert manifest.validate(strict=False) == [], manifest.validate(strict=False)

# Phase 2 proves a pure in-memory owner partition is semantically and digest identical.
partitions = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
recomposed = compose_owned_sections(partitions, owners, extension_owner=extension_owner)
assert recomposed == manifest_data, "owner partition round trip changed manifest semantics"
assert canonical_json_bytes(recomposed) == expected_bytes, "owner partition round trip changed canonical bytes"
assert sha256_bytes(canonical_json_bytes(recomposed)) == expected_digest, "owner partition round trip changed digest"
assert set(partitions) == set(owners.values()), partitions

# Partitioning and composition must deep-copy nested values so a future authoring layer
# cannot mutate the canonical object through shared references.
isolated = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
isolated[owners["platforms"]]["platforms"].append("__mutation-probe__")
assert "__mutation-probe__" not in manifest_data["platforms"], "partition leaked a mutable canonical reference"
isolated_result = compose_owned_sections(
    partition_by_owner(manifest_data, owners, extension_owner=extension_owner),
    owners,
    extension_owner=extension_owner,
)
isolated_result["platforms"].append("__result-probe__")
assert "__result-probe__" not in manifest_data["platforms"], "composition leaked a mutable partition reference"


def expect_composition_failure(label, callback, message):
    try:
        callback()
    except ManifestCompositionError as exc:
        assert message in str(exc), (label, str(exc), message)
    else:
        raise AssertionError(f"{label} did not fail closed")


missing_manifest = deepcopy(manifest_data)
missing_manifest.pop("version")
expect_composition_failure(
    "partition missing section",
    lambda: partition_by_owner(missing_manifest, owners, extension_owner=extension_owner),
    "missing owned sections",
)

unknown_manifest = deepcopy(manifest_data)
unknown_manifest["rogue"] = {}
expect_composition_failure(
    "partition unknown section",
    lambda: partition_by_owner(unknown_manifest, owners, extension_owner=extension_owner),
    "unowned sections",
)

missing_partitions = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
missing_partitions[owners["version"]].pop("version")
expect_composition_failure(
    "compose missing section",
    lambda: compose_owned_sections(missing_partitions, owners, extension_owner=extension_owner),
    "missing owned sections",
)

duplicate_partitions = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
duplicate_partitions[owners["agents"]]["version"] = manifest_data["version"]
expect_composition_failure(
    "compose duplicate section",
    lambda: compose_owned_sections(duplicate_partitions, owners, extension_owner=extension_owner),
    "duplicated across owners",
)

misowned_partitions = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
version_value = misowned_partitions[owners["version"]].pop("version")
misowned_partitions[owners["agents"]]["version"] = version_value
expect_composition_failure(
    "compose misowned section",
    lambda: compose_owned_sections(misowned_partitions, owners, extension_owner=extension_owner),
    "is owned by identity, not asset-catalog",
)

unknown_partitions = partition_by_owner(manifest_data, owners, extension_owner=extension_owner)
unknown_partitions[owners["agents"]]["rogue"] = {}
expect_composition_failure(
    "compose unknown section",
    lambda: compose_owned_sections(unknown_partitions, owners, extension_owner=extension_owner),
    "has no declared owner",
)

extension_manifest = deepcopy(manifest_data)
extension_manifest["x-round-trip"] = {"enabled": True}
extension_partitions = partition_by_owner(extension_manifest, owners, extension_owner=extension_owner)
assert extension_partitions[extension_owner]["x-round-trip"] == {"enabled": True}
extension_recomposed = compose_owned_sections(extension_partitions, owners, extension_owner=extension_owner)
assert extension_recomposed == extension_manifest

misowned_extension = partition_by_owner(extension_manifest, owners, extension_owner=extension_owner)
extension_value = misowned_extension[extension_owner].pop("x-round-trip")
misowned_extension[owners["agents"]]["x-round-trip"] = extension_value
expect_composition_failure(
    "compose misowned extension",
    lambda: compose_owned_sections(misowned_extension, owners, extension_owner=extension_owner),
    "is owned by extension-governance, not asset-catalog",
)

# Even with a pure reference composer, file-backed fragments/generators remain forbidden.
# Runtime and release consumers still bind directly to manifest.json.
for retired_or_future in (
    root / "manifest.yaml",
    root / migration_gate["authoring_root"],
    root / "manifests" / "manifest-fragments",
    root / migration_gate["generator_path"],
):
    assert not retired_or_future.exists(), (
        "file-backed manifest composition requires a deliberate contract migration first: "
        f"{retired_or_future.relative_to(root)}"
    )

root_manifest_candidates = sorted(path.name for path in root.glob("manifest.*") if path.is_file())
assert root_manifest_candidates == ["manifest.json"], root_manifest_candidates

print(json.dumps({
    "schema": policy["schema"],
    "status": "pass",
    "canonical_source": policy["canonical_source"],
    "runtime_consumer_mode": policy["runtime_consumer_mode"],
    "authoring_mode": policy["authoring_mode"],
    "reference_composer_mode": reference["mode"],
    "reference_composer_runtime_enabled": reference["runtime_enabled"],
    "required_section_count": len(required_set),
    "owner_domain_count": len(set(owners.values())),
    "manifest_digest": manifest.digest,
    "round_trip_digest": sha256_bytes(canonical_json_bytes(recomposed)),
    "parallel_ssot_allowed": future["parallel_ssot_allowed"],
    "runtime_fragment_loading": future["runtime_fragment_loading"],
}, sort_keys=True))
PY

echo '[PASS] manifest composition and bounded-context ownership contract pass'
