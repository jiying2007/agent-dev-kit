"""Interpreter policy classification without invoking any runtime CLI."""
from __future__ import annotations

import unittest

from agent_dev_kit.doctor import _python_environment_support


class PythonSupportTest(unittest.TestCase):
    def test_below_minimum_is_not_compatible(self):
        report = _python_environment_support((3, 7, 17))
        self.assertFalse(report["python_supported"])
        self.assertFalse(report["python_ci_tested"])
        self.assertEqual(report["python_runtime_class"], "unsupported")

    def test_legacy_compatibility_does_not_claim_upstream_maintenance(self):
        for version, eol, tested in (
            ((3, 8, 20), "2024-10-07", True),
            ((3, 9, 25), "2025-10-31", False),
            ((3, 10, 22), "2026-10-01", False),
        ):
            with self.subTest(version=version):
                report = _python_environment_support(version)
                self.assertTrue(report["python_supported"])
                self.assertEqual(report["python_ci_tested"], tested)
                self.assertEqual(report["python_runtime_class"], "legacy-compatibility")
                self.assertEqual(report["python_upstream_status"], "end-of-life")
                self.assertEqual(report["python_upstream_eol_date"], eol)

    def test_tested_versions_do_not_imply_continuous_upstream_verification(self):
        for version in ((3, 11, 14), (3, 12, 12)):
            report = _python_environment_support(version)
            self.assertEqual(report["python_runtime_class"], "ci-validated")
            self.assertTrue(report["python_ci_tested"])
            self.assertEqual(report["python_support_scope"], "package-compatibility-only")
            self.assertEqual(report["python_upstream_status"], "not-assessed")

    def test_new_interpreter_is_not_automatically_ci_validated(self):
        for version in ((3, 13, 0), (3, 14, 0), (3, 15, 0), (4, 0, 0)):
            report = _python_environment_support(version)
            self.assertTrue(report["python_supported"])
            self.assertFalse(report["python_ci_tested"])
            self.assertEqual(report["python_runtime_class"], "unvalidated")
            self.assertIsNone(report["python_upstream_eol_date"])


if __name__ == "__main__":
    unittest.main()
