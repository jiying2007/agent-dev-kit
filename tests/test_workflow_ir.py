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

    def test_full_document_identity_rejects_unchanged_stage_digest_injection(self) -> None:
        manifest = Manifest.load(ROOT)
        policy_path = ROOT / "manifests" / "workflow_ir_policy.json"
        source_name = "feature-delivery"
        entry = next(item for item in manifest.data["workflows"] if item["name"] == source_name)
        with tempfile.TemporaryDirectory() as raw:
            candidate_root = Path(raw)
            for workflow in manifest.data["workflows"]:
                relative = Path(workflow["path"])
                target = candidate_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            # The compiler also validates its schema relative to the isolated
            # source root; keep this fixture limited to the real schema file.
            schema_rel = Path("schemas/workflow-ir-v2.schema.json")
            schema_target = candidate_root / schema_rel
            schema_target.parent.mkdir(parents=True, exist_ok=True)
            schema_target.write_bytes((ROOT / schema_rel).read_bytes())
            candidate = Manifest(candidate_root, manifest.data, candidate_root / "manifest.json")
            self.assertEqual(compile_workflow_ir(candidate, policy_path)["workflow_count"],
                             len(manifest.data["workflows"]))
            target = candidate_root / entry["path"]
            baseline = target.read_text(encoding="utf-8")
            for payload in (
                "\n## Stage Contract\n3. `publish`: injected\n",
                "\n1. ## Stage Contract\n   3. `publish`: nested\n",
                "\n<h2\n>Stage Contract</h2>\n3. `publish`: raw HTML\n",
                "\nStage Contract\n-\n3. `publish`: Setext\n",
                "\nHarmless-looking prose outside the Stage Contract\n",
            ):
                target.write_text(baseline + payload, encoding="utf-8")
                with self.assertRaisesRegex(ManifestError, "workflow document source identity drifted"):
                    compile_workflow_ir(candidate, policy_path)
            target.write_text(baseline, encoding="utf-8")
            self.assertEqual(compile_workflow_ir(candidate, policy_path)["workflow_count"],
                             len(manifest.data["workflows"]))
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
            # Existing Chinese workflow stages use a full-width colon.
            # Parse both punctuation forms without allowing hidden stages.
            path.write_text(
                "# Example\n\n## Stage Contract\n"
                "1. `propose`：计划\n2. `verify`: 验证\n\n## Commands\n",
                encoding="utf-8",
            )
            self.assertEqual(len(_stage_contract_digest(path, ["propose", "verify"])), 64)

            # The old parser truncated at the first later H2, so a second
            # Stage Contract heading kept the previous digest unchanged.
            valid_document = path.read_text(encoding="utf-8")
            valid_digest = _stage_contract_digest(path, ["propose", "verify"])
            # A legitimate command code fence is fine; it must not change
            # the authority or the digest of the preceding Stage Contract.
            path.write_text(valid_document + "\n```sh\necho ok\n```\n", encoding="utf-8")
            self.assertEqual(_stage_contract_digest(path, ["propose", "verify"]), valid_digest)
            for trailing in (
                "\n## Stage Contract\n3. `publish`: hidden unauthorized stage\n",
                "\n### Stage Contract\n3. `publish`: hidden under H3\n",
                "\n  ## Stage Contract\n3. `publish`: indented duplicate\n",
                "\n## stage Contract\n3. `publish`: mixed-case duplicate\n",
                "\n## Stage  Contract\n3. `publish`: extra-space duplicate\n",
                "\n## Stage Contract (copy)\n3. `publish`: ambiguous heading\n",
                "\nStage Contract\n--------------\n3. `publish`: Setext H2 duplicate\n",
                "\nStage Contract\n-\n3. `publish`: single-dash Setext H2 duplicate\n",
                "\nStage Contract\n=\n3. `publish`: single-equals Setext H1 duplicate\n",
                "\n<h2>Stage Contract</h2>\n3. `publish`: HTML H2 duplicate\n",
                "\n<div><h2>Stage Contract</h2></div>\n3. `publish`: nested HTML H2 duplicate\n",
                "\n<h2\n>Stage Contract</h2>\n3. `publish`: split HTML H2 opener\n",
                "\n<h2\n class=\"stage\">Stage Contract</h2>\n3. `publish`: split HTML H2 with attribute\n",
                "\n<H2\n>Stage Contract</H2>\n3. `publish`: split uppercase HTML H2\n",
                "\n> Stage Contract\n> -\n> 3. `publish`: blockquote Setext H2 duplicate\n",
                "\n> > Stage Contract\n> > =\n> > 3. `publish`: nested blockquote Setext H1\n",

                "\n## Stage\u3000Contract\n3. `publish`: ideographic-space duplicate\n",
                "\n## Stage\u00a0Contract\n3. `publish`: nonbreaking-space duplicate\n",
                "\n＃＃ Stage Contract\n3. `publish`: fullwidth-hash duplicate\n",
                "\n## Stage\u200bContract\n3. `publish`: zero-width duplicate\n",
                "\n## Stage&nbsp;Contract\n3. `publish`: named HTML entity\n",
                "\n## Stage&#32;Contract\n3. `publish`: numeric HTML entity\n",
                "\n## Sta&#103;e Contract\n3. `publish`: encoded heading letter\n",
                "\n## Stage\u034f Contract\n3. `publish`: combining grapheme joiner\n",
                "\n## Stage\ufe0e Contract\n3. `publish`: variation selector\n",
                "\n## St\u0430ge Contract\n3. `publish`: Cyrillic homoglyph\n",
                "\n> ## Stage Contract\n3. `publish`: blockquoted heading\n",
                "\n1. ## Stage Contract\n   3. `publish`: nested ordered-list heading\n",
                "\n1) ## Stage Contract\n   3. `publish`: parenthesized ordered-list heading\n",
                "\n> 1. ## Stage Contract\n   3. `publish`: blockquoted ordered-list heading\n",
                "\n- ## Stage Contract\n  3. `publish`: unordered-list heading\n",
                "\n## Stage\u2060 Contract\n3. `publish`: word joiner\n",
                "\n## Stage contract\n3. `publish`: lowercase duplicate\n",
                "\n## Stage  Contract\n3. `publish`: padded duplicate\n",
                "\n## Stage-Contract\n3. `publish`: punctuation duplicate\n",
                "\n# STAGE CONTRACT\n3. `publish`: H1 alias\n",
                "\n    ```\n## Stage Contract\n3. `publish`: indented-fence bypass\n    ```\n",
                "\n```python\n~~~\n## Stage Contract\n3. `publish`: mismatched-fence bypass\n```\n",
                "\n```md\n## Stage Contract\n3. `publish`: code-example duplicate\n```\n",
                "\n&#35;&#35; Stage Contract\n3. `publish`: encoded heading marker\n",
            ):
                path.write_text(valid_document + trailing, encoding="utf-8")
                with self.assertRaises(ManifestError):
                    _stage_contract_digest(path, ["propose", "verify"])

            path.write_text(valid_document + "\nDocument discusses Stage Contract again\n", encoding="utf-8")
            self.assertEqual(_stage_contract_digest(path, ["propose", "verify"]), valid_digest)

            for body in (
                "1. `propose`: plan\n2. `package`: write\n3. `verify`: inspect",
                "1. `verify`: inspect\n2. `propose`: plan",
                "1. `propose`: plan\n2. `propose`: duplicated",
                "1. `propose`: plan\n3. `verify`: skipped stage number",
                "1. `propose`: plan\n2. `verify`: inspect\n3. `publish` — hidden stage",
                "1. `propose`: plan\n2. `verify`: inspect\n 3. `publish`: indented stage",
                "1. `propose`: plan\n2. `verify`: inspect\n- 3. `publish`: nested stage",
                "1. `propose`: plan\n2. `verify`: inspect\n0. `publish`: zero stage",
                "1. `propose`: plan\n2. `verify`: inspect\n3) `publish`: invalid delimiter",
                                "1. `propose`: plan\n2. `verify`: inspect\n+ 3. `publish`: plus-prefixed stage",
                                "1. `propose`: plan\n2. `verify`: inspect\n> 3. `publish`: quoted stage",
                                "1. `propose`: plan\n2. `verify`: inspect\n3 . `publish`: spaced ordinal",
                "1. `propose`: plan\n2. `verify`: inspect\n3、 `publish`：中文编号",
                "1. `propose`: plan\n2. `verify`: inspect\n第三步 `publish`: Chinese stage",
                "1. `propose`: plan\n2. `verify`: inspect\nNotes: extra stage prose",
            ):
                path.write_text("# Example\n\n## Stage Contract\n" + body
                                + "\n\n## Commands\n", encoding="utf-8")
                with self.assertRaises(ManifestError):
                    _stage_contract_digest(path, ["propose", "verify"])

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
