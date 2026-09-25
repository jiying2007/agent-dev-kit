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
