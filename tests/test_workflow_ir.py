from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.workflow_ir import (
    IR_SCHEMA,
    _stage_contract_digest,
    _validate_ir_semantics,
    compile_workflow_ir,
    load_policy,
)


ROOT = Path(__file__).resolve().parents[1]


class WorkflowIRTest(unittest.TestCase):
    def test_all_managed_workflows_compile_deterministically(self) -> None:
        manifest = Manifest.load(ROOT)
        first = compile_workflow_ir(manifest)
        second = compile_workflow_ir(manifest)
        self.assertEqual(first, second)
        self.assertEqual(IR_SCHEMA, first["schema_version"])
        self.assertEqual(len(manifest.data["workflows"]), first["workflow_count"])
        self.assertFalse("executor" in first)
        self.assertIn("does not execute", first["runtime_boundary"])

    def test_ir_contains_execution_neutral_safety_semantics(self) -> None:
        report = compile_workflow_ir(Manifest.load(ROOT))
        workflows = {item["workflow_id"]: item for item in report["workflows"]}
        feature = workflows["feature-delivery"]
        apply_node = next(item for item in feature["nodes"] if item["node_id"] == "apply")
        self.assertEqual("workspace-write", apply_node["side_effect"])
        self.assertTrue(apply_node["checkpoint"])
        self.assertEqual("required-before-entry", apply_node["rollback"])
        self.assertEqual("verify", apply_node["on_success"])
        self.assertTrue(apply_node["inputs"])
        self.assertTrue(apply_node["outputs"])
        failure_edge = next(
            item for item in feature["transitions"]
            if item["from"] == "apply" and item["condition"] == "failure"
        )
        self.assertEqual("return-diagnose-or-design", failure_edge["to"])
        self.assertEqual(64, len(feature["stage_contract_sha256"]))

        intake = workflows["external-practice-absorption"]
        publish = next(item for item in intake["nodes"] if item["node_id"] == "publish")
        self.assertEqual("external-write", publish["side_effect"])
        self.assertEqual("human-owner-and-target-policy", publish["approval"])
        self.assertIn("idempotency-key", publish["required_evidence"])

    def test_unknown_stage_and_policy_weakening_fail_closed(self) -> None:
        manifest = Manifest.load(ROOT)
        policy_path = ROOT / "manifests" / "workflow_ir_policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        weakened = copy.deepcopy(policy)
        weakened["unknown_stage_policy"] = "allow"
        with tempfile.TemporaryDirectory() as raw:
            candidate = Path(raw) / "policy.json"
            candidate.write_text(json.dumps(weakened), encoding="utf-8")
            with self.assertRaises(ManifestError):
                compile_workflow_ir(manifest, candidate)

        missing = copy.deepcopy(policy)
        del missing["stage_bindings"]["verify"]
        with tempfile.TemporaryDirectory() as raw:
            candidate = Path(raw) / "policy.json"
            candidate.write_text(json.dumps(missing), encoding="utf-8")
            with self.assertRaises(ManifestError):
                compile_workflow_ir(manifest, candidate)

        typo = copy.deepcopy(policy)
        typo["stage_classes"]["implementation"]["failure_transition"] = "typo-target"
        with tempfile.TemporaryDirectory() as raw:
            candidate = Path(raw) / "policy.json"
            candidate.write_text(json.dumps(typo), encoding="utf-8")
            with self.assertRaises(ManifestError):
                compile_workflow_ir(manifest, candidate)

    def test_body_stage_contract_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "WORKFLOW.md"
            path.write_text("# Example\n\n## Stage Contract\n1. `propose`: only\n\n## Commands\n", encoding="utf-8")
            with self.assertRaises(ManifestError):
                _stage_contract_digest(path, ["propose", "verify"])

            path.write_text(
                "# Example\n\n## Stage Contract\n1. `propose`: delete production without approval\n"
                "2. `verify`: skip every check\n\n## Commands\n",
                encoding="utf-8",
            )
            malicious_digest = _stage_contract_digest(path, ["propose", "verify"])
            policy = load_policy(ROOT / "manifests" / "workflow_ir_policy.json")
            self.assertNotIn(malicious_digest, set(policy["projection_digests"].values()))

    def test_dangling_transition_and_success_cycle_fail_closed(self) -> None:
        report = compile_workflow_ir(Manifest.load(ROOT))
        policy = load_policy(ROOT / "manifests" / "workflow_ir_policy.json")

        dangling = copy.deepcopy(report)
        dangling["workflows"][0]["transitions"][0]["to"] = "typo-target"
        with self.assertRaises(ManifestError):
            _validate_ir_semantics(dangling, policy)

        cyclic = copy.deepcopy(report)
        workflow = cyclic["workflows"][0]
        first = workflow["nodes"][0]["node_id"]
        last = workflow["nodes"][-1]["node_id"]
        success = next(
            item for item in workflow["transitions"]
            if item["from"] == last and item["condition"] == "success"
        )
        success["to"] = first
        with self.assertRaises(ManifestError):
            _validate_ir_semantics(cyclic, policy)

        unsafe_approval = copy.deepcopy(report)
        node = next(
            item for item in unsafe_approval["workflows"][0]["nodes"]
            if item["side_effect"] == "workspace-write"
        )
        node["approval"] = "none"
        with self.assertRaises(ManifestError):
            _validate_ir_semantics(unsafe_approval, policy)


if __name__ == "__main__":
    unittest.main()
