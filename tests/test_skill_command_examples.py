"""Execute the published Skill examples against isolated, observable failures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "skills/adk-release-versioning/references/details.md"
FLAKY = "optional-skills/adk-test-flakiness-triage/references/details.md"


def bash_example(path: str, marker: str) -> str:
    blocks = re.findall(r"```bash\n(.*?)```", (ROOT / path).read_text(), re.S)
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"expected one executable example for {marker}: {path}")
    return matches[0]


def run_example(code: str, root: Path, *arguments: str, environment=None):
    return subprocess.run(["bash", "-c", code, "skill-example", *arguments], cwd=root,
                          env=environment, capture_output=True, text=True, timeout=15)


class ReleaseHistoryExampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "source repository"
        self.repo.mkdir()
        self.environment = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                                GIT_AUTHOR_NAME="Skill fixture", GIT_COMMITTER_NAME="Skill fixture",
                                GIT_AUTHOR_EMAIL="fixture@example.invalid",
                                GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.git("init", "-q")
        self.code = bash_example(RELEASE, "release_history()") + '\nrelease_history "$@"\n'

    def git(self, *arguments):
        result = subprocess.run(["git", *arguments], cwd=self.repo, env=self.environment,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout.strip()

    def commit(self, subject, body=""):
        self.git("commit", "--allow-empty", "-q", "-m", subject, "-m", body)
        return self.git("rev-parse", "HEAD")

    def history(self, *arguments, root=None):
        return run_example(self.code, root or self.repo, *arguments, environment=self.environment)

    def test_initial_release_preserves_all_commits_without_tags(self):
        first = self.commit("first implementation", "Details without a conventional prefix")
        second = self.commit("fix: initial error", "Second paragraph\n\nMore evidence")
        result = self.history("initial")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=INITIAL", result.stdout)
        for value in (first, second, "first implementation", "Details without a conventional prefix",
                      "fix: initial error", "Second paragraph\n\nMore evidence"):
            self.assertIn(value, result.stdout)
        self.assertLess(result.stdout.index("commit " + first), result.stdout.index("commit " + second))

    def test_verified_release_range_keeps_breaking_revert_and_unknown_types(self):
        baseline = self.commit("published baseline")
        self.git("tag", "v1.0.0")
        changes = [
            ("feat: export data", "Export behavior"),
            ("build!: require toolchain 18", "BREAKING CHANGE: old build format is rejected"),
            ("revert: remove export", "Reverts the export behavior"),
            ("security patch for parser", "No conventional type; still needs review"),
        ]
        commits = []
        for index, (subject, body) in enumerate(changes):
            commits.append(self.commit(subject, body))
            if index == 2:
                self.git("tag", "scratch-checkpoint")
        result = self.history("since-release", "v1.0.0")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=" + baseline, result.stdout)
        self.assertNotIn("commit " + baseline, result.stdout)
        for identity, (subject, body) in zip(commits, changes):
            self.assertIn("commit " + identity, result.stdout)
            self.assertIn(subject, result.stdout)
            self.assertIn(body, result.stdout)
        self.assertEqual(commits[-1], self.git("rev-parse", "HEAD"))

    def test_invalid_or_unrelated_baseline_fails_without_initial_fallback(self):
        self.commit("baseline")
        unrelated = self.git("commit-tree", self.git("rev-parse", "HEAD^{tree}"), "-m", "unrelated root")
        for baseline in ("missing-release", "--all", unrelated):
            with self.subTest(baseline=baseline):
                result = self.history("since-release", baseline)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertTrue(result.stderr)

    def test_shallow_history_is_rejected_even_for_explicit_initial_mode(self):
        self.commit("first")
        self.commit("second")
        clone = self.root / "shallow"
        self.git("clone", "-q", "--depth=1", self.repo.as_uri(), str(clone))
        result = self.history("initial", root=clone)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("shallow", result.stderr)
        self.assertEqual("", result.stdout)

    def test_empty_verified_range_is_distinct_from_git_or_usage_failure(self):
        identity = self.commit("release")
        result = self.history("since-release", identity)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("base=" + identity, result.stdout)
        self.assertIn("target=" + identity, result.stdout)
        self.assertNotIn("commit ", result.stdout)
        for arguments, root in (((), self.repo), (("initial", "extra"), self.repo),
                                (("initial",), self.root)):
            with self.subTest(arguments=arguments, root=root.name):
                failed = self.history(*arguments, root=root)
                self.assertNotEqual(0, failed.returncode)
                self.assertEqual("", failed.stdout)


class FlakySampleExampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.code = bash_example(FLAKY, "run_flaky_samples()") + '\nrun_flaky_samples "$@"\n'
        self.runner = self.root / "sample runner [fixture].py"
        self.runner.write_text(
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "sample = Path(os.environ['FLAKY_SAMPLE_DIR'])\n"
            "attempt = int(sample.name.removeprefix('run-'))\n"
            "code = int(sys.argv[1].split(',')[attempt - 1])\n"
            "outcome = 'passed' if code == 0 else 'failed' if code == 1 else 'error'\n"
            "(sample / 'result.json').write_text(json.dumps({'name': sys.argv[2], 'outcome': outcome}))\n"
            "print('PASSED noisy_log_name\\nPASSED noisy_log_name')\n"
            "print(outcome, sys.argv[2], flush=True)\n"
            "print('stderr retained', file=sys.stderr)\n"
            "sys.exit(code)\n"
        )

    def sample(self, codes, name="test_items[case 1]", directory="new evidence", code=None):
        output = self.root / directory
        command = [sys.executable, str(self.runner), ",".join(map(str, codes)), name]
        if code is not None:
            command = [sys.executable, "-c", code]
        result = run_example(self.code, self.root, str(len(codes)), str(output), *command)
        return result, output

    def test_success_failure_and_mixed_runs_keep_exact_exit_codes_and_reports(self):
        literal_name = "test_items[case 1]; $(touch MUST_NOT_RUN)"
        for codes in ([0, 0, 0], [9, 9, 9], [0, 1, 2, 0]):
            with self.subTest(codes=codes):
                result, output = self.sample(codes, literal_name, directory="runs-" + "-".join(map(str, codes)))
                self.assertEqual(int(any(codes)), result.returncode, result.stderr)
                rows = (output / "results.tsv").read_text().splitlines()
                self.assertEqual(["attempt\texit_code", *[f"{i}\t{code}" for i, code in enumerate(codes, 1)]], rows)
                for attempt, code in enumerate(codes, 1):
                    run = output / f"run-{attempt}"
                    report = json.loads((run / "result.json").read_text())
                    self.assertEqual(literal_name, report["name"])
                    self.assertEqual("passed" if code == 0 else "failed" if code == 1 else "error", report["outcome"])
                    log = (run / "output.log").read_text()
                    self.assertIn("stderr retained", log)
                    self.assertIn(literal_name, log)
                self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_existing_evidence_is_not_reused_or_overwritten(self):
        result, output = self.sample([0])
        self.assertEqual(0, result.returncode, result.stderr)
        before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
        result, _ = self.sample([1])
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual(before, {path.relative_to(output): path.read_bytes()
                                  for path in output.rglob("*") if path.is_file()})

    def test_sample_collection_failure_stops_without_fake_completed_attempt(self):
        command = ("import os; from pathlib import Path; "
                   "sample=Path(os.environ['FLAKY_SAMPLE_DIR']); "
                   "(sample.parent / 'run-2').write_text('blocked collection path'); "
                   "print('first real observation')")
        result, output = self.sample([0, 0, 0], code=command)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertEqual("attempt\texit_code\n1\t0\n", (output / "results.tsv").read_text())
        self.assertIn("first real observation", (output / "run-1/output.log").read_text())
        self.assertFalse((output / "run-3").exists())
        self.assertNotIn("attempts=3", result.stdout)

    def test_status_write_failure_is_not_a_successful_collection(self):
        command = ("import os; from pathlib import Path; "
                   "status=Path(os.environ['FLAKY_SAMPLE_DIR']).parent / 'results.tsv'; "
                   "status.unlink(); status.mkdir(); print('test command returned zero')")
        result, output = self.sample([0], code=command)
        self.assertEqual(2, result.returncode, result.stderr)
        self.assertIn("returned zero", (output / "run-1/output.log").read_text())

    def test_invalid_sample_budgets_do_not_execute_or_create_output(self):
        for budget in ("0", "21", "-1", "99999", "$(touch MUST_NOT_RUN)"):
            with self.subTest(budget=budget):
                output = self.root / "not-created"
                result = run_example(self.code, self.root, budget, str(output), "false")
                self.assertEqual(2, result.returncode)
                self.assertFalse(output.exists())
        self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_environment_example_only_prints_names_not_synthetic_secret_values(self):
        environment = {"PATH": os.environ["PATH"], "CI_JOB_TOKEN": "synthetic-private-value",
                       "TEST_PASSWORD": "another-private-value", "UNRELATED": "debug-value"}
        code = bash_example(FLAKY, "# environment-names:")
        result = run_example(code, self.root, environment=environment)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["CI_JOB_TOKEN", "TEST_PASSWORD"], json.loads(result.stdout))
        for value in environment.values():
            self.assertNotIn(value, result.stdout)


if __name__ == "__main__":
    unittest.main()
