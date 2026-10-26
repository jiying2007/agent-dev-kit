from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.planning_state import check_current_state


class PlanningStateTest(unittest.TestCase):
    def test_current_state_is_bounded_without_granting_completion(self) -> None:
        value = {"schema_version": "adk.current-state/v1", "goal_ref": "requirements.md",
                 "milestone": "owner lifecycle", "evidence_refs": ["tests-receipt.json"],
                 "blockers": [], "next_actions": ["verify shutdown"], "history_refs": ["history.md"]}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "current.json"
            path.write_text(json.dumps(value))
            before = path.read_bytes()
            result = check_current_state(path)
            self.assertEqual("pass", result["status"])
            self.assertFalse(result["completion_allowed"])
            self.assertFalse(result["evidence_contents_verified"])
            self.assertEqual(before, path.read_bytes())
            self.assertIn("current-state-byte-limit", check_current_state(path, max_bytes=10)["reasons"])
            value["next_actions"] *= 4
            path.write_text(json.dumps(value))
            self.assertIn("current-state-next-actions-limit", check_current_state(path)["reasons"])

    def test_malformed_and_duplicated_history_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "current.json"
            for raw in (b"[]", b"invalid", b"\xff"):
                path.write_bytes(raw)
                self.assertEqual("fail", check_current_state(path)["status"])
            path.write_text(json.dumps({"schema_version": "adk.current-state/v1", "historical_body": "full copied history"}))
            self.assertIn("current-state-fields-invalid", check_current_state(path)["reasons"])


    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX input boundary")
    def test_state_input_rejects_fifo_and_leaf_symlink_without_hanging(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "original.json"
            source.write_text('{"schema_version":"adk.current-state/v1"}')
            alias = root / "alias.json"
            alias.symlink_to(source)
            fifo = root / "blocked.fifo"
            os.mkfifo(fifo)
            for unsafe in (alias, fifo, root):
                with self.subTest(unsafe=unsafe.name):
                    result = check_current_state(unsafe)
                    self.assertEqual("fail", result["status"])
                    self.assertIn("current-state-input-invalid", result["reasons"])
                    self.assertFalse(result["completion_allowed"])
                    self.assertIsNone(result["state_sha256"])

    def test_duplicate_keys_nonfinite_values_and_excessive_depth_fail_closed(self) -> None:
        valid = {"schema_version": "adk.current-state/v1", "goal_ref": "requirements.md",
                 "milestone": "owner lifecycle", "evidence_refs": ["tests-receipt.json"],
                 "blockers": [], "next_actions": ["verify shutdown"], "history_refs": ["history.md"]}
        original = json.dumps(valid)
        invalid_cases = (
            original.replace('"goal_ref": "requirements.md"',
                             '"goal_ref": "requirements.md", "goal_ref": "forged.md"'),
            original.replace('"milestone": "owner lifecycle"', '"milestone": NaN'),
            original.replace('"milestone": "owner lifecycle"', '"milestone": 1e10000'),
            original.replace('"milestone": "owner lifecycle"',
                             '"milestone": ' + "[" * 65 + '"owner lifecycle"' + "]" * 65),
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "current.json"
            for raw in invalid_cases:
                with self.subTest(raw=raw[:80]):
                    path.write_text(raw)
                    result = check_current_state(path)
                    self.assertEqual("fail", result["status"])
                    self.assertIn("current-state-schema-invalid", result["reasons"])
                    self.assertFalse(result["completion_allowed"])
