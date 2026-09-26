from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "agent_dev_kit"


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
        elif isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
    return result


class NativeCampaignBoundaryTest(unittest.TestCase):
    def test_dependency_direction_is_contract_to_execution_to_orchestration(self) -> None:
        contract = imports(SRC / "native_campaign_contract.py")
        execution = imports(SRC / "native_campaign_execution.py")
        orchestration = imports(SRC / "native_campaign.py")

        self.assertNotIn("native_campaign", contract)
        self.assertNotIn("native_campaign", execution)
        self.assertNotIn("agent_dev_kit.native_campaign", contract)
        self.assertNotIn("agent_dev_kit.native_campaign", execution)
        self.assertTrue(
            "native_campaign_contract" in orchestration
            or "agent_dev_kit.native_campaign_contract" in orchestration
        )
        self.assertTrue(
            "native_campaign_execution" in orchestration
            or "agent_dev_kit.native_campaign_execution" in orchestration
        )

    def test_native_campaign_v2_is_the_only_active_certification_contract(self) -> None:
        active = {
            "native-target-campaign-plan": ROOT / "schemas" / "native-target-campaign-plan-v2.schema.json",
            "native-target-campaign-evidence": ROOT / "schemas" / "native-target-campaign-evidence-v2.schema.json",
            "native-target-conformance-receipt": ROOT / "schemas" / "native-target-conformance-receipt-v2.schema.json",
        }
        retired = (
            ROOT / "schemas" / "native-target-campaign-plan-v1.schema.json",
            ROOT / "schemas" / "native-target-campaign-evidence-v1.schema.json",
            ROOT / "schemas" / "native-target-conformance-receipt-v1.schema.json",
        )
        for path in active.values():
            self.assertTrue(path.is_file(), path)
        for path in retired:
            self.assertFalse(path.exists(), path)

        import json

        registry = json.loads((ROOT / "manifests" / "contract_registry.json").read_text(encoding="utf-8"))
        contracts = {item["id"]: item for item in registry["contracts"]}
        for contract_id, schema_path in active.items():
            record = contracts[contract_id]
            self.assertEqual(record["version"], "2", record)
            self.assertEqual(record["compatibility"], "hard-cut", record)
            self.assertEqual(record["schema_path"], schema_path.relative_to(ROOT).as_posix(), record)

        runbook = (ROOT / "docs" / "runbooks" / "native-campaign.md").read_text(encoding="utf-8")
        self.assertNotIn("campaign plan/evidence/receipt v1 schemas remain unchanged", runbook)
        self.assertIn("active certification path is the v2 hard-cut", runbook)

    def test_bounded_context_modules_stay_under_repository_default_budget(self) -> None:
        for name in (
            "native_campaign.py",
            "native_campaign_contract.py",
            "native_campaign_execution.py",
        ):
            with self.subTest(name=name):
                self.assertLessEqual((SRC / name).stat().st_size, 30000)


if __name__ == "__main__":
    unittest.main()
