#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

bash "$ROOT_DIR/scripts/check-profile-coherence.sh"

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 -m agent_dev_kit.profile_coherence_contract \
  --root "$ROOT_DIR" --summary-json >"$TMP"

python3 - "$ROOT_DIR/manifest.json" "$TMP" <<'PY'
import json
import sys

manifest_path, summary_path = sys.argv[1:]
with open(manifest_path, encoding="utf-8") as handle:
    manifest = json.load(handle)
with open(summary_path, encoding="utf-8") as handle:
    summary = json.load(handle)

profiles = manifest["profiles"]


def parents(name):
    value = profiles[name].get("extends")
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item]
    return []


def direct(name, key):
    value = profiles[name].get(key, [])
    return sorted({item for item in value if isinstance(item, str) and item})


def resolved(name, key, visiting=()):
    assert name not in visiting, (name, visiting)
    values = set(direct(name, key))
    for parent in parents(name):
        values.update(resolved(parent, key, visiting + (name,)))
    return sorted(values)


def depth(name, visiting=()):
    assert name not in visiting, (name, visiting)
    lineage = parents(name)
    if not lineage:
        return 0
    return 1 + max(depth(parent, visiting + (name,)) for parent in lineage)


expected_inventory = {}
for name in sorted(profiles):
    direct_agents = direct(name, "include_agents")
    direct_skills = direct(name, "include_skills")
    resolved_agents = resolved(name, "include_agents")
    resolved_skills = resolved(name, "include_skills")
    expected_inventory[name] = {
        "parents": sorted(parents(name)),
        "inheritance_depth": depth(name),
        "direct_agents": direct_agents,
        "inherited_agents": sorted(set(resolved_agents) - set(direct_agents)),
        "resolved_agents": resolved_agents,
        "direct_skills": direct_skills,
        "inherited_skills": sorted(set(resolved_skills) - set(direct_skills)),
        "resolved_skills": resolved_skills,
    }

all_agents = {
    item
    for record in expected_inventory.values()
    for item in record["resolved_agents"]
}
all_skills = {
    item
    for record in expected_inventory.values()
    for item in record["resolved_skills"]
}
expected_stats = {
    "profiles": len(expected_inventory),
    "resolved_agent_references": sum(
        len(record["resolved_agents"]) for record in expected_inventory.values()
    ),
    "resolved_skill_references": sum(
        len(record["resolved_skills"]) for record in expected_inventory.values()
    ),
    "unique_resolved_agents": len(all_agents),
    "unique_resolved_skills": len(all_skills),
    "max_inheritance_depth": max(
        (record["inheritance_depth"] for record in expected_inventory.values()),
        default=0,
    ),
}

core = expected_inventory.get("core", {})
core_agents = set(core.get("resolved_agents", []))
core_skills = set(core.get("resolved_skills", []))
expected_overlap = {}
for name, record in expected_inventory.items():
    if name == "core" or record["parents"]:
        continue
    agents = sorted(core_agents & set(record["resolved_agents"]))
    skills = sorted(core_skills & set(record["resolved_skills"]))
    expected_overlap[name] = {
        "agents": agents,
        "skills": skills,
        "agent_count": len(agents),
        "skill_count": len(skills),
    }

assert summary["schema"] == "adk-profile-coherence/v2", summary
assert summary["status"] == "pass", summary
assert summary["source"] == "manifest.json", summary
assert summary["profiles"] == len(profiles), summary
assert summary["profile_inventory"] == expected_inventory, summary
assert summary["capability_stats"] == expected_stats, summary
assert summary["standalone_core_overlap"] == expected_overlap, summary
PY

[[ ! -e "$ROOT_DIR/skills/adk-test-strategy/references/embedded-tdd-matrix.md" ]] || {
  echo "[FAIL] embedded TDD matrix leaked into platform-neutral test strategy" >&2
  exit 1
}
[[ -f "$ROOT_DIR/skills/adk-unit-test-embedded/references/embedded-tdd-matrix.md" ]] || {
  echo "[FAIL] embedded TDD matrix missing from embedded-only unit test skill" >&2
  exit 1
}

echo "[PASS] profile coherence"
