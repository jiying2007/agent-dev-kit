from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.phase_context import resolve_delivery_lifecycle as phase_delivery_lifecycle
from agent_dev_kit.skill_relationships import (
    _contract,
    _entries,
    _explicit_relationships,
    _load_contract,
    _resolve_delivery_lifecycle,
    resolve_delivery_lifecycle,
    resolve_skill_relationships,
)

ROOT = Path(__file__).resolve().parents[1]


class SkillRelationshipContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = Manifest.load(ROOT)
        cls.entries = _entries(cls.manifest)

    def test_typed_relationships_are_delivery_authority(self) -> None:
        result = resolve_skill_relationships(self.manifest)
        self.assertEqual(result["status"], "pass")
        self.assertFalse(result["legacy_depends_on_authoritative_for_delivery_sequencing"])
        typed = {
            (row["from"], row["to"], row["type"], row["requirement"])
            for row in result["typed_relationships"]
        }
        self.assertIn(
            (
                "adk-code-review-loop",
                "adk-verification-before-completion",
                "delivery-precedence",
                "required",
            ),
            typed,
        )
        self.assertIn(
            (
                "adk-verification-before-completion",
                "adk-commit-pr-quality-gate",
                "delivery-precedence",
                "required",
            ),
            typed,
        )
        self.assertIn(
            (
                "adk-commit-pr-quality-gate",
                "adk-branch-closeout",
                "delivery-precedence",
                "required",
            ),
            typed,
        )

    def test_terminal_lifecycle_has_single_typed_authority(self) -> None:
        direct = resolve_delivery_lifecycle(self.manifest)
        facade = phase_delivery_lifecycle(self.manifest)
        self.assertEqual(direct["steps"], facade["steps"])
        self.assertEqual(
            [row["stage"] for row in direct["steps"]],
            ["review", "completion", "commit-pr", "closeout"],
        )
        self.assertEqual(
            direct["relationship_semantics_source"],
            "manifests/skill_relationship_contracts_v1.json",
        )
        self.assertFalse(direct["legacy_manifest_dependencies_authoritative"])

    def test_historical_inverted_review_dependency_is_removed(self) -> None:
        review = self.entries["adk-code-review-loop"]
        self.assertNotIn("adk-verification-before-completion", review.get("depends_on", []))

    def test_unknown_typed_endpoint_fails_closed(self) -> None:
        contract, _ = _contract(self.manifest)
        mutated = json.loads(json.dumps(contract))
        mutated["relationships"].append(
            {
                "from": "adk-does-not-exist",
                "to": "adk-code-review-loop",
                "type": "handoff",
                "requirement": "required",
            }
        )
        with self.assertRaisesRegex(ManifestError, "endpoint is unknown"):
            _explicit_relationships(mutated, self.entries)

    def test_delivery_precedence_must_exactly_match_adjacent_lifecycle(self) -> None:
        contract, _ = _contract(self.manifest)
        mutated = json.loads(json.dumps(contract))
        mutated["relationships"] = [
            row
            for row in mutated["relationships"]
            if not (
                row["from"] == "adk-verification-before-completion"
                and row["to"] == "adk-commit-pr-quality-gate"
                and row["type"] == "delivery-precedence"
            )
        ]
        explicit = _explicit_relationships(mutated, self.entries)
        with self.assertRaisesRegex(ManifestError, "exactly match adjacent"):
            _resolve_delivery_lifecycle(self.manifest, mutated, self.entries, explicit)

    def test_inverted_terminal_stage_order_fails_closed(self) -> None:
        contract, _ = _contract(self.manifest)
        mutated = json.loads(json.dumps(contract))
        mutated["delivery_lifecycle"]["steps"][0]["stage"] = "completion"
        mutated["delivery_lifecycle"]["steps"][1]["stage"] = "review"
        explicit = _explicit_relationships(mutated, self.entries)
        with self.assertRaisesRegex(ManifestError, "review -> completion"):
            _resolve_delivery_lifecycle(self.manifest, mutated, self.entries, explicit)

    def test_only_delivery_precedence_can_claim_sequencing_authority(self) -> None:
        contract_path = ROOT / "manifests" / "skill_relationship_contracts_v1.json"
        schema_path = ROOT / "schemas" / "skill-relationship-contract-v1.schema.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["relationship_types"]["handoff"]["sequencing_authority"] = True
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            bad_contract = temp_root / "contract.json"
            local_schema = temp_root / "schema.json"
            bad_contract.write_text(json.dumps(contract), encoding="utf-8")
            local_schema.write_bytes(schema_path.read_bytes())
            with self.assertRaisesRegex(ManifestError, "Only delivery-precedence"):
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
