"""Exercise the published diagnostic oracle against real isolated Git histories."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import load_target_contract, render_asset


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS: list[dict[str, object]] = []


class DiagnosticBisectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.git_binary = shutil.which("git")
        cls.bash_binary = shutil.which("bash")
        if cls.git_binary is None or cls.bash_binary is None:
            raise AssertionError("Git and Bash are required for diagnostic method tests")
        manifest = Manifest.load(ROOT)
        asset = next(item for item in manifest.all_assets("skill")
                     if item.name == "adk-systematic-debugging")
        rendered = render_asset(manifest, load_target_contract(manifest, "claude-code"), asset)
        reference = next(item for item in rendered if item.destination.endswith(
            "/references/tight-feedback-loop.md"))
        cls.reference_sha256 = hashlib.sha256(reference.content).hexdigest()
        text = reference.content.decode("utf-8")
        block = re.search(r"<!-- adk-example: bisect-probe -->\s*```bash\n(.*?)\n```",
                          text, re.DOTALL)
        if block is None:
            raise AssertionError("Published diagnostic oracle is missing")
        cls.recipe = block.group(1)

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="adk-bisect-method-")
        self.addCleanup(temporary.cleanup)
        self.area = Path(temporary.name)
        self.repo = self.area / "consumer"
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update({"LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
                         "GIT_CONFIG_GLOBAL": os.devnull,
                         "PYTHONDONTWRITEBYTECODE": "1"})
        self.wrapper = self.area / "published-oracle.sh"
        self.wrapper.write_text(self.recipe + "\n", encoding="utf-8")
        self.probe = self.area / "project-probe.py"
        self.probe.write_text(
            'import json, sys\nfrom pathlib import Path\n'
            's = json.loads(Path("state.json").read_text())\n'
            'if s.get("infrastructure_error"):\n'
            '    print("runner cannot inspect the target", file=sys.stderr)\n'
            '    raise SystemExit(2)\n'
            'if not s["buildable"]:\n'
            '    print("bad" if sys.argv[1] == "build" else "untestable")\n'
            'else:\n'
            '    print("bad" if sys.argv[1] == "semantic" and s["bug"] else "good")\n',
            encoding="utf-8",
        )
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "ADK diagnostic fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.hooksPath", os.devnull)

    def run_command(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(argv, cwd=self.repo, env=self.env,
                                capture_output=True, text=True, timeout=10)
        RECEIPTS.append({"test": self.id(), "argv": argv, "exit": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr,
                         "reference_sha256": self.reference_sha256})
        return result

    def git(self, *args: str) -> str:
        result = self.run_command([self.git_binary, "-c", "core.fsmonitor=false", *args])
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result.stdout

    def history(self, states: list[dict[str, object]]) -> list[str]:
        commits = []
        for index, state in enumerate(states):
            (self.repo / "state.json").write_text(json.dumps({**state, "step": index}) + "\n",
                                                   encoding="utf-8")
            self.git("add", "state.json")
            self.git("commit", "-qm", f"controlled state {index}")
            commits.append(self.git("rev-parse", "HEAD").strip())
        return commits

    def oracle(self, target: str = "semantic") -> list[str]:
        return [self.bash_binary, "--noprofile", "--norc", str(self.wrapper),
                sys.executable, "-B", str(self.probe), target]

    def bisect(self, commits: list[str], target: str = "semantic") -> tuple[subprocess.CompletedProcess[str], str]:
        # Calibrate the actual oracle on both known endpoints before searching.
        for commit, expected in ((commits[0], 0), (commits[-1], 1)):
            self.git("checkout", "--detach", "-q", commit)
            result = self.run_command(self.oracle(target))
            self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        self.git("bisect", "start", commits[-1], commits[0])
        result = self.run_command([self.git_binary, "bisect", "run", *self.oracle(target)])
        log = self.git("bisect", "log")
        self.git("bisect", "reset")
        return result, log

    def unique_first_bad(self, result: subprocess.CompletedProcess[str], log: str) -> str:
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        candidates = re.findall(r"^# first bad commit: \[([0-9a-f]{40})\]", log, re.MULTILINE)
        self.assertEqual(1, len(candidates), log)
        return candidates[0]

    def test_published_oracle_preserves_outcomes_and_aborts_unknown_results(self) -> None:
        prefix = [self.bash_binary, "--noprofile", "--norc", str(self.wrapper)]
        for output, process_exit, expected in (
            ("good", 0, 0), ("bad", 0, 1), ("untestable", 0, 125),
            ("unknown", 0, 128), ("", 0, 128), ("good\nbad", 0, 128),
            ("good", 2, 128), ("bad", 126, 128), ("bad", 127, 128),
        ):
            with self.subTest(output=output, process_exit=process_exit):
                command = [*prefix, sys.executable, "-c",
                           f"import sys; print({output!r}); raise SystemExit({process_exit})"]
                result = self.run_command(command)
                self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
        missing = self.run_command([*prefix, str(self.area / "missing-probe")])
        self.assertEqual(128, missing.returncode, missing.stderr)

    def test_real_bisect_skips_unrelated_unbuildable_revision(self) -> None:
        good = {"buildable": True, "bug": False}
        bad = {"buildable": True, "bug": True}
        commits = self.history([good, good, {"buildable": False, "bug": False},
                                good, bad, bad])
        result, log = self.bisect(commits)
        self.assertEqual(commits[4], self.unique_first_bad(result, log))
        self.assertIn("git bisect skip " + commits[2], log)

    def test_real_bisect_treats_build_failure_as_bad_for_build_regression(self) -> None:
        good = {"buildable": True, "bug": False}
        bad = {"buildable": False, "bug": False}
        commits = self.history([good, good, bad, bad, bad, bad])
        result, log = self.bisect(commits, "build")
        self.assertEqual(commits[2], self.unique_first_bad(result, log))
        self.assertNotIn("git bisect skip ", log)

    def test_real_bisect_aborts_instead_of_blames_infrastructure_error(self) -> None:
        good = {"buildable": True, "bug": False}
        bad = {"buildable": True, "bug": True}
        commits = self.history([good, good, {**good, "infrastructure_error": True},
                                good, bad, bad])
        result, log = self.bisect(commits)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("exit code 128", result.stdout + result.stderr)
        self.assertNotIn("# first bad commit:", log)
        self.assertNotIn("git bisect bad " + commits[2], log)
        self.assertNotIn("git bisect skip " + commits[2], log)

    def test_real_bisect_preserves_ambiguity_next_to_skipped_boundary(self) -> None:
        good = {"buildable": True, "bug": False}
        bad = {"buildable": True, "bug": True}
        commits = self.history([good, good, {"buildable": False, "bug": False},
                                bad, bad, bad])
        result, log = self.bisect(commits)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("first bad commit could be any of", result.stdout)
        self.assertIn(commits[2], result.stdout)
        self.assertIn(commits[3], result.stdout)
        self.assertNotIn("# first bad commit:", log)


if __name__ == "__main__":
    unittest.main()
