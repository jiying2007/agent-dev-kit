"""Commit message syntax and no implicit issue requirement."""
from __future__ import annotations
import json
import subprocess
import sys
import unittest
from agent_dev_kit.commit_message_policy import validate_message


class CommitMessagePolicyTests(unittest.TestCase):
    def test_zh_and_en(self) -> None:
        self.assertEqual(validate_message("fix(runtime): 修复边界条件")["status"], "pass")
        self.assertEqual(validate_message("docs: Update README")["status"], "pass")

    def test_issue_policy_is_opt_in(self) -> None:
        self.assertEqual(validate_message("fix: 修复连接错误")["status"], "pass")
        self.assertIn("issue-required-by-repository-policy",
                      validate_message("fix: 修复连接错误", require_issue=True)["issues"])
        self.assertEqual(validate_message("fix: 修复连接错误\n\nFixes #123", require_issue=True)["status"], "pass")

    def test_breaking_and_invalid(self) -> None:
        self.assertTrue(validate_message("feat(api)!: 统一接口")["breaking"])
        self.assertTrue(validate_message("feat: 统一接口\n\nBREAKING CHANGE: Removed v1")["breaking"])
        for msg in ("", "misc: 未知类型", "fix(scope) 缺少冒号", "fix: 修复问题。"):
            with self.subTest(msg=msg):
                self.assertEqual(validate_message(msg)["status"], "needs-fix")

    def test_cli_is_read_only_and_returns_verdict(self) -> None:
        for message, expected in (("test: 新增回归", 0), ("invalid", 2)):
            result = subprocess.run(
                [sys.executable, "-m", "agent_dev_kit.commit_message_policy", "--message", message],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"],
                             "pass" if expected == 0 else "needs-fix")
