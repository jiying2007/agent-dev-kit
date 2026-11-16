"""Execute the published Skill examples against isolated, observable failures."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RELEASE = "skills/adk-release-versioning/references/details.md"
FLAKY = "optional-skills/adk-test-flakiness-triage/references/details.md"
SECURITY = "optional-skills/adk-security-supply-chain/SKILL.md"
SUPPLY_RUNBOOK = "docs/runbooks/security-supply-chain.md"
BSP = "skills/adk-bsp-porting-playbook/SKILL.md"
INTERFACE = "skills/adk-interface-contract-design/references/details.md"
ADC = ROOT / "examples/embedded-test-matrix"
CMAKE = "skills/adk-cmake-cross-build/SKILL.md"
HIL = "skills/adk-integration-hil-sil/SKILL.md"


def bash_example(path: str, marker: str) -> str:
    blocks = re.findall(r"```bash\n(.*?)```", (ROOT / path).read_text(), re.S)
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"expected one executable example for {marker}: {path}")
    return matches[0]


def run_example(code: str, root: Path, *arguments: str, environment=None,
                timeout=15, label="skill-example"):
    """Bound the whole example; keep diagnostics and terminate its own process group."""
    command = ["bash", "-c", code, "skill-example", *arguments]
    started = time.monotonic()
    process = subprocess.Popen(command, cwd=root, env=environment, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as expired:
        work_elapsed = time.monotonic() - started
        cleanup_started = time.monotonic()
        cleanup_deadline = cleanup_started + 1
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        cleanup_status = "complete"
        try:
            stdout, stderr = process.communicate(timeout=max(0, cleanup_deadline - time.monotonic()))
        except subprocess.TimeoutExpired as draining:
            # A descendant outside this owned group could retain a pipe. Do not
            # let cleanup extend the work budget or wait without a limit.
            stdout, stderr = draining.stdout or expired.stdout, draining.stderr or expired.stderr
            process.stdout.close()
            process.stderr.close()
            try:
                process.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                cleanup_status = "leader-not-reaped"
            else:
                cleanup_status = "pipe-drain-incomplete"
        def decoded(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
        raise AssertionError(
            f"{label}: timeout; budget={timeout}s; work_elapsed={work_elapsed:.3f}s; "
            f"cleanup_elapsed={time.monotonic() - cleanup_started:.3f}s; cleanup={cleanup_status}\n"
            f"stdout:\n{decoded(stdout)}\nstderr:\n{decoded(stderr)}"
        ) from None
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


class CommandExampleRunnerTests(unittest.TestCase):
    def test_default_budget_and_normal_exit_keep_the_original_contract(self):
        self.assertEqual(15, run_example.__kwdefaults__["timeout"])
        with tempfile.TemporaryDirectory() as directory:
            for status in (0, 7):
                result = run_example('printf "visible stdout\\n"; printf "visible stderr\\n" >&2; exit "$1"',
                                     Path(directory), str(status))
                self.assertEqual(status, result.returncode)
                self.assertEqual("visible stdout\n", result.stdout)
                self.assertEqual("visible stderr\n", result.stderr)

    def test_timeout_keeps_both_streams_kills_its_descendant_and_spares_another_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unrelated = subprocess.Popen(["sleep", "60"], start_new_session=True)
            try:
                code = ('sleep 60 & child=$!; printf "%s\\n" "$child" > child.pid; '
                        'printf "configure complete\\n"; printf "build waiting\\n" >&2; wait')
                with self.assertRaises(AssertionError) as failure:
                    run_example(code, root, timeout=0.5, label="timeout-fixture")
                message = str(failure.exception)
                for expected in ("timeout-fixture", "budget=0.5s", "work_elapsed=", "cleanup_elapsed=",
                                 "stdout:\nconfigure complete", "stderr:\nbuild waiting"):
                    self.assertIn(expected, message)
                child = int((root / "child.pid").read_text())
                # Linux may briefly retain an already killed orphan as a zombie;
                # that is not a running child, and is reaped by its new parent.
                state = Path(f"/proc/{child}/stat")
                try:
                    child_state = state.read_text().rsplit(") ", 1)[1].split()[0]
                except FileNotFoundError:
                    pass
                else:
                    self.assertEqual("Z", child_state)
                self.assertIsNone(unrelated.poll(), "cleanup must not signal another process group")
            finally:
                unrelated.kill()
                unrelated.wait(timeout=2)
                if (root / "child.pid").exists():
                    try:
                        os.kill(int((root / "child.pid").read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass


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


class SecurityScanExampleTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(shutil.which("rg"), "execute published scans with real ripgrep")
        temporary = tempfile.TemporaryDirectory(prefix="adk scan evidence ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sentinel = "SYNTHETIC_ONLY_NOT_A_CREDENTIAL_8713"
        self.content = f'api_key="{self.sentinel}" license curl https writeFile BASE_URL\n'
        self.commands = []
        for source, count in ((SECURITY, 5), (SUPPLY_RUNBOOK, 2)):
            commands = [line for line in bash_example(source, "<candidate_path>").splitlines()
                        if line.startswith("rg ") and "<candidate_path>" in line]
            self.assertEqual(count, len(commands), source)
            self.commands.extend((source, index, command)
                                 for index, command in enumerate(commands, 1))

    def scan(self, command, candidate):
        code = "set -euo pipefail\n" + command.replace("<candidate_path>", '"$1"')
        return run_example(code, self.root, str(candidate), label="security-candidate-scan")

    def test_all_scans_keep_candidate_paths_without_printing_matching_contents(self):
        candidate = self.root / "candidate assets [fixture]"
        candidate.mkdir()
        paths = set()
        for index in range(24):
            path = candidate / f"asset-{index}.txt"
            path.write_text(self.content)
            paths.add(str(path))
        for source, index, command in self.commands:
            with self.subTest(source=source, command=index):
                result = self.scan(command, candidate)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(self.sentinel in result.stdout + result.stderr,
                                 "published scan printed synthetic file contents")
                self.assertEqual(paths, set(result.stdout.splitlines()))

    def test_no_match_and_io_errors_keep_distinct_status_and_diagnostics(self):
        ordinary = self.root / "ordinary.txt"
        ordinary.write_text("ordinary neutral prose\n")
        absent = self.root / "missing candidate.txt"
        for source, index, command in self.commands:
            with self.subTest(source=source, command=index):
                empty = self.scan(command, ordinary)
                self.assertEqual(1, empty.returncode, empty.stderr)
                self.assertEqual("", empty.stdout + empty.stderr)
                error = self.scan(command, absent)
                self.assertEqual(2, error.returncode, error.stderr)
                self.assertEqual("", error.stdout)
                self.assertIn(str(absent), error.stderr)

    def test_secret_scan_preserves_hidden_ignored_coverage_and_git_exclusion(self):
        candidate = self.root / "candidate"
        candidate.mkdir()
        (candidate / ".git").mkdir()
        (candidate / ".gitignore").write_text("ignored.txt\n")
        for path in (candidate / ".env", candidate / "ignored.txt", candidate / ".git/config"):
            path.write_text(self.content)
        source, index, command = next(item for item in self.commands
                                      if item[0] == SECURITY and "api[_-]?key" in item[2])
        result = self.scan(command, candidate)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({str(candidate / ".env"), str(candidate / "ignored.txt")},
                         set(result.stdout.splitlines()))
        self.assertNotIn(self.sentinel, result.stdout + result.stderr)


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
        for codes in ([0, 0, 0], [9, 9, 9], [0, 1, 2, 0], [0, 1, 9, 124]):
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

    def test_reported_interrupt_status_stops_after_preserving_the_current_sample(self):
        for status in (130, 143):
            with self.subTest(status=status):
                result, output = self.sample([status, 0, 0], directory=f"reported-{status}")
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-2").exists())
                self.assertEqual(["run-1"], sorted(path.name for path in output.glob("run-*")))
                log = (output / "run-1/output.log").read_text()
                self.assertIn("stderr retained", log)
                self.assertIn("error test_items[case 1]", log)
                self.assertTrue((output / "run-1/result.json").is_file())
                self.assertNotIn("attempts=3", result.stdout)

    def test_interrupt_after_an_observation_preserves_both_samples_and_stops(self):
        for previous, status in ((0, 130), (9, 143)):
            with self.subTest(previous=previous, status=status):
                result, output = self.sample([previous, status, 0], directory=f"later-{status}")
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{previous}\n2\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-3").exists())
                for attempt in (1, 2):
                    self.assertIn("stderr retained", (output / f"run-{attempt}/output.log").read_text())

    def test_child_self_signals_stop_sampling_without_claiming_parent_signal_handling(self):
        for signum, status in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(signal=signum.name):
                command = ("import os, signal, sys\n"
                           "print('before child signal', flush=True)\n"
                           "print('child stderr retained', file=sys.stderr, flush=True)\n"
                           f"signal.signal({int(signum)}, signal.SIG_DFL)\n"
                           f"os.kill(os.getpid(), {int(signum)})\n"
                           "raise AssertionError('child continued after its signal')\n")
                result, output = self.sample([status, 0, 0], directory=signum.name, code=command)
                self.assertEqual(status, result.returncode, result.stderr)
                self.assertEqual(f"attempt\texit_code\n1\t{status}\n",
                                 (output / "results.tsv").read_text())
                self.assertFalse((output / "run-2").exists())
                self.assertEqual(["run-1"], sorted(path.name for path in output.glob("run-*")))
                log = (output / "run-1/output.log").read_text()
                self.assertIn("before child signal", log)
                self.assertIn("child stderr retained", log)
                self.assertNotIn("child continued", log)

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


class BspBuildExampleTests(unittest.TestCase):
    """Run GNU make with a tiny recording Makefile, not a simulated device build."""

    def setUp(self):
        self.assertIsNotNone(shutil.which("make"), "the published example requires GNU make")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source tree"
        self.source.mkdir()
        self.output = self.root / "build output"
        self.capture = self.root / "make-calls.tsv"
        record = ('\t@printf "%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n" '
                  '"$@" "$(ARCH)" "$(CROSS_COMPILE)" "$(O)" "$(MAKEFLAGS)" '
                  '"$(CURDIR)" >> "$(BSP_CAPTURE)"\n')
        (self.source / "Makefile").write_text(
            ".PHONY: board_defconfig board-image board.dtb\n"
            "board_defconfig:\n" + record +
            '\t@test "$(FAIL_CONFIG)" != "1"\n'
            '\t@printf "CONFIG_BOARD=y\\n" > "$(O)/.config"\n'
            "board-image board.dtb:\n" + record +
            '\t@test -f "$(O)/.config"\n'
            '\t@test "$(FAIL_BUILD)" != "1"\n'
            '\t@printf "fixture artifact\\n" > "$(O)/$@"\n'
        )
        self.environment = dict(os.environ, BSP_SOURCE_DIR=str(self.source), BSP_OUTPUT_DIR=str(self.output),
                                BSP_ARCH="arm", BSP_CROSS_COMPILE="arm-linux-gnueabihf-",
                                BSP_DEFCONFIG="board_defconfig", BSP_IMAGE_TARGET="board-image",
                                BSP_DT_TARGET="board.dtb", BSP_BUILD_JOBS="2", BSP_CAPTURE=str(self.capture),
                                ARCH="arm64", CROSS_COMPILE="wrong-host-toolchain-", MAKEFLAGS="-j17",
                                FAIL_CONFIG="0", FAIL_BUILD="0")
        self.code = bash_example(BSP, "# verified-linux-kbuild:")

    def build(self, **overrides):
        return run_example(self.code, self.root, environment=dict(self.environment, **overrides))

    def calls(self):
        return [line.split("\t") for line in self.capture.read_text().splitlines()]

    def test_make_preserves_selected_arch_toolchain_config_output_and_cpu_ram_budget(self):
        result = self.build()
        self.assertEqual(0, result.returncode, result.stderr)
        rows = self.calls()
        self.assertEqual("board_defconfig", rows[0][0])
        self.assertCountEqual(["board-image", "board.dtb"], [row[0] for row in rows[1:]])
        for target, arch, cross, output, flags, source in rows:
            self.assertEqual("arm", arch, target)
            self.assertEqual("arm-linux-gnueabihf-", cross, target)
            self.assertEqual(str(self.output), output)
            self.assertEqual(str(self.source), source)
            self.assertRegex(flags, r"(?:^|\s)-j2(?:\s|$)")
            self.assertNotIn("-j17", flags)
        self.assertEqual("CONFIG_BOARD=y\n", (self.output / ".config").read_text())
        self.assertTrue((self.output / "board-image").is_file())
        self.assertTrue((self.output / "board.dtb").is_file())

    def test_no_dt_target_does_not_invent_a_dt_build(self):
        result = self.build(BSP_ARCH="arm64", BSP_CROSS_COMPILE="aarch64-linux-gnu-", BSP_DT_TARGET="")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["board_defconfig", "board-image"], [row[0] for row in self.calls()])
        self.assertTrue(all(row[1:3] == ["arm64", "aarch64-linux-gnu-"] for row in self.calls()))
        self.assertFalse((self.output / "board.dtb").exists())

    def test_invalid_job_budget_stops_before_configuration_or_output_creation(self):
        for jobs in ("", "0", "-1", "02", "2.5", "$(touch MUST_NOT_RUN)"):
            with self.subTest(jobs=jobs):
                result = self.build(BSP_BUILD_JOBS=jobs)
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.capture.exists())
        self.assertFalse((self.root / "MUST_NOT_RUN").exists())

    def test_existing_output_and_config_are_never_reused_or_reset(self):
        self.output.mkdir()
        original = self.output / ".config"
        original.write_text("CONFIG_USER_SETTING=y\n")
        result = self.build()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("CONFIG_USER_SETTING=y\n", original.read_text())
        self.assertFalse(self.capture.exists())

    def test_config_failure_prevents_image_and_dt_commands(self):
        result = self.build(FAIL_CONFIG="1")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(["board_defconfig"], [row[0] for row in self.calls()])
        self.assertFalse((self.output / "board-image").exists())
        self.assertFalse((self.output / "board.dtb").exists())

    def test_build_failure_is_reported_and_keeps_config_for_diagnosis(self):
        result = self.build(FAIL_BUILD="1", BSP_DT_TARGET="")
        self.assertNotEqual(0, result.returncode)
        self.assertTrue((self.output / ".config").is_file())
        self.assertFalse((self.output / "board-image").exists())

    def test_missing_identity_input_and_relative_output_do_not_build(self):
        for name in ("BSP_SOURCE_DIR", "BSP_OUTPUT_DIR", "BSP_ARCH", "BSP_CROSS_COMPILE",
                     "BSP_DEFCONFIG", "BSP_IMAGE_TARGET"):
            with self.subTest(missing=name):
                result = self.build(**{name: ""})
                self.assertNotEqual(0, result.returncode)
                self.assertFalse(self.output.exists())
                self.assertFalse(self.capture.exists())
        result = self.build(BSP_OUTPUT_DIR="relative-output")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.root / "relative-output").exists())


class EmbeddedAdcExampleTests(unittest.TestCase):
    """Compile and execute the shipped C tests; no target/device claim."""

    def setUp(self):
        self.compiler = shutil.which("cc")
        self.assertIsNotNone(self.compiler, "the ADC example requires a real native C compiler")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def compile_and_run(self, *flags):
        executable = self.root / "adc-test"
        result = subprocess.run(
            [self.compiler, "-std=c11", "-Wall", "-Wextra", "-Werror", "-O2", *flags,
             "-I", str(ADC / "src"), str(ADC / "src/adc_scale.c"),
             str(ADC / "tests/test_adc_scale.c"), "-o", str(executable)],
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)
        result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for name in ("zero", "full-scale", "invalid", "maximum-int-full-scale", "maximum-int-clamped"):
            self.assertIn("PASS " + name + " ", result.stdout)

    def test_native_endpoints_clamping_and_invalid_inputs(self):
        self.compile_and_run("-DNDEBUG")

    def test_native_endpoints_with_supported_ubsan(self):
        flags = ("-fsanitize=signed-integer-overflow", "-fno-sanitize-recover=all")
        probe = self.root / "sanitizer-probe.c"
        probe.write_text("#include <limits.h>\nint main(void) { volatile int n = INT_MAX; return n + 1; }\n")
        executable = self.root / "sanitizer-probe"
        compiled = subprocess.run([self.compiler, *flags, str(probe), "-o", str(executable)],
                                  capture_output=True, text=True, timeout=15)
        if compiled.returncode:
            self.skipTest("UBSan capability unavailable: " + compiled.stderr.strip())
        result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        if result.returncode == 0 or "signed integer overflow" not in result.stderr:
            self.skipTest("UBSan runtime did not diagnose the overflow probe: " + result.stderr.strip())
        # A failure in the actual example is a regression, never a capability skip.
        self.compile_and_run(*flags)


class _CmakeExampleFixture:
    def prepare(self, *, register_tests=True, generator="Ninja"):
        backend = "make" if generator == "Unix Makefiles" else "ninja"
        required = ("cmake", "ctest", backend, "cc", "file", "size", "objdump", "python3", "mktemp")
        missing = [tool for tool in required if shutil.which(tool) is None]
        if missing:
            reason = "real CMake example not executed; missing tools: " + ", ".join(missing)
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail(reason + "; GitHub Actions must execute this fixture")
            self.skipTest(reason)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.evidence = self.root / "test evidence"
        self.evidence.mkdir()
        self.source = self.root / "source project"
        self.source.mkdir()
        (self.source / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.21)\n'
            'project(adk_command_example C)\n'
            'enable_testing()\n'
            'set(FIXTURE_ID "manual" CACHE STRING "")\n'
            'add_executable(firmware main.c)\n'
            'set_target_properties(firmware PROPERTIES SUFFIX ".elf")\n'
            'file(GENERATE OUTPUT "${CMAKE_BINARY_DIR}/$<CONFIG>/identity.h"\n'
            '  CONTENT "#define FIXTURE_ID \\\"${FIXTURE_ID}:$<CONFIG>\\\"\\n")\n'
            'target_include_directories(firmware PRIVATE "${CMAKE_BINARY_DIR}/$<CONFIG>")\n'
            + ('add_test(NAME identity COMMAND firmware "${CMAKE_BINARY_DIR}/ctest-identity.txt")\n'
               if register_tests else ''))
        (self.source / "main.c").write_text(
            '#include <stdio.h>\n#include "identity.h"\n'
            'int main(int argc, char **argv) {\n'
            '  puts(FIXTURE_ID);\n'
            '  if (argc == 2) {\n'
            '    FILE *receipt = fopen(argv[1], "w");\n'
            '    if (!receipt) return 2;\n'
            '    int written = fprintf(receipt, "%s\\n", FIXTURE_ID);\n'
            '    if (fclose(receipt) != 0 || written < 0) return 3;\n'
            '  }\n'
            '  return 0;\n}\n')
        self.toolchain = self.source / "host toolchain.cmake"
        self.toolchain.write_text('set(CMAKE_C_COMPILER "' + shutil.which("cc") + '")\n')
        self.output = self.source / "out" / "manual build"
        self.environment = dict(
            os.environ, CC=shutil.which("cc"), ADK_SOURCE_DIR=str(self.source),
            ADK_BINARY_DIR=str(self.output), ADK_GENERATOR=generator, ADK_BUILD_MODE="manual",
            ADK_TOOLCHAIN_FILE=str(self.toolchain), ADK_CONFIG="Release", ADK_BUILD_JOBS="1",
            ADK_TEST_BACKEND="host-unit", ADK_ELF=str(self.output / "firmware.elf"),
            ADK_SIZE=shutil.which("size"), ADK_OBJDUMP=shutil.which("objdump"),
            ADK_EVIDENCE_DIR=str(self.evidence),
            ADK_CONFIGURE_PRESET="unselected-configure", ADK_BUILD_PRESET="unselected-build",
            ADK_TEST_PRESET="unselected-test")

    def published(self, marker, **overrides):
        environment = dict(self.environment, **overrides)
        # Fixture-only trace identifies the last configure/build/CTest command
        # if the aggregate example budget expires; the published block is intact.
        return run_example("set -x\n" + bash_example(CMAKE, marker), self.source,
                           environment=environment, label=f"CMake/{environment['ADK_BUILD_MODE']}/{marker}")

    def assert_identity(self, identity, output, artifact):
        self.assertEqual(identity + "\n", (output / "ctest-identity.txt").read_text())
        self.assertEqual(b"\x7fELF", artifact.read_bytes()[:4])
        executed = subprocess.run([str(artifact)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, executed.returncode, executed.stderr)
        self.assertEqual(identity + "\n", executed.stdout)
        inspected = self.published("# built-artifact:", ADK_ELF=str(artifact))
        self.assertEqual(0, inspected.returncode, inspected.stdout + inspected.stderr)
        self.assertIn(str(artifact), inspected.stdout)
        self.assertIn(".text", inspected.stdout)


class CmakeBuildExampleTests(_CmakeExampleFixture, unittest.TestCase):
    """Keep the original Ninja/multiconfig cases and their CI tool requirement."""

    def test_preset_names_bind_binary_directory_configuration_tests_and_elf(self):
        self.prepare()
        old = self.source / "build" / "demo"
        # A real, separately configured old build makes a wrong directory observable.
        for command in (["cmake", "-S", str(self.source), "-B", str(old), "-G", "Ninja",
                         "-DFIXTURE_ID=old", "-DCMAKE_BUILD_TYPE=Debug"],
                        ["cmake", "--build", str(old), "--parallel", "1"]):
            result = subprocess.run(command, env=self.environment, capture_output=True, text=True, timeout=15)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        old_bytes = {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()}
        output = self.source / "out" / "preset build"
        (self.source / "CMakePresets.json").write_text(json.dumps({
            "version": 3,
            "configurePresets": [{"name": "configure-board", "generator": "Ninja Multi-Config",
                                  "binaryDir": "${sourceDir}/out/preset build",
                                  "cacheVariables": {"FIXTURE_ID": "preset", "CMAKE_CONFIGURATION_TYPES": "Debug;Release"}}],
            "buildPresets": [{"name": "compile-release", "configurePreset": "configure-board", "configuration": "Release"}],
            "testPresets": [{"name": "run-release", "configurePreset": "configure-board", "configuration": "Release"}],
        }))
        result = self.published("# cmake-build:", ADK_BUILD_MODE="preset", ADK_CONFIGURE_PRESET="configure-board",
                                ADK_BUILD_PRESET="compile-release", ADK_TEST_PRESET="run-release",
                                ADK_BINARY_DIR=str(self.source / "must-not-be-created"),
                                ADK_TOOLCHAIN_FILE="missing-unselected-toolchain", ADK_GENERATOR="unselected")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assert_identity("preset:Release", output, output / "Release" / "firmware.elf")
        self.assertFalse((self.source / "must-not-be-created").exists())
        self.assertEqual(old_bytes, {p.relative_to(old): p.read_bytes() for p in old.rglob("*") if p.is_file()})

    def test_manual_directory_configuration_tests_and_elf_do_not_invoke_presets(self):
        self.prepare()
        result = self.published("# cmake-build:", ADK_CONFIG="RelWithDebInfo")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assert_identity("manual:RelWithDebInfo", self.output, self.output / "firmware.elf")
        self.assertFalse((self.source / "build").exists())

    def test_empty_ctest_selection_fails_after_a_real_successful_build(self):
        self.prepare(register_tests=False)
        result = self.published("# cmake-build:")
        self.assertNotEqual(0, result.returncode)
        self.assertTrue((self.output / "firmware.elf").is_file())
        self.assertIn("No tests", result.stdout + result.stderr)
        self.assertFalse((self.output / "ctest-identity.txt").exists())

    def test_compile_only_preserves_not_run_without_invoking_ctest(self):
        self.prepare(register_tests=False)
        result = self.published("# cmake-build:", ADK_TEST_BACKEND="compile-only")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("target tests: not-run", result.stdout)
        self.assertTrue((self.output / "firmware.elf").is_file())
        self.assertFalse((self.output / "ctest-identity.txt").exists())

    def test_adc_cmake_target_builds_and_runs_with_a_strict_c90_default(self):
        self.prepare()
        # The library needs C11; its consumer tests themselves remain valid C90.
        self.toolchain.write_text(self.toolchain.read_text()
                                  + 'set(CMAKE_C_STANDARD 90)\n'
                                  + 'set(CMAKE_C_STANDARD_REQUIRED ON)\n'
                                  + 'set(CMAKE_C_EXTENSIONS OFF)\n')
        result = self.published("# cmake-build:", ADK_SOURCE_DIR=str(ADC), CFLAGS="-pedantic-errors")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("adc_scale_host_unit", result.stdout)
        executable = self.output / "test_adc_scale"
        executed = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, executed.returncode, executed.stdout + executed.stderr)
        self.assertIn("PASS maximum-int-full-scale ", executed.stdout)
        self.assertIn("PASS maximum-int-clamped ", executed.stdout)
        inspected = self.published("# built-artifact:", ADK_ELF=str(executable))
        self.assertEqual(0, inspected.returncode, inspected.stdout + inspected.stderr)
        self.assertIn(str(executable), inspected.stdout)


class CtestQualificationExampleTests(_CmakeExampleFixture, unittest.TestCase):
    """Real native CMake/CTest semantics, using an available single-config backend."""

    def prepare_native(self, *, register_tests=True, extra=""):
        self.prepare(register_tests=register_tests, generator="Unix Makefiles")
        cmake = self.source / "CMakeLists.txt"
        cmake.write_text(cmake.read_text() + extra)

    def reports(self):
        return sorted(self.evidence.glob("ctest.*/ctest.xml"))

    def test_all_skipped_is_rejected_despite_successful_ctest_exit(self):
        self.prepare_native(register_tests=False, extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'))
        result = self.published("# cmake-build:")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("passed=0 selected=1 skipped=1", result.stdout)
        self.assertIn("no executed passing tests", result.stderr)
        report, = self.reports()
        self.assertEqual("notrun", ET.parse(report).getroot().find("testcase").get("status"))

    def test_empty_and_all_disabled_selections_remain_failures(self):
        for extra in ("", 'add_test(NAME disabled COMMAND "${CMAKE_COMMAND}" -E true)\n'
                          'set_tests_properties(disabled PROPERTIES DISABLED TRUE)\n'):
            with self.subTest(disabled=bool(extra)):
                self.prepare_native(register_tests=False, extra=extra)
                result = self.published("# cmake-build:")
                self.assertNotEqual(0, result.returncode)
                self.assertTrue((self.output / "firmware.elf").is_file())
                self.assertIn("CTest report:", result.stdout)

    def test_mixed_results_report_partial_and_test_runs_only_once(self):
        self.prepare_native(extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'
            'add_test(NAME disabled COMMAND "${CMAKE_COMMAND}" -E true)\n'
            'set_tests_properties(disabled PROPERTIES DISABLED TRUE)\n'))
        main = self.source / "main.c"
        main.write_text(main.read_text().replace('fopen(argv[1], "w")', 'fopen(argv[1], "a")'))
        result = self.published("# cmake-build:")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("status=partial passed=1 selected=3 skipped=1 disabled=1", result.stdout)
        self.assertEqual("manual:Release\n", (self.output / "ctest-identity.txt").read_text())
        self.assertEqual(1, len(self.reports()))

    def test_new_run_cannot_reuse_a_previous_passing_report(self):
        self.prepare_native()
        first = self.published("# cmake-build:")
        self.assertEqual(0, first.returncode, first.stdout + first.stderr)
        self.assertIn("status=pass passed=1 selected=1 skipped=0 disabled=0", first.stdout)
        original, = self.reports()
        original_bytes = original.read_bytes()
        cmake = self.source / "CMakeLists.txt"
        cmake.write_text(cmake.read_text() + 'set_tests_properties(identity PROPERTIES SKIP_RETURN_CODE 0)\n')
        second = self.published("# cmake-build:")
        self.assertNotEqual(0, second.returncode)
        self.assertIn("passed=0 selected=1 skipped=1", second.stdout)
        self.assertEqual(2, len(self.reports()))
        self.assertEqual(original_bytes, original.read_bytes())
        new_report, = [p for p in self.reports() if p != original]
        self.assertIn(str(new_report), second.stdout)

    def test_real_ctest_failure_keeps_its_nonzero_status(self):
        self.prepare_native(extra='add_test(NAME failing COMMAND "${CMAKE_COMMAND}" -E false)\n')
        result = self.published("# cmake-build:")
        self.assertEqual(8, result.returncode, result.stdout + result.stderr)
        self.assertNotIn("status=pass", result.stdout)
        report, = self.reports()
        cases = ET.parse(report).getroot().findall("testcase")
        self.assertEqual({"run", "fail"}, {c.get("status") for c in cases})

    def test_failed_build_does_not_read_or_replace_an_old_report(self):
        self.prepare_native()
        old = self.evidence / "ctest.old"
        old.mkdir()
        report = old / "ctest.xml"
        original = b'<testsuite tests="1"><testcase status="run"/></testsuite>'
        report.write_bytes(original)
        (self.source / "main.c").write_text("this is an intentional compiler error\n")
        result = self.published("# cmake-build:")
        self.assertNotEqual(0, result.returncode)
        self.assertNotIn("CTest report:", result.stdout)
        self.assertEqual([report], self.reports())
        self.assertEqual(original, report.read_bytes())

    def test_preset_compile_only_needs_no_test_preset_or_python(self):
        self.prepare_native(register_tests=False)
        output = self.source / "out" / "compile-only preset"
        (self.source / "CMakePresets.json").write_text(json.dumps({
            "version": 3,
            "configurePresets": [{"name": "native", "generator": "Unix Makefiles",
                                  "binaryDir": str(output),
                                  "cacheVariables": {"CMAKE_BUILD_TYPE": "Release",
                                                     "CMAKE_C_COMPILER": shutil.which("cc")}}],
            "buildPresets": [{"name": "compile", "configurePreset": "native"}],
        }))
        tool_path = self.root / "build-tools-without-python"
        tool_path.mkdir()
        for name in ("bash", "cmake", "make", "gmake", "cc", "as", "ld", "ar", "ranlib"):
            actual = shutil.which(name)
            if actual:
                (tool_path / name).symlink_to(actual)
        self.assertIsNone(shutil.which("python3", path=str(tool_path)))
        environment = dict(self.environment, PATH=str(tool_path), ADK_BUILD_MODE="preset",
                           ADK_CONFIGURE_PRESET="native", ADK_BUILD_PRESET="compile",
                           ADK_TEST_BACKEND="compile-only")
        for name in ("ADK_TEST_PRESET", "ADK_EVIDENCE_DIR"):
            environment.pop(name)
        result = run_example("set -x\n" + bash_example(CMAKE, "# cmake-build:"), self.source,
                             environment=environment, label="CMake/preset/compile-only/no-python")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("target tests: not-run", result.stdout)
        self.assertTrue((output / "firmware.elf").is_file())
        self.assertEqual([], self.reports())

    def test_hil_collection_preserves_skip_evidence_without_claiming_qualification(self):
        self.prepare_native(register_tests=False, extra=(
            'add_test(NAME skipped COMMAND "${CMAKE_COMMAND}" -E false)\n'
            'set_tests_properties(skipped PROPERTIES SKIP_RETURN_CODE 1)\n'))
        built = self.published("# cmake-build:", ADK_TEST_BACKEND="compile-only")
        self.assertEqual(0, built.returncode, built.stdout + built.stderr)
        result = run_example(bash_example(HIL, "# hil-sil-ctest:"), self.source,
                             environment=self.environment, label="SIL/report-collection")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report, = self.reports()
        self.assertIn(str(report), result.stdout)
        self.assertEqual("notrun", ET.parse(report).getroot().find("testcase").get("status"))
        qualification = (ROOT / HIL).read_text()
        for marker in ("不自动判整项通过", "零实际 pass", "混合 pass/skip 为 partial", "缺必跑项 blocked"):
            self.assertIn(marker, qualification)


class CtestReportReaderTests(unittest.TestCase):
    def test_published_reader_rejects_missing_malformed_unknown_and_failure_results(self):
        block = bash_example(CMAKE, "# cmake-build:")
        reader, = re.findall(r"python3 - \"\$report\" <<'PY'\n(.*?)\nPY", block, re.S)
        passing = '<testcase name="passing" status="run"/>'
        skipped = '<testcase name="skipped" status="notrun"><skipped/></testcase>'
        disabled = '<testcase name="disabled" status="disabled"/>'
        cases = [
            (f'<testsuite tests="1">{passing}</testsuite>', True, "status=pass passed=1"),
            (f'<testsuite tests="3">{passing}{skipped}{disabled}</testsuite>', True,
             "status=partial passed=1 selected=3 skipped=1 disabled=1"),
            (f'<testsuite tests="1">{skipped}</testsuite>', False, "passed=0"),
            (f'<testsuite tests="1">{disabled}</testsuite>', False, "passed=0"),
            ('<testsuite tests="0"/>', False, "passed=0"),
            (f'<other tests="1">{passing}</other>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase/></testsuite>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase status="unknown"/></testsuite>', False,
             "invalid CTest report"),
            (f'<testsuite tests="99">{passing}</testsuite>', False, "invalid CTest report"),
            (f'<testsuite tests="2">{passing}<testcase status="fail"><failure/></testcase></testsuite>',
             False, "CTest failures in report"),
            (f'<testsuite tests="2">{passing}<testcase status="run"><error/></testcase></testsuite>',
             False, "CTest failures in report"),
            (f'<testsuite tests="2">{passing}<testcase status="run"><skipped/></testcase></testsuite>',
             False, "invalid passing status"),
            ("<testsuite", False, "ParseError"),
            ("", False, "ParseError"),
            (None, False, "FileNotFoundError"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for index, (xml, success, expected) in enumerate(cases):
                with self.subTest(index=index):
                    report = Path(directory) / f"report-{index}.xml"
                    if xml is not None:
                        report.write_text(xml)
                    result = subprocess.run([sys.executable, "-c", reader, str(report)],
                                            capture_output=True, text=True, timeout=15)
                    self.assertEqual(success, result.returncode == 0, result.stdout + result.stderr)
                    self.assertIn(expected, result.stdout + result.stderr)


class InterfaceVersionExampleTests(unittest.TestCase):
    def test_compiled_consumer_requires_minor_21_and_async_cancel(self):
        compiler = shutil.which("cc")
        self.assertIsNotNone(compiler, "compile the published C example with a real native compiler")
        blocks = re.findall(r"```c\n(.*?)```", (ROOT / INTERFACE).read_text(), re.S)
        code, = [block for block in blocks if "iface_version_compatible(" in block]
        # Literal vectors derive from the consumer contract, not the implementation macros.
        vectors = [(0x0000, 1, 0), (0x01ff, 1, 0), (0x0200, 1, 0), (0x0201, 1, 1),
                   (0x0202, 1, 1), (0x02ff, 1, 1), (0x0300, 1, 0), (0xffff, 1, 0),
                   (0x0201, 0, 0), (0x0202, 2, 0), (0x0202, 3, 1)]
        rows = ",\n".join(f"{{{version}, {caps}, {expected}}}" for version, caps, expected in vectors)
        harness = ('\n#include <stdio.h>\n'
                   'int main(void) {\n'
                   '  const struct { uint16_t version; uint32_t caps; bool expected; } cases[] = {\n' + rows +
                   '\n  };\n'
                   '  for (unsigned int i = 0; i < sizeof cases / sizeof cases[0]; ++i) {\n'
                   '    bool actual = iface_version_compatible(cases[i].version, cases[i].caps);\n'
                   '    if (actual != cases[i].expected) {\n'
                   '      fprintf(stderr, "case %u: actual=%d expected=%d\\n", i, actual, cases[i].expected);\n'
                   '      return 1;\n'
                   '    }\n'
                   '  }\n'
                   '  return 0;\n'
                   '}\n')
        with tempfile.TemporaryDirectory() as directory:
            source, executable = Path(directory) / "version.c", Path(directory) / "version-check"
            source.write_text(code + harness)
            compiled = subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                                       str(source), "-o", str(executable)], capture_output=True, text=True, timeout=15)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=15)
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
