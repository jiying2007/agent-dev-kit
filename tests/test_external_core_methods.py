"""Execute the exported reference examples; no model or provider evaluation."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import load_target_contract, render_asset

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = {
    "adk-task-breakdown": "references/vertical-slice-planning.md",
    "adk-test-strategy": "references/high-value-tdd.md",
    "adk-verification-before-completion": "references/verification-governance-details.md",
}


def example(text: str, identity: str, language: str = "python") -> str:
    matches = re.findall(
        rf"<!-- adk-example: {re.escape(identity)} -->\n```{language}\n(.*?)\n```",
        text, re.DOTALL,
    )
    if len(matches) != 1:
        raise AssertionError(f"Expected one public example: {identity}")
    return matches[0] + "\n"


class ExternalCoreMethodsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        manifest = Manifest.load(ROOT)
        contract = load_target_contract(manifest, "claude-code")
        cls.exported = {}
        for asset in manifest.all_assets("skill"):
            if asset.name not in REFERENCES:
                continue
            files = render_asset(manifest, contract, asset)
            main = next(item for item in files if item.destination.endswith("/SKILL.md"))
            reference_path = (Path(main.destination).parent / REFERENCES[asset.name]).as_posix()
            reference = next(item for item in files if item.destination == reference_path)
            cls.exported[asset.name] = (main.content.decode(), reference.content.decode())

    def run_program(self, code: str, *arguments: str, files: dict[str, str] | None = None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = root / "example.py"
            program.write_text(code, encoding="utf-8")
            for name, content in (files or {}).items():
                (root / name).write_text(content, encoding="utf-8")
            return subprocess.run(
                [sys.executable, "-B", str(program), *arguments], cwd=root,
                capture_output=True, text=True, timeout=10,
            )

    def rows(self, run):
        return [json.loads(line) for line in run.stdout.splitlines()]

    def test_methods_and_examples_survive_native_frontmatter_rebuild(self):
        self.assertEqual(set(self.exported), set(REFERENCES))
        for name, (main, reference) in self.exported.items():
            with self.subTest(skill=name):
                _, metadata, body = main.split("---", 2)
                self.assertNotIn("constraints:", metadata)
                self.assertIn(REFERENCES[name], body)
                self.assertIn("<!-- adk-example:", reference)

    def test_new_discovery_uses_production_matcher_without_granting_writes(self):
        for phrase, owner in (
            ("公共契约迁移拆分", "adk-task-breakdown"),
            ("独立断言", "adk-test-strategy"),
            ("检查器校准", "adk-test-strategy"),
        ):
            for negated in (False, True):
                with self.subTest(phrase=phrase, negated=negated):
                    prompt = ("不要" if negated else "请规划") + phrase
                    run = subprocess.run(
                        ["bash", str(ROOT / "scripts/devkit.sh"), "match", "--text", prompt],
                        cwd=ROOT, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(run.returncode, 1 if negated else 0, run.stdout + run.stderr)
                    self.assertIn("mutation_permission=deny", run.stdout)
                    if negated:
                        self.assertIn("match=false", run.stdout)
                        self.assertIn("decision=abstain", run.stdout)
                    else:
                        self.assertIn("skill=" + owner + " ", run.stdout)
                        self.assertIn("effect_ceiling=read-only", run.stdout)

    def test_migration_runs_both_real_consumers_at_each_safe_stage(self):
        code = example(self.exported["adk-task-breakdown"][1], "contract-migration")
        run = self.run_program(code, "safe")
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
        rows = self.rows(run)
        self.assertEqual([row["stage"] for row in rows],
                         ["before", "expand", "migrate-a", "migrate-b", "contract"])
        for row in rows:
            self.assertEqual(len(row["consumers"]), 2)
            for consumer in row["consumers"]:
                self.assertEqual(consumer, {"exit": 0, "value": "Ada", "error": ""})

    def test_direct_and_early_contract_fail_actual_old_consumers(self):
        code = example(self.exported["adk-task-breakdown"][1], "contract-migration")
        for route, failed_consumers in (("direct", [0, 1]), ("early", [1])):
            with self.subTest(route=route):
                run = self.run_program(code, route)
                self.assertEqual(run.returncode, 1, run.stderr + run.stdout)
                rows = self.rows(run)
                for row in rows[:-1]:
                    self.assertTrue(all(consumer["exit"] == 0 for consumer in row["consumers"]))
                consumers = rows[-1]["consumers"]
                self.assertEqual([i for i, consumer in enumerate(consumers) if consumer["exit"]],
                                 failed_consumers)
                for index in failed_consumers:
                    self.assertIn("KeyError: 'name'", consumers[index]["error"])

    def test_independent_oracle_rejects_bug_mirrored_helper_misses(self):
        code = example(self.exported["adk-test-strategy"][1], "independent-oracle")
        mirrored = self.run_program(code, "mirror", "broken")
        self.assertEqual(mirrored.returncode, 0, mirrored.stderr)
        self.assertTrue(all(row["pass"] for row in self.rows(mirrored)))
        independent = self.run_program(code, "independent", "broken")
        self.assertEqual(independent.returncode, 1, independent.stderr)
        rows = self.rows(independent)
        self.assertEqual([row["input"] for row in rows if not row["pass"]], ["a&b c"])
        self.assertEqual(rows[-1]["expected"], "tag=a%26b%20c")
        self.assertEqual(rows[-1]["actual"], "tag=a&b%20c")
        good = self.run_program(code, "independent", "good")
        self.assertEqual(good.returncode, 0, good.stderr + good.stdout)
        self.assertEqual([row["input"] for row in self.rows(good)], ["", "plain", "a&b c"])
        self.assertTrue(all(row["pass"] for row in self.rows(good)))

    def checker(self, report: str, *, threshold: str = "error", scanner_exit: int = 0):
        reference = self.exported["adk-verification-before-completion"][1]
        return self.run_program(
            example(reference, "checker-calibration"), threshold,
            sys.executable, "scanner.py", "report.json", str(scanner_exit),
            files={"scanner.py": example(reference, "checker-scanner"), "report.json": report},
        )

    def clean_report(self):
        reference = self.exported["adk-verification-before-completion"][1]
        return json.loads(example(reference, "checker-clean-report", "json"))

    def test_checker_preserves_clean_and_threshold_permitted_results(self):
        clean = self.clean_report()
        for report in (clean, dict(clean, findings=["warning"])):
            with self.subTest(findings=report["findings"]):
                run = self.checker(json.dumps(report))
                self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
                self.assertEqual(self.rows(run), [{"scanner_exit": 0, "verdict": 0}])
        stricter = self.checker(json.dumps(dict(clean, findings=["warning"])), threshold="warning")
        self.assertEqual(stricter.returncode, 1, stricter.stderr + stricter.stdout)
        self.assertEqual(self.checker(json.dumps(clean), threshold="warning").returncode, 0)

    def test_checker_rejects_violation_even_when_scanner_exits_zero(self):
        report = json.dumps(dict(self.clean_report(), findings=["error"]))
        reference = self.exported["adk-verification-before-completion"][1]
        naive = self.run_program(example(reference, "checker-scanner"), "report.json", "0",
                                 files={"report.json": report})
        self.assertEqual(naive.returncode, 0)
        self.assertEqual(json.loads(naive.stdout)["findings"], ["error"])
        checked = self.checker(report)
        self.assertEqual(checked.returncode, 1, checked.stderr + checked.stdout)
        self.assertEqual(self.rows(checked), [{"scanner_exit": 0, "verdict": 1}])

    def test_checker_does_not_turn_invalid_or_incomplete_reports_into_pass(self):
        clean = self.clean_report()
        cases = {
            "tool-error": dict(clean, errors=["scanner unavailable"]),
            "incomplete": dict(clean, complete=False),
            "empty-coverage": dict(clean, scanned=[]),
            "partial-coverage": dict(clean, scanned=["a.py"]),
            "unknown-level": dict(clean, findings=["unknown"]),
            "invalid-level-type": dict(clean, findings=[None]),
            "invalid-schema-type": dict(clean, schema=True),
            "invalid-scope-type": dict(clean, scanned=[{}]),
            "missing-field": {key: value for key, value in clean.items() if key != "findings"},
        }
        for name, report in cases.items():
            with self.subTest(case=name):
                run = self.checker(json.dumps(report))
                self.assertEqual(run.returncode, 2, run.stderr + run.stdout)
                self.assertEqual(self.rows(run), [{"scanner_exit": 0, "verdict": 2}])
        malformed = self.checker("{")
        self.assertEqual(malformed.returncode, 2)
        failed_process = self.checker(json.dumps(clean), scanner_exit=3)
        self.assertEqual(failed_process.returncode, 2)
        self.assertEqual(self.rows(failed_process), [{"scanner_exit": 3, "verdict": 2}])
        self.assertEqual(self.checker(json.dumps(clean), threshold="unknown").returncode, 2)


if __name__ == "__main__":
    unittest.main()
