#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

python3 - "$ROOT" <<'PY'
import json
import re
import sys
from pathlib import Path

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
expected_digest = sha256_bytes(canonical_json_bytes(manifest_data))
assert manifest.digest == expected_digest, (manifest.digest, expected_digest)
assert manifest.validate(strict=False) == [], manifest.validate(strict=False)

# Until a deterministic composer is introduced under an explicit contract, fragments
# and generators are forbidden. This prevents parallel SSOT or runtime include semantics.
for retired_or_future in (
    root / "manifest.yaml",
    root / "manifests" / "manifest-sections",
    root / "manifests" / "manifest-fragments",
    root / "tools" / "compose_manifest.py",
):
    assert not retired_or_future.exists(), (
        "manifest composition surface requires a deliberate contract migration first: "
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
    "required_section_count": len(required_set),
    "owner_domain_count": len(set(owners.values())),
    "manifest_digest": manifest.digest,
    "parallel_ssot_allowed": future["parallel_ssot_allowed"],
    "runtime_fragment_loading": future["runtime_fragment_loading"],
}, sort_keys=True))
PY

echo '[PASS] manifest composition and bounded-context ownership contract pass'
