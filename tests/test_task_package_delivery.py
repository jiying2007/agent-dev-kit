"""Validate actual shipped task examples and malformed JSON at the typed boundary.

These tests exercise source contracts and compiler outputs, not a live dispatcher.
"""
from __future__ import annotations

import copy
from datetime import date
import json
from pathlib import Path
import re
import tempfile
import unittest

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.intent_boundary import validate_prototype_evidence, validate_task_package
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]


def research_package() -> dict[str, object]:
    return {
        "structured_output_schema": "adk-task-package-schema-v2",
        "strict_schema_decision": True,
        "refusal_handling": "blocked or replan",
        "goal": "Check the retry deadline",
        "context": "Frozen source and authorized read scope",
        "constraints": ["read-only"],
        "done_when": ["Boundary evidence reviewed"],
        "primary_action": "inspect",
        "action_mode": "read-only",
        "verification": ["Read the boundary assertion"],
        "artifacts": ["review.md"],
        "blockers": [],
        "work_item_kind": "research",
        "question_to_resolve": "Is equality at the deadline allowed?",
        "evidence_required": ["Condition and boundary test"],
        "implementation_permission": "forbidden",
        "exit_gate": "evidence-reviewed",
        "handoff_target": "task-owner",
        "retention_decision": "keep-final",
    }


def prototype_evidence() -> dict[str, object]:
    return {
        "structured_output_schema": "adk-prototype-evidence-schema-v1",
        "question": "Does cancellation preserve the state invariant?",
        "base_commit": "a" * 40,
        "scope": "isolated state fixture",
        "artifact_path": "evidence/prototype.json",
        "artifact_sha256": "b" * 64,
        "runtime_assumptions": "host simulation only",
        "observed_result": "late completion ignored",
        "decision_supported": True,
        "verification_command": "python3 state_fixture.py",
        "verification_exit_code": 0,
        "retention_decision": "expire",
        "expires_at": "2026-12-01",
        "cleanup_owner": "fixture-owner",
        "rollback_anchor": "remove the isolated fixture",
        "active_references_absent": True,
    }


class TaskPackageTypeTests(unittest.TestCase):
    def test_all_work_kinds_preserve_their_permission_and_exit_gate(self):
        for kind, permission, gate in (
            ("decision", "forbidden", "owner-decision"),
            ("research", "forbidden", "evidence-reviewed"),
            ("prototype", "forbidden", "prototype-reviewed"),
            ("implementation", "approved", "implementation-verified"),
        ):
            with self.subTest(kind=kind):
                task = dict(research_package(), work_item_kind=kind,
                            implementation_permission=permission, exit_gate=gate)
                if kind == "prototype":
                    task["artifacts"] = ["prototype_evidence:evidence/prototype.json"]
                self.assertEqual((), validate_task_package(task))
                wrong_permission = "forbidden" if permission == "approved" else "approved"
                self.assertTrue(validate_task_package(dict(task, implementation_permission=wrong_permission)))
                self.assertTrue(validate_task_package(dict(task, exit_gate="wrong-gate")))
        self.assertTrue(validate_task_package(dict(research_package(),
                        work_item_kind="prototype", exit_gate="prototype-reviewed")))

    def test_task_malformed_json_types_return_errors_without_exceptions(self):
        for kind in ("research", "prototype"):
            task = research_package()
            if kind == "prototype":
                task.update(work_item_kind=kind, exit_gate="prototype-reviewed",
                            artifacts=["prototype_evidence:evidence/prototype.json"])
            for field, values in {
                "artifacts": (None, 1, True, {}, [1], [None], [], "review.md"),
                "work_item_kind": (None, 1, True, {}, [], ["research"], ""),
                "retention_decision": (None, 1, True, {}, [], ["keep-final"], ""),
            }.items():
                for value in values:
                    with self.subTest(kind=kind, field=field, value=value):
                        errors = validate_task_package(dict(task, **{field: value}))
                        self.assertIsInstance(errors, tuple)
                        self.assertTrue(errors)

    def test_prototype_malformed_types_and_expiry_are_not_coerced(self):
        valid = prototype_evidence()
        self.assertEqual((), validate_prototype_evidence(valid, as_of=date(2026, 11, 17)))
        for field, values in {
            "retention_decision": (None, 1, True, {}, [], ["expire"]),
            "expires_at": (None, 20261201, True, {}, [], ["2026-12-01"]),
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    errors = validate_prototype_evidence(dict(valid, **{field: value}),
                                                         as_of=date(2026, 11, 17))
                    self.assertIsInstance(errors, tuple)
                    self.assertTrue(errors)
        self.assertTrue(validate_prototype_evidence(
            dict(valid, expires_at="2026-11-16"), as_of=date(2026, 11, 17)))
        self.assertTrue(validate_prototype_evidence(
            dict(valid, retention_decision="delete-orphan", active_references_absent=False)))


class ExportedTaskPackageTests(unittest.TestCase):
    def test_shipped_example_is_complete_and_preserves_scope_without_extra_fields(self):
        manifest = Manifest.load(ROOT)
        with tempfile.TemporaryDirectory(prefix="adk-task-package-consumer-") as directory:
            for target in ("claude-code", "opencode"):
                with self.subTest(target=target):
                    result = export_assets(manifest, target, Path(directory), ["core"])
                    consumer = Path(result["output"])
                    reference = consumer / "skills/adk-task-breakdown/references/task-packaging.md"
                    text = reference.read_text(encoding="utf-8")
                    blocks = re.findall(
                        r"<!-- adk-example: task-package-v2 -->\n```json\n(.*?)\n```",
                        text, re.DOTALL,
                    )
                    self.assertEqual(1, len(blocks), "consumer needs one complete executable v2 example")
                    package = json.loads(blocks[0])
                    self.assertEqual(set(research_package()), set(package))
                    self.assertEqual((), validate_task_package(package))
                    self.assertEqual("research", package["work_item_kind"])
                    self.assertEqual("forbidden", package["implementation_permission"])
                    for expected in (
                        "scope_read: src/retry.py", "scope_write: []",
                        "global_constraints: read-only", "interfaces: retry deadline",
                    ):
                        self.assertIn(expected, package["constraints"])
                    self.assertFalse((consumer / "manifests/structured_output_contracts.json").exists())
                    self.assertIn("ready_to_handoff", text)
                    for field in ("scope_read", "scope_write", "global_constraints", "interfaces",
                                  "ready_to_handoff", "owner"):
                        rejected = dict(package, **{field: True})
                        self.assertTrue(validate_task_package(rejected), field)
                    # The shipped payload supports the existing kind transitions,
                    # but cannot declare research approved or omit prototype evidence.
                    self.assertTrue(validate_task_package(dict(package, implementation_permission="approved")))
                    prototype = dict(package, work_item_kind="prototype", exit_gate="prototype-reviewed")
                    self.assertTrue(validate_task_package(prototype))
                    prototype["artifacts"] = ["prototype_evidence:evidence/prototype.json"]
                    self.assertEqual((), validate_task_package(prototype))
                    missing = copy.deepcopy(package)
                    missing.pop("evidence_required")
                    self.assertTrue(validate_task_package(missing))
                    self.assertTrue(validate_task_package(dict(package, structured_output_schema="retired-v1")))


if __name__ == "__main__":
    unittest.main()
