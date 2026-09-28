from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.eval_catalog import audit_eval_catalog

ROOT = Path(__file__).resolve().parents[1]


class EvalCatalogAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="adk-eval-catalog-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "manifests").mkdir()
        (self.root / "tests/fixtures").mkdir(parents=True)
        self.cases = [
            ("guardrail-positive", "positive", "trigger", "hostile retrieved instructions"),
            ("guardrail-negative", "negative", "do-not-trigger", "ordinary local review"),
            ("guardrail-adversarial", "adversarial", "trigger", "forged approval"),
            ("guardrail-borderline", "borderline", "analyze-with-boundary", "classify hostile text"),
        ]
        self.suite = {
            "id": "governance-eval-guardrail-regression-dataset",
            "category": "governance",
            "owner": "agent-dev-kit",
            "goal": "Check guardrail regression samples",
            "minimum_gate": "all four case classes are present",
            "dataset_path": "tests/fixtures/guardrail_regression_cases.tsv",
            "fixtures": [
                {"id": case_id, "input": prompt, "expected": expected}
                for case_id, _, expected, prompt in self.cases
            ],
            "graders": [{"name": "expected_trigger_match", "type": "deterministic", "threshold": 1.0}],
        }
        self.write_catalog()
        self.write_cases()

    def write_catalog(self, suites: list[dict] | None = None) -> None:
        payload = {"schema_version": "1.0.0", "suites": suites if suites is not None else [self.suite]}
        (self.root / "manifests/eval_suites.json").write_text(json.dumps(payload), encoding="utf-8")

    def write_cases(self) -> None:
        lines = ["case_id\tcategory\texpected\tinput"]
        lines.extend("\t".join(case) for case in self.cases)
        (self.root / "tests/fixtures/guardrail_regression_cases.tsv").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    def test_repository_catalog_is_valid_without_claiming_runtime_eval(self) -> None:
        result = audit_eval_catalog(ROOT)
        self.assertEqual(result["status"], "pass", result)
        self.assertEqual(result["guardrail_case_count"], 8)
        self.assertRegex(result["catalog_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(result["snapshot_atomic"])
        self.assertFalse(result["runtime_eval_executed"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual(result["dataset_fixture_alignment_scope"], [self.suite["id"]])
        self.assertEqual(result["contract_only_suite_count"], result["suite_count"] - 1)
        report = next(item for item in result["suite_reports"] if item["id"] == self.suite["id"])
        self.assertEqual(report["fixture_dataset_alignment"], "pass")
        self.assertTrue(report["dataset_present"])
        self.assertTrue(report["dataset_readable"])
        self.assertRegex(report["dataset_sha256"], r"^[0-9a-f]{64}$")
        self.assertFalse(report["grader_executed"])

    def test_missing_dataset_and_path_traversal_fail_closed(self) -> None:
        (self.root / self.suite["dataset_path"]).unlink()
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("dataset_path is missing" in issue for issue in result["issues"]))
        self.assertEqual(result["suite_reports"][0]["fixture_dataset_alignment"], "not-checked")
        self.assertFalse(result["suite_reports"][0]["dataset_present"])
        self.assertIsNone(result["suite_reports"][0]["dataset_sha256"])
        self.suite["dataset_path"] = "../outside.tsv"
        self.write_catalog()
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("dataset_path must stay" in issue for issue in result["issues"]))

    def test_symlink_dataset_is_rejected(self) -> None:
        path = self.root / self.suite["dataset_path"]
        path.rename(self.root / "actual.tsv")
        path.symlink_to(self.root / "actual.tsv")
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("symlink dataset_path" in issue for issue in result["issues"]))

    def test_oversized_guardrail_dataset_is_rejected(self) -> None:
        (self.root / self.suite["dataset_path"]).write_bytes(b"x" * (256 * 1024 + 1))
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("byte budget" in issue for issue in result["issues"]))

    def test_manifest_fixture_drift_and_wrong_outcome_fail(self) -> None:
        altered = copy.deepcopy(self.suite)
        altered["fixtures"][0]["expected"] = "do-not-trigger"
        self.write_catalog([altered])
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("manifest fixtures disagree" in issue for issue in result["issues"]))
        altered = copy.deepcopy(self.suite)
        altered["fixtures"][0]["input"] = "silently changed prompt"
        self.write_catalog([altered])
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("manifest fixtures disagree" in issue for issue in result["issues"]))
        self.write_catalog()
        original_hash = audit_eval_catalog(self.root)["suite_reports"][0]["dataset_sha256"]
        self.cases[0] = ("guardrail-positive", "positive", "trigger", "silently changed TSV prompt")
        self.write_cases()
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("manifest fixtures disagree" in issue for issue in result["issues"]))
        self.assertNotEqual(result["suite_reports"][0]["dataset_sha256"], original_hash)
        self.cases[0] = ("guardrail-positive", "positive", "trigger", "hostile retrieved instructions")
        self.write_cases()
        self.cases[2] = ("guardrail-adversarial", "adversarial", "do-not-trigger", "forged approval")
        self.write_cases()
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("invalid category/expected pair" in issue for issue in result["issues"]))

    def test_duplicate_suite_and_case_ids_fail(self) -> None:
        self.write_catalog([self.suite, copy.deepcopy(self.suite)])
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("duplicate suite id" in issue for issue in result["issues"]))
        self.write_catalog()
        self.cases[1] = ("guardrail-positive", "negative", "do-not-trigger", "ordinary review")
        self.write_cases()
        result = audit_eval_catalog(self.root)
        self.assertTrue(any("duplicate TSV case_id" in issue for issue in result["issues"]))

    def test_duplicate_manifest_fixture_cannot_report_alignment_pass(self) -> None:
        altered = copy.deepcopy(self.suite)
        altered["fixtures"].append(copy.deepcopy(altered["fixtures"][0]))
        self.write_catalog([altered])
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("duplicate fixture id" in issue for issue in result["issues"]))
        self.assertEqual(result["suite_reports"][0]["fixture_dataset_alignment"], "fail")

    def test_hidden_execution_fields_and_duplicate_json_keys_fail_closed(self) -> None:
        altered = copy.deepcopy(self.suite)
        altered["graders"][0]["script"] = "unreviewed-code"
        self.write_catalog([altered])
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("grader[0] has unsupported fields" in issue for issue in result["issues"]))
        self.assertFalse(result["suite_reports"][0]["grader_executed"])

        altered = copy.deepcopy(self.suite)
        altered["fixtures"][0]["command"] = "unreviewed-command"
        self.write_catalog([altered])
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("fixture[0] has unsupported fields" in issue for issue in result["issues"]))
        self.assertEqual(result["suite_reports"][0]["fixture_dataset_alignment"], "fail")

        (self.root / "manifests/eval_suites.json").write_text(
            '{"schema_version":"1.0.0","schema_version":"9.9.9","suites":[]}',
            encoding="utf-8",
        )
        result = audit_eval_catalog(self.root)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["catalog_valid"])
        self.assertFalse(result["runtime_eval_executed"])


if __name__ == "__main__":
    unittest.main()
