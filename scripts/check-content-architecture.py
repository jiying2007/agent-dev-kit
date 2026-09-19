#!/usr/bin/env python3
from __future__ import print_function

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agent_dev_kit.matcher import resolve_skill_content  # noqa: E402
from agent_dev_kit.model import Manifest, ManifestError  # noqa: E402

SUMMARY = "--summary-json" in sys.argv[1:]
failures = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def load_json(path):
    p = ROOT / path
    check(p.is_file(), "missing file: %s" % path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append("invalid json %s: %s" % (path, exc))
        return {}


def validate_json(instance_path, schema_path):
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    if instance and schema:
        try:
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(instance)
        except Exception as exc:
            failures.append("schema validation failed %s: %s" % (instance_path, exc))
    return instance


def parse_skill_frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    lines = text[4:end].splitlines()
    result = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith((" ", "\t")) or ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if key in ("name", "description"):
            if value in (">", "|"):
                parts = []
                j = i + 1
                while j < len(lines) and (lines[j].startswith(" ") or not lines[j].strip()):
                    if lines[j].strip():
                        parts.append(lines[j].strip())
                    j += 1
                result[key] = " ".join(parts)
                i = j
                continue
            result[key] = value.strip("\"'")
        i += 1
    return result


def normalized_long_lines(text):
    values = set()
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        if len(line) >= 48 and not line.startswith("#"):
            values.add(line)
    return values


try:
    manifest_obj = Manifest.load(ROOT)
except ManifestError as exc:
    failures.append("manifest load failed: %s" % exc)
    manifest_obj = None
manifest = manifest_obj.data if manifest_obj is not None else load_json("manifest.json")
policy = validate_json(
    "manifests/content_architecture_policy.json",
    "schemas/content-architecture-policy-v1.schema.json",
)
agent_value = validate_json(
    "manifests/agent_value_contracts.json",
    "schemas/agent-value-contracts-v1.schema.json",
)
skill_contract = validate_json(
    "manifests/skill_content_contracts_v2.json",
    "schemas/skill-content-contract-v2.schema.json",
)
handoff_schema = load_json("schemas/agent-handoff-v1.schema.json")
if handoff_schema:
    try:
        Draft202012Validator.check_schema(handoff_schema)
    except Exception as exc:
        failures.append("invalid handoff schema: %s" % exc)

identity_baseline = policy.get("identity_baseline", {}) if isinstance(policy, dict) else {}
thin_policy = policy.get("agent_thin_contract", {}) if isinstance(policy, dict) else {}

# Agent identity/parity/thin-contract checks. Existing Agent Value contracts remain
# the single typed authority for permission, decision authority, handoff and eval.
agents = manifest.get("agents", [])
agent_by_id = {item.get("name"): item for item in agents if isinstance(item, dict)}
contracts = agent_value.get("agent_contracts", []) if isinstance(agent_value, dict) else []
contract_by_id = {item.get("agent_id"): item for item in contracts if isinstance(item, dict)}
check(len(agent_by_id) == len(agents), "manifest agent identities must be unique")
check(set(contract_by_id) == set(agent_by_id), "Agent Value contract must cover manifest agents exactly")
check(len(agent_by_id) == identity_baseline.get("agent_count"), "agent count drift requires explicit policy update")

required_headings = thin_policy.get("required_headings", [])
forbidden_headings = thin_policy.get("forbidden_procedure_headings", [])
for agent_id, item in agent_by_id.items():
    path = ROOT / item["path"]
    check(path.is_file(), "missing Agent file: %s" % item["path"])
    if not path.is_file():
        continue
    text = path.read_text(encoding="utf-8")
    limit_key = "p0_max_bytes" if item.get("quality_tier") == "p0" else "p1_max_bytes"
    limit = thin_policy.get(limit_key, 5000)
    check(len(text.encode("utf-8")) <= limit, "%s exceeds thin Agent byte limit %s" % (agent_id, limit))
    for heading in required_headings:
        check(heading in text, "%s missing thin-contract heading %s" % (agent_id, heading))
    for heading in forbidden_headings:
        check(("## " + heading) not in text, "%s reintroduced procedure heading %s" % (agent_id, heading))
    if thin_policy.get("forbid_shell_code_fences") is True:
        check("```bash" not in text and "```sh" not in text, "%s must not carry command cookbook" % agent_id)
    contract = contract_by_id.get(agent_id, {})
    envelope = contract.get("permission_envelope", {}) if isinstance(contract, dict) else {}
    check(envelope.get("permission_profile") == item.get("permission_profile"), "%s permission drift vs manifest" % agent_id)
    check("`%s`" % item.get("permission_profile") in text, "%s must state manifest permission profile" % agent_id)
    for skill_id in item.get("default_skills", []):
        check(skill_id in text, "%s missing default Skill reference %s" % (agent_id, skill_id))
    for target in item.get("handoff_to", []):
        check(target in text, "%s missing manifest handoff target %s" % (agent_id, target))

# Agent -> default Skill exact-line duplication ratchet. This intentionally avoids fuzzy
# semantic policing; it prevents copied procedure/checklist lines from returning to Agent core.
for agent_id, item in agent_by_id.items():
    agent_path = ROOT / item["path"]
    if not agent_path.is_file():
        continue
    agent_lines = normalized_long_lines(agent_path.read_text(encoding="utf-8"))
    for skill_id in item.get("default_skills", []):
        skill_item = next((x for x in manifest.get("skills", []) if x.get("name") == skill_id), None)
        if not skill_item:
            continue
        skill_path = ROOT / skill_item["path"]
        if not skill_path.is_file():
            continue
        overlap = agent_lines & normalized_long_lines(skill_path.read_text(encoding="utf-8"))
        check(len(overlap) <= 2, "%s duplicates procedure text from %s: %s" % (agent_id, skill_id, sorted(overlap)[:3]))

# Skill v2 is derived from manifest. CI and runtime intentionally call the same
# resolver so eligibility semantics cannot drift between a checker and matcher.
core_skills = manifest.get("skills", [])
optional_skills = manifest.get("optional_skills", [])
all_skills = [("core", x) for x in core_skills] + [("optional", x) for x in optional_skills]
all_ids = [item.get("name") for _, item in all_skills]
check(len(all_ids) == len(set(all_ids)), "core + optional Skill identities must be unique")
check(len(core_skills) == identity_baseline.get("core_skill_count"), "core Skill count drift requires explicit policy update")
check(len(optional_skills) == identity_baseline.get("optional_skill_count"), "optional Skill count drift requires explicit policy update")
overrides = skill_contract.get("overrides", {}) if isinstance(skill_contract, dict) else {}
check(set(overrides).issubset(set(all_ids)), "Skill v2 overrides contain unknown identity")

derived = {}
if manifest_obj is not None:
    for scope, item in all_skills:
        skill_id = item.get("name")
        try:
            metadata = resolve_skill_content(manifest_obj, skill_id)
        except ManifestError as exc:
            failures.append(str(exc))
            continue
        check(metadata.get("scope") == scope, "%s Skill v2 scope drift" % skill_id)
        if metadata.get("capability_class") in ("support", "knowledge"):
            check(metadata.get("runtime_role") != "primary", "%s support/knowledge capability cannot be primary" % skill_id)
        if metadata.get("capability_class") == "guardrail" and metadata.get("runtime_role") == "primary":
            check(skill_id in overrides, "%s guardrail primary requires explicit override" % skill_id)
        path = ROOT / item.get("path", "")
        check(path.is_file(), "missing Skill file: %s" % item.get("path"))
        if path.is_file():
            meta = parse_skill_frontmatter(path.read_text(encoding="utf-8"))
            check(meta.get("name") == skill_id, "%s SKILL frontmatter name mismatch" % skill_id)
            check(bool(meta.get("description")), "%s SKILL description missing" % skill_id)
            if meta.get("description"):
                check(len(meta["description"]) <= 1024, "%s Skill description exceeds portable bound" % skill_id)
        derived[skill_id] = metadata

check(
    policy.get("production_behavior_without_authority")
    == skill_contract.get("policy", {}).get("production_behavior_without_authority"),
    "production behavior evidence policy drift between content policy and Skill v2",
)

# V2 migration hotspots / compatibility cleanup ratchets.
context_text = (ROOT / "skills/adk-context-engineering/SKILL.md").read_text(encoding="utf-8")
check("10 分钟" not in context_text, "context-engineering must not restore hard-coded 10-minute policy")
check("schemas/agent-handoff-v1.schema.json" in context_text, "context-engineering must use global handoff schema")
bsp_agent = (ROOT / "agents/bsp-analyst/AGENTS.md").read_text(encoding="utf-8")
bsp_skill = (ROOT / "skills/adk-bsp-analysis/SKILL.md").read_text(encoding="utf-8")
check("references/bsp-analysis-details.md" in bsp_skill, "BSP details must use progressive disclosure reference")
check("```bash" not in bsp_agent, "BSP Agent must not regain BSP command procedure")
check((ROOT / "skills/adk-bsp-analysis/references/bsp-analysis-details.md").is_file(), "missing BSP on-demand reference")

# E1/E3 fixture is structural in CI; production runtime behavior remains explicit not-measured.
eval_fixture = load_json("tests/fixtures/content-architecture/routing-authority-cases.json")
case_types = {case.get("case_type") for case in eval_fixture.get("cases", []) if isinstance(case, dict)}
for required in ("route-positive", "near-miss-negative", "authority-negative", "permission-negative", "handoff", "abstain"):
    check(required in case_types, "missing Skill Content v2 eval case type: %s" % required)
for case in eval_fixture.get("cases", []):
    if not isinstance(case, dict):
        continue
    skill_id = case.get("expected_skill")
    if skill_id:
        check(skill_id in derived, "eval fixture references unknown skill %s" % skill_id)
        expected_role = case.get("expected_runtime_role")
        if expected_role:
            check(derived.get(skill_id, {}).get("runtime_role") == expected_role, "eval fixture role drift for %s" % skill_id)
    agent_id = case.get("expected_agent")
    if agent_id:
        check(agent_id in agent_by_id, "eval fixture references unknown agent %s" % agent_id)

summary = {
    "status": "pass" if not failures else "fail",
    "checks": checks,
    "failures": failures,
    "agent_count": len(agent_by_id),
    "core_skill_count": len(core_skills),
    "optional_skill_count": len(optional_skills),
    "production_behavior_evidence": policy.get("production_behavior_without_authority"),
}
if SUMMARY:
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
else:
    if failures:
        for item in failures:
            print("[FAIL] %s" % item, file=sys.stderr)
    else:
        print("[PASS] Agent/Skill content architecture checks=%s agents=%s skills=%s+%s" % (checks, len(agent_by_id), len(core_skills), len(optional_skills)))

sys.exit(0 if not failures else 1)
