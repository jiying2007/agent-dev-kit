"""Compile managed workflow metadata into a deterministic execution-neutral IR."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import yaml

from .model import Manifest, ManifestError


POLICY_SCHEMA = "adk-workflow-ir-policy/v1"
IR_SCHEMA = "adk-workflow-ir/v2"
POLICY_FIELDS = {
    "schema_version",
    "ir_schema_version",
    "last_updated",
    "runtime_boundary",
    "allowed_command_risks",
    "timeout_policy",
    "cancellation_policy",
    "unknown_stage_policy",
    "terminal_states",
    "edge_conditions",
    "projection_digests",
    "stage_classes",
    "stage_bindings",
}
STAGE_CLASS_FIELDS = {
    "side_effect",
    "approval",
    "retry",
    "idempotency",
    "checkpoint",
    "rollback",
    "failure_transition",
    "input_refs",
    "output_refs",
    "required_evidence",
}
WORKFLOW_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "version",
    "last_updated",
    "primary_agent",
    "primary_skill",
    "triggers",
    "profiles",
    "command_risk",
    "stages",
    "artifacts",
    "verification",
    "failure_handling",
}


def _string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError("{} must be a non-empty string".format(label))
    return value


def _strings(value: Any, label: str, *, non_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or (non_empty and not value):
        raise ManifestError("{} must be a{} string array".format(label, " non-empty" if non_empty else ""))
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ManifestError("{} must contain non-empty strings".format(label))
    if len(value) != len(set(value)):
        raise ManifestError("{} must not contain duplicates".format(label))
    return list(value)


def _load_json(path: Path, label: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("{} is invalid: {}".format(label, exc)) from exc
    if not isinstance(value, dict):
        raise ManifestError("{} must be an object".format(label))
    return value


def load_policy(path: Path) -> Dict[str, Any]:
    raw = dict(_load_json(path, "workflow IR policy"))
    if set(raw) != POLICY_FIELDS or raw.get("schema_version") != POLICY_SCHEMA:
        raise ManifestError("workflow IR policy fields or schema are invalid")
    if raw.get("ir_schema_version") != IR_SCHEMA:
        raise ManifestError("workflow IR policy must target {}".format(IR_SCHEMA))
    _string(raw.get("last_updated"), "workflow IR policy last_updated")
    _string(raw.get("runtime_boundary"), "workflow IR policy runtime_boundary")
    risks = _strings(raw.get("allowed_command_risks"), "allowed_command_risks")
    if set(risks) != {"low", "medium", "high"}:
        raise ManifestError("allowed_command_risks must define low, medium and high")
    for field in ("timeout_policy", "cancellation_policy"):
        _string(raw.get(field), field)
    if raw.get("unknown_stage_policy") != "fail-closed":
        raise ManifestError("unknown_stage_policy must be fail-closed")
    terminal_states = set(_strings(raw.get("terminal_states"), "terminal_states"))
    edge_conditions = set(_strings(raw.get("edge_conditions"), "edge_conditions"))
    if "complete" not in terminal_states or edge_conditions != {"success", "failure", "cancel", "rollback"}:
        raise ManifestError("workflow IR terminal states or edge conditions are incomplete")
    projection_digests = raw.get("projection_digests")
    if not isinstance(projection_digests, dict) or not projection_digests:
        raise ManifestError("projection_digests must be a non-empty object")
    for workflow_id, digest in projection_digests.items():
        if (
            not isinstance(workflow_id, str)
            or not workflow_id
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise ManifestError("projection_digests contains an invalid entry")

    classes = raw.get("stage_classes")
    if not isinstance(classes, dict) or not classes:
        raise ManifestError("stage_classes must be a non-empty object")
    normalized_classes: Dict[str, Dict[str, Any]] = {}
    for name, value in classes.items():
        _string(name, "stage class name")
        if not isinstance(value, dict) or set(value) != STAGE_CLASS_FIELDS:
            raise ManifestError("stage class {} fields are invalid".format(name))
        if not isinstance(value.get("checkpoint"), bool):
            raise ManifestError("stage class {} checkpoint must be boolean".format(name))
        normalized = dict(value)
        normalized["required_evidence"] = _strings(
            value.get("required_evidence"), "stage class {} required_evidence".format(name)
        )
        normalized["input_refs"] = _strings(value.get("input_refs"), "stage class {} input_refs".format(name))
        normalized["output_refs"] = _strings(value.get("output_refs"), "stage class {} output_refs".format(name))
        for field in STAGE_CLASS_FIELDS - {"checkpoint", "required_evidence", "input_refs", "output_refs"}:
            _string(value.get(field), "stage class {} {}".format(name, field))
        if value.get("failure_transition") not in terminal_states:
            raise ManifestError("stage class {} failure_transition is not a terminal state".format(name))
        normalized_classes[name] = normalized

    bindings = raw.get("stage_bindings")
    if not isinstance(bindings, dict) or not bindings:
        raise ManifestError("stage_bindings must be a non-empty object")
    for stage, class_name in bindings.items():
        _string(stage, "stage binding")
        if class_name not in normalized_classes:
            raise ManifestError("stage {} references unknown class {}".format(stage, class_name))

    raw["stage_classes"] = normalized_classes
    return raw


def _frontmatter(path: Path) -> Dict[str, Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ManifestError("workflow file is unreadable: {}".format(path)) from exc
    if not lines or lines[0] != "---":
        raise ManifestError("workflow frontmatter is missing: {}".format(path))
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ManifestError("workflow frontmatter is not terminated: {}".format(path)) from exc
    try:
        value = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        raise ManifestError("workflow frontmatter is invalid: {}".format(path)) from exc
    if not isinstance(value, dict) or set(value) != WORKFLOW_FRONTMATTER_FIELDS:
        raise ManifestError("workflow frontmatter fields are invalid: {}".format(path))
    return dict(value)


def _stage_contract_digest(path: Path, stages: Sequence[str]) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "## Stage Contract"
    if marker not in text:
        raise ManifestError("workflow body is missing Stage Contract: {}".format(path))
    section = text.split(marker, 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for stage in stages:
        if "`{}`".format(stage) not in section:
            raise ManifestError("workflow Stage Contract is missing stage {}: {}".format(stage, path))
    canonical = "\n".join(line.rstrip() for line in section.strip().splitlines()) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_ir_semantics(report: Mapping[str, Any], policy: Mapping[str, Any]) -> None:
    terminal_states = set(policy["terminal_states"])
    edge_conditions = set(policy["edge_conditions"])
    for workflow in report.get("workflows", []):
        nodes = workflow.get("nodes", [])
        transitions = workflow.get("transitions", [])
        node_ids = [node["node_id"] for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ManifestError("compiled workflow IR contains duplicate node IDs")
        if [node["ordinal"] for node in nodes] != list(range(1, len(nodes) + 1)):
            raise ManifestError("compiled workflow IR node ordinals are not contiguous")
        terminal_nodes = [node for node in nodes if node["terminal"]]
        if len(terminal_nodes) != 1 or terminal_nodes[0]["terminal_state"] != "complete":
            raise ManifestError("compiled workflow IR must have one complete terminal node")
        if any(not node["inputs"] or not node["outputs"] for node in nodes):
            raise ManifestError("compiled workflow IR node I/O contracts must be non-empty")
        for node in nodes:
            stage_class = node["stage_class"]
            if stage_class not in policy["stage_classes"]:
                raise ManifestError("compiled workflow IR references an unknown stage class")
            expected = policy["stage_classes"][stage_class]
            exact_fields = {
                "side_effect": expected["side_effect"],
                "approval": expected["approval"],
                "retry": expected["retry"],
                "idempotency": expected["idempotency"],
                "checkpoint": expected["checkpoint"],
                "rollback": expected["rollback"],
                "required_evidence": expected["required_evidence"],
                "inputs": expected["input_refs"],
                "outputs": expected["output_refs"],
                "on_failure": expected["failure_transition"],
                "timeout": policy["timeout_policy"],
                "cancellation": policy["cancellation_policy"],
            }
            for field, expected_value in exact_fields.items():
                if node[field] != expected_value:
                    raise ManifestError(
                        "compiled workflow IR node policy differs from stage class: {}.{}".format(
                            node["node_id"], field
                        )
                    )

        known_nodes = set(node_ids)
        by_source: Dict[str, set[str]] = {node_id: set() for node_id in node_ids}
        success_adjacency: Dict[str, set[str]] = {node_id: set() for node_id in node_ids}
        for edge in transitions:
            source = edge["from"]
            target = edge["to"]
            condition = edge["condition"]
            if source not in known_nodes or target not in known_nodes | terminal_states:
                raise ManifestError("compiled workflow IR contains a dangling transition")
            if condition not in edge_conditions or condition in by_source[source]:
                raise ManifestError("compiled workflow IR contains an invalid or duplicate transition condition")
            by_source[source].add(condition)
            if condition == "success" and target in known_nodes:
                success_adjacency[source].add(target)
        for node in nodes:
            required = {"success", "failure", "cancel"}
            if node["rollback"] != "not-applicable":
                required.add("rollback")
            if by_source[node["node_id"]] != required:
                raise ManifestError("compiled workflow IR transition coverage is incomplete")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visiting:
                raise ManifestError("compiled workflow IR success transitions must be acyclic")
            if node_id in visited:
                return
            visiting.add(node_id)
            for target in success_adjacency[node_id]:
                visit(target)
            visiting.remove(node_id)
            visited.add(node_id)

        for node_id in node_ids:
            visit(node_id)


def compile_workflow_ir(
    manifest: Manifest,
    policy_path: Optional[Path] = None,
) -> Dict[str, Any]:
    policy_path = policy_path or manifest.root / "manifests" / "workflow_ir_policy.json"
    policy = load_policy(policy_path)
    workflows = manifest.data.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        raise ManifestError("manifest workflows must be a non-empty array")

    compiled = []
    names = set()
    manifest_names = {entry.get("name") for entry in workflows if isinstance(entry, dict)}
    if set(policy["projection_digests"]) != manifest_names:
        raise ManifestError("workflow projection digests must cover every managed workflow exactly")
    for entry in workflows:
        if not isinstance(entry, dict):
            raise ManifestError("manifest workflow entry must be an object")
        name = _string(entry.get("name"), "manifest workflow name")
        if name in names:
            raise ManifestError("duplicate workflow name: {}".format(name))
        names.add(name)
        relative = _string(entry.get("path"), "workflow {} path".format(name))
        path = manifest.root / relative
        frontmatter = _frontmatter(path)
        for field in ("name", "description", "primary_agent", "primary_skill", "command_risk"):
            if frontmatter.get(field) != entry.get(field):
                raise ManifestError("workflow {} {} differs between manifest and frontmatter".format(name, field))
        if frontmatter.get("profiles") != entry.get("profiles"):
            raise ManifestError("workflow {} profiles differ between manifest and frontmatter".format(name))
        risk = frontmatter.get("command_risk")
        if risk not in policy["allowed_command_risks"]:
            raise ManifestError("workflow {} command_risk is invalid".format(name))
        stages = _strings(frontmatter.get("stages"), "workflow {} stages".format(name))
        artifacts = _strings(frontmatter.get("artifacts"), "workflow {} artifacts".format(name))
        verification = _strings(frontmatter.get("verification"), "workflow {} verification".format(name))
        failure_handling = _strings(
            frontmatter.get("failure_handling"), "workflow {} failure_handling".format(name)
        )
        stage_contract_sha256 = _stage_contract_digest(path, stages)
        if stage_contract_sha256 != policy["projection_digests"][name]:
            raise ManifestError("workflow Stage Contract projection drifted: {}".format(name))

        nodes = []
        transitions = []
        for index, stage in enumerate(stages):
            class_name = policy["stage_bindings"].get(stage)
            if class_name is None:
                raise ManifestError("workflow {} has unbound stage {}".format(name, stage))
            stage_policy = policy["stage_classes"][class_name]
            next_stage = stages[index + 1] if index + 1 < len(stages) else None
            nodes.append({
                "node_id": stage,
                "ordinal": index + 1,
                "stage_class": class_name,
                "terminal": next_stage is None,
                "terminal_state": "complete" if next_stage is None else None,
                "inputs": list(stage_policy["input_refs"]),
                "outputs": list(stage_policy["output_refs"]),
                "side_effect": stage_policy["side_effect"],
                "approval": stage_policy["approval"],
                "retry": stage_policy["retry"],
                "timeout": policy["timeout_policy"],
                "cancellation": policy["cancellation_policy"],
                "idempotency": stage_policy["idempotency"],
                "checkpoint": stage_policy["checkpoint"],
                "rollback": stage_policy["rollback"],
                "required_evidence": list(stage_policy["required_evidence"]),
                "on_success": next_stage or "complete",
                "on_failure": stage_policy["failure_transition"],
            })
            transitions.append({"from": stage, "to": next_stage or "complete", "condition": "success"})
            transitions.append({"from": stage, "to": stage_policy["failure_transition"], "condition": "failure"})
            transitions.append({"from": stage, "to": "cancelled", "condition": "cancel"})
            if stage_policy["rollback"] != "not-applicable":
                transitions.append({"from": stage, "to": "rollback-required", "condition": "rollback"})

        compiled.append({
            "workflow_id": name,
            "version": _string(frontmatter.get("version"), "workflow {} version".format(name)),
            "description": frontmatter["description"],
            "command_risk": risk,
            "primary_agent": frontmatter["primary_agent"],
            "primary_skill": frontmatter["primary_skill"],
            "profiles": list(frontmatter["profiles"]),
            "entry_conditions": list(entry.get("entry_conditions", [])),
            "exit_evidence": list(entry.get("exit_evidence", [])),
            "artifacts": artifacts,
            "verification": verification,
            "failure_handling": failure_handling,
            "stage_contract_sha256": stage_contract_sha256,
            "nodes": nodes,
            "transitions": transitions,
        })

    report = {
        "schema_version": IR_SCHEMA,
        "policy_schema_version": POLICY_SCHEMA,
        "runtime_boundary": policy["runtime_boundary"],
        "workflow_count": len(compiled),
        "workflows": compiled,
    }
    schema_path = manifest.root / "schemas" / "workflow-ir-v2.schema.json"
    schema = _load_json(schema_path, "workflow IR schema")
    from jsonschema import Draft202012Validator

    errors = sorted(
        Draft202012Validator(schema).iter_errors(report),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise ManifestError("compiled workflow IR is invalid: {}".format(errors[0].message))
    _validate_ir_semantics(report, policy)
    return report


def _discover_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [Path.cwd()] + list(current.parents):
        if (candidate / "manifest.json").is_file() and (candidate / "manifests").is_dir():
            return candidate.resolve()
    raise ManifestError("ADK root was not found")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="workflow-ir")
    parser.add_argument("--root", type=Path)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve() if args.root else _discover_root()
    try:
        report = compile_workflow_ir(Manifest.load(root))
    except ManifestError as exc:
        print("[FAIL] {}".format(exc))
        return 1
    if args.summary_json:
        print(json.dumps({
            "schema_version": report["schema_version"],
            "status": "pass",
            "workflow_count": report["workflow_count"],
            "node_count": sum(len(item["nodes"]) for item in report["workflows"]),
            "runtime_execution_enabled": False,
        }, sort_keys=True, separators=(",", ":")))
    else:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
