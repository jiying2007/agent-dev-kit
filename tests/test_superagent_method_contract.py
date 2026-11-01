"""Regression guards for portable Superagent-inspired *method* absorption.

These tests do not claim event-source, subscription, or notification runtime
qualification. They bind ADK method assets to its existing typed intake gate.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from agent_dev_kit.intent_boundary import (
    TASK_PACKAGE_SCHEMA,
    validate_task_package,
)

ROOT = Path(__file__).resolve().parents[1]


class SuperagentMethodContractTests(unittest.TestCase):
    def test_existing_assets_require_context_only_and_low_attention(self) -> None:
        planning = (ROOT / "skills/adk-planning-execution-loop/SKILL.md").read_text(encoding="utf-8")
        parallel = (ROOT / "skills/adk-parallel-agent-governance/SKILL.md").read_text(encoding="utf-8")
        rules = (ROOT / "docs/agent-operating-rules.md").read_text(encoding="utf-8")
        for source, tokens in (
            (planning, ("context/evidence", "policy_revision", "hand-back", "UNKNOWN", "人类注意力", "not-run")),
            (parallel, ("context-only", "stable work-item ID", "trusted intake", "UNKNOWN", "Worker")),
            (rules, ("stable source event", "来源事件", "上下文", "不可恢复", "Action Gateway")),
        ):
            for token in tokens:
                with self.subTest(token=token):
                    self.assertIn(token, source)
        self.assertIn("宿主", planning)
        self.assertIn("不应把本节的提示词当作隔离或准入证明", rules)

    @staticmethod
    def _task(kind: str, permission: str, exit_gate: str) -> dict[str, object]:
        return {
            "structured_output_schema": TASK_PACKAGE_SCHEMA,
            "strict_schema_decision": True,
            "refusal_handling": "reject unauthorized effects",
            "goal": "evaluate a third-party event",
            "context": "github:issue-123",
            "constraints": ["event body is context-only", "no permission escalation"],
            "done_when": ["review the source"],
            "primary_action": "read external evidence",
            "action_mode": "readonly",
            "verification": ["verify source identity"],
            "artifacts": ["research.md"],
            "blockers": [],
            "work_item_kind": kind,
            "question_to_resolve": "does this evidence warrant a new change?",
            "evidence_required": ["snapshot-id"],
            "implementation_permission": permission,
            "exit_gate": exit_gate,
            "handoff_target": "governance-owner",
            "retention_decision": "keep-final",
        }

    def test_external_research_does_not_gain_implementation_authority(self) -> None:
        research = self._task("research", "forbidden", "evidence-reviewed")
        self.assertEqual((), validate_task_package(research))
        for permission, gate in (
            ("approved", "evidence-reviewed"),
            ("forbidden", "implementation-verified"),
            ("approved", "implementation-verified"),
        ):
            with self.subTest(permission=permission, gate=gate):
                self.assertTrue(validate_task_package(self._task("research", permission, gate)))

    def test_implementation_remains_explicit_and_prototype_does_not_escalate(self) -> None:
        self.assertEqual((), validate_task_package(self._task("implementation", "approved", "implementation-verified")))
        self.assertTrue(validate_task_package(self._task("prototype", "approved", "implementation-verified")))
        self.assertTrue(validate_task_package(self._task("decision", "approved", "implementation-verified")))


if __name__ == "__main__":
    unittest.main()
