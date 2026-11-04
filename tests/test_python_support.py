"""Build-control-plane interpreter policy; deployed Skills need no ADK Python."""

from __future__ import annotations

import unittest

from agent_dev_kit.doctor import _python_environment_support


class PythonSupportTest(unittest.TestCase):
    def test_pre_311_interpreters_are_not_supported(self) -> None:
        for version in ((3, 7, 17), (3, 8, 20), (3, 9, 25), (3, 10, 22)):
            with self.subTest(version=version):
                report = _python_environment_support(version)
                self.assertFalse(report["python_supported"])
                self.assertFalse(report["python_ci_tested"])
                self.assertEqual(report["python_runtime_class"], "unsupported")

    def test_supported_versions_are_build_only(self) -> None:
        for version in ((3, 11, 14), (3, 12, 12)):
            with self.subTest(version=version):
                report = _python_environment_support(version)
                self.assertTrue(report["python_supported"])
                self.assertTrue(report["python_ci_tested"])
                self.assertEqual(report["python_minimum"], "3.11")
                self.assertEqual(report["python_ci_matrix"], ["3.11", "3.12"])
                self.assertEqual(report["python_support_scope"], "build-control-plane-only")
                self.assertEqual(report["python_runtime_class"], "ci-validated")
                self.assertFalse(report["delivered_skill_requires_adk_python"])

    def test_new_interpreter_is_not_automatically_qualified(self) -> None:
        for version in ((3, 13, 0), (3, 14, 0), (3, 15, 0), (4, 0, 0)):
            report = _python_environment_support(version)
            self.assertTrue(report["python_supported"])
            self.assertFalse(report["python_ci_tested"])
            self.assertEqual(report["python_runtime_class"], "unvalidated")
            self.assertFalse(report["delivered_skill_requires_adk_python"])


if __name__ == "__main__":
    unittest.main()
