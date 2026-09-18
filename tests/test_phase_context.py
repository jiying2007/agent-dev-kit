from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.phase_context import (
    _contract,
    _load_contract,
    _resolve_selector,
    _skill_entries,
    resolve_delivery_lifecycle,
    resolve_phase_context,
)

ROOT = Path(__file__).resolve().parents[1]


class PhaseContextContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = Manifest.load(ROOT)
        cls.entries = _skill_entries(cls.manifest)

    def test_manifest_has_no_phase_to_skill_path_mirror(self) -> None:
        for section in ("context_layers", "embedded_context_layers"):
            value = self.manifest.data.get(section)
            self.assertIsInstance(value, dict)
            self.assertNotIn("L2-phase-triggered", value)

    def test_review_phase_resolves_primary_plus_language_overlay(self) -> None:
        result = resolve_phase_context(self.manifest, "general", "review")
        self.assertEqual(result["schema"], "adk-phase-context-resolution/v2")
        self.assertEqual(result["status"], "pass")
        rows = {item["name"]: item for item in result["skills"]}
        self.assertEqual(rows["adk-code-review-loop"]["runtime_role"], "primary")
        self.assertEqual(rows["adk-chinese-code-review"]["runtime_role"], "supporting")
        self.assertEqual(
            [item["name"] for item in result["skills"] if item["runtime_role"] == "primary"],
            ["adk-code-review-loop"],
        )

    def test_verify_phase_separates_test_execution_from_completion_gate(self) -> None:
        result = resolve_phase_context(self.manifest, "general", "verify")
        rows = {item["name"]: item for item in result["skills"]}
        self.assertEqual(rows["adk-test-strategy"]["runtime_role"], "primary")
        self.assertEqual(rows["adk-artifact-gating"]["runtime_role"], "governance")
        self.assertNotIn("adk-verification-before-completion", rows)

    def test_driver_phase_contains_implementation_bringup_and_interrupt_dma(self) -> None:
        result = resolve_phase_context(self.manifest, "embedded", "driver-development")
        names = {item["name"] for item in result["skills"]}
        self.assertTrue(
            {
                "adk-driver-implementation",
                "adk-driver-bringup-checklist",
                "adk-interrupt-dma-patterns",
            }.issubset(names),
            names,
        )

    def test_delivery_lifecycle_is_review_then_completion_then_commit_then_closeout(self) -> None:
        result = resolve_delivery_lifecycle(self.manifest)
        self.assertEqual(result["schema"], "adk-delivery-lifecycle-resolution/v2")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["pre_review_requirements"], ["verification-evidence"])
        self.assertEqual(
            result["relationship_semantics_source"],
            "manifests/skill_relationship_contracts_v2.json",
        )
        self.assertEqual(
            [(item["stage"], item["name"]) for item in result["steps"]],
            [
                ("review", "adk-code-review-loop"),
                ("completion", "adk-verification-before-completion"),
                ("commit-pr", "adk-commit-pr-quality-gate"),
                ("closeout", "adk-branch-closeout"),
            ],
        )

    def test_skill_selector_fails_closed_on_role_drift(self) -> None:
        with self.assertRaisesRegex(ManifestError, "role drift"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {
                    "kind": "skill",
                    "skill": "adk-code-review-loop",
                    "expected_runtime_role": "supporting",
                },
            )

    def test_unknown_skill_fails_closed(self) -> None:
        with self.assertRaisesRegex(ManifestError, "unknown Skill"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {"kind": "skill", "skill": "adk-does-not-exist", "expected_runtime_role": "primary"},
            )

    def test_non_unique_group_cannot_be_promoted_to_exactly_one_primary(self) -> None:
        with self.assertRaisesRegex(ManifestError, "exactly one primary"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {
                    "kind": "selection-group",
                    "selection_group": "debugging",
                    "include_runtime_roles": ["primary"],
                    "primary_cardinality": "exactly-one",
                },
            )

    def test_phase_resource_cannot_escape_repository_root(self) -> None:
        contract, digest = _contract(self.manifest)
        mutated = json.loads(json.dumps(contract))
        mutated["domains"]["general"]["review"]["resources"] = ["../../outside"]
        with patch("agent_dev_kit.phase_context._contract", return_value=(mutated, digest)):
            with self.assertRaisesRegex(ManifestError, "escapes allowed root"):
                resolve_phase_context(self.manifest, "general", "review")

    def test_contract_schema_rejects_unknown_top_level_field(self) -> None:
        contract_path = ROOT / "manifests" / "phase_context_contract_v2.json"
        schema_path = ROOT / "schemas" / "phase-context-contract-v2.schema.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["unexpected_authority"] = True
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            bad_contract = temp_root / "contract.json"
            local_schema = temp_root / "schema.json"
            bad_contract.write_text(json.dumps(contract), encoding="utf-8")
            local_schema.write_bytes(schema_path.read_bytes())
            with self.assertRaisesRegex(ManifestError, "schema validation failed"):
                _load_contract(
                    str(bad_contract),
                    bad_contract.stat().st_mtime_ns,
                    bad_contract.stat().st_size,
                    str(local_schema),
                    local_schema.stat().st_mtime_ns,
                    local_schema.stat().st_size,
                )


if __name__ == "__main__":
    unittest.main()
