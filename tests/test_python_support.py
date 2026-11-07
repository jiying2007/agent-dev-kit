"""Build-control-plane interpreter policy; delivered Skills do not require ADK Python."""
from __future__ import annotations
import unittest
from agent_dev_kit.doctor import _python_environment_support


class PythonSupportTest(unittest.TestCase):
    def test_unsupported_interpreters_rejected(self) -> None:
        for version in ((3, 8, 20), (3, 10, 22), (3, 11, 14),
                        (3, 13, 0), (3, 14, 0), (4, 0, 0)):
            with self.subTest(version=version):
                report = _python_environment_support(version)
                self.assertFalse(report["python_supported"])
                self.assertFalse(report["python_ci_tested"])
                self.assertEqual(report["python_runtime_class"], "unsupported")

    def test_only_python312_is_supported_for_build_tools(self) -> None:
        for version in ((3, 12, 0), (3, 12, 12), (3, 12, 25)):
            with self.subTest(version=version):
                report = _python_environment_support(version)
                self.assertTrue(report["python_supported"])
                self.assertTrue(report["python_ci_tested"])
                self.assertEqual(report["python_minimum"], "3.12")
                self.assertEqual(report["python_ci_matrix"], ["3.12"])
                self.assertEqual(report["python_support_scope"], "build-control-plane-only")
                self.assertEqual(report["python_runtime_class"], "ci-validated")
                self.assertFalse(report["delivered_skill_requires_adk_python"])


if __name__ == "__main__":
    unittest.main()
