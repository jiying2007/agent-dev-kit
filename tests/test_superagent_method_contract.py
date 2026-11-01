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
            (planning, ("context/evidence", "hand-back", "UNKNOWN")),
            (parallel, ("context-only", "stable work-item ID", "Worker")),
            (rules, ("source_id", "native_event_id", "policy_revision",
                     "trusted intake", "UNKNOWN", "not-run", "Action Gateway")),
        ):
            for token in tokens:
                with self.subTest(token=token):
                    self.assertIn(token, source)
        self.assertIn("只有已验证交付", rules)
        self.assertIn("不应把本节的提示词当作隔离或准入证明", rules)
        self.assertNotIn("danger-full-access", planning)
        self.assertNotIn("danger-full-access", parallel)

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
            "artifacts": (["prototype_evidence:reviewed-prototype.md"] if kind == "prototype" else ["research.md"]),
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
                self.as    def test_explicit_implementation_and_valid_prototype_baselines(self) -> None:
        implementation = self._task("implementation", "approved", "implementation-verified")
        prototype = self._task("prototype", "forbidden", "prototype-reviewed")
        decision = self._task("decision", "forbidden", "owner-decision")
        for item in (implementation, prototype, decision):
            self.assertEqual((), validate_task_package(item))

    def test_prototype_and_decision_reject_only_the_wrong_boundary(self) -> None:
        for kind, gate in (("prototype", "prototype-reviewed"), ("decision", "owner-decision")):
            valid = self._task(kind, "forbidden", gate)
            self.assertEqual((), validate_task_package(valid))
            with self.subTest(kind=kind, field="permission"):
                self.assertEqual(
                    (f"{kind} requires implementation_permission=forbidden",),
                    validate_task_package(dict(valid, implementation_permission="approved")),
                )
            with self.subTest(kind=kind, field="exit_gate"):
                self.assertEqual(
                    (f"{kind} requires exit_gate={gate}",),
                    validate_task_package(dict(valid, exit_gate="implementation-verified")),
                )

    def test_prototype_artifact_does_not_hide_permission_failures(self) -> None:
        valid = self._task("prototype", "forbidden", "prototype-reviewed")
        self.assertEqual((), validate_task_package(valid))
        self.assertEqual(
            ("prototype requires implementation_permission=forbidden",
             "prototype requires exit_gate=prototype-reviewed"),
            validate_task_package(
                dict(valid, implementation_permission="approved", exit_gate="implementation-verified")
            ),
        )
        self.assertEqual(
            ("prototype requires a prototype_evidence artifact",),
            validate_task_package(dict(valid, artifacts=["research.md"])),
        )


if __name__ == "__main__":
    unittest.main()
