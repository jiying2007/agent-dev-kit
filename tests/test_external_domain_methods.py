"""Run the published host examples; no model, fuzz campaign or board certification."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
PROPERTY = ROOT / "skills/adk-unit-test-embedded/references/property-stateful-tests.md"
SANITIZER = ROOT / "skills/adk-systematic-debugging/references/sanitizer-validation.md"
STACK = ROOT / "skills/adk-performance-profiling-embedded/references/mcu-memory-footprint.md"


def fence(path: Path, language: str) -> str:
    blocks = re.findall(r"(?ms)^```" + re.escape(language) + r"\n(.*?)\n```", path.read_text())
    if len(blocks) != 1:
        raise AssertionError(f"Expected one executable {language} example in {path}")
    return blocks[0] + "\n"


def run(command: list[str], directory: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    return subprocess.run(command, cwd=directory, env=environment, text=True,
                          capture_output=True, timeout=20, check=False)


class PublishedDomainExamplesTests(unittest.TestCase):
    def require_gcc(self, directory: Path, flags: list[str]) -> None:
        if shutil.which("gcc") is None:
            self.skipTest("not-run: GCC unavailable; no dependency installed")
        (directory / "supported.c").write_text("int main(void) { return 0; }\n")
        build = run(["gcc", *flags, "supported.c", "-o", "supported"], directory)
        if build.returncode:
            self.skipTest("not-run: compiler/runtime support unavailable: " + build.stderr[:400])
        started = run([str(directory / "supported")], directory)
        if started.returncode or started.stderr:
            self.skipTest("inconclusive: host runtime did not start cleanly: " + started.stderr[:400])

    def test_public_state_sequence_replays_and_rejects_the_bug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = run([sys.executable, "-I", "-c", fence(PROPERTY, "python")], Path(temporary))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        # The bounded alphabet has sum(3**n for n in range(5)) sequences.
        # Empty/full rejection and fresh state are exercised by that domain.
        self.assertEqual(result["cases"], 121)
        self.assertEqual(result["steps"], 426)
        self.assertEqual(result["counterexample"], [1, 0, 2, 0])
        self.assertEqual(result["expected"], ["ok", 0, "ok", 1])
        self.assertEqual(result["actual"], ["ok", 0, "ok", 0])
        self.assertEqual(result["replay"], result["actual"])
        self.assertEqual(result["fixed_pass"], 121)

    def test_public_ubsan_example_observes_diagnostics_despite_zero_exit(self) -> None:
        for tool in ("bash", "env"):
            if shutil.which(tool) is None:
                self.skipTest(f"not-run: {tool} unavailable")
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self.require_gcc(work, ["-std=c11", "-fsanitize=undefined"])
            capability = run(["env", "-u", "UBSAN_OPTIONS", "gcc", "-dumpmachine"], work)
            if capability.returncode:
                self.skipTest("not-applicable: example requires host env -u support")
            (work / "overflow.c").write_text(fence(SANITIZER, "c"))
            completed = run(["bash", "-c", fence(SANITIZER, "bash")], work)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            exits = {name: int(code) for name, code in
                     re.findall(r"(?m)^(recover|fatal|fixed) exit=(-?\d+)$", completed.stdout)}
            self.assertEqual(set(exits), {"recover", "fatal", "fixed"})
            self.assertEqual(exits["recover"], 0)
            self.assertNotEqual(exits["fatal"], 0)
            self.assertEqual(exits["fixed"], 0)
            for name in ("recover", "fatal"):
                diagnostic = (work / f"{name}.err").read_text()
                self.assertIn("runtime error: signed integer overflow", diagnostic)
            self.assertEqual((work / "fixed.err").read_text(), "")

    def test_public_gcc_stack_example_exposes_dynamic_part(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            self.require_gcc(work, ["-std=c11", "-fstack-usage"])
            target = run(["gcc", "-dumpmachine"], work)
            self.assertEqual(target.returncode, 0, target.stderr)
            if not target.stdout.strip().startswith("x86_64-"):
                self.skipTest("not-applicable: published fixture uses x86-64 -mno-red-zone")
            if shutil.which("bash") is None:
                self.skipTest("not-run: Bash unavailable")
            (work / "stack.c").write_text(fence(STACK, "c"))
            built = run(["bash", "-c", fence(STACK, "bash")], work)
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertTrue((work / "stack.o").is_file())
            # GCC versions differ in the location/mangled-name fields. The
            # trailing bytes and qualifiers have the documented meaning.
            entries = {}
            for line in (work / "stack.su").read_text().splitlines():
                fields = line.split("\t")
                entries[fields[0].rsplit(":", 1)[-1]] = (
                    int(fields[-2]), set(fields[-1].split(",")))
            self.assertEqual(set(entries), {"leaf", "caller", "dynamic_frame"})
            for name, local_bytes in (("leaf", 256), ("caller", 384)):
                self.assertEqual(entries[name][1], {"static"})
                self.assertGreaterEqual(entries[name][0], local_bytes)
            if entries["dynamic_frame"][1] != {"dynamic"}:
                self.skipTest("not-applicable: installed GCC did not emit unbounded dynamic qualifier")
            self.assertGreater(entries["dynamic_frame"][0], 0)
            self.assertLess(entries["dynamic_frame"][0], 4096)
            # Drive the same published object at its allowed VLA maximum;
            # this is host reachability, not measurement of a task stack peak.
            (work / "drive.c").write_text(
                "#include <stddef.h>\nint caller(int); int dynamic_frame(size_t);\n"
                "int main(void) { return caller(3) == 6 && dynamic_frame(4096) == 1 ? 0 : 1; }\n")
            linked = run(["gcc", "drive.c", "stack.o", "-o", "drive"], work)
            self.assertEqual(linked.returncode, 0, linked.stderr)
            exercised = run([str(work / "drive")], work)
            self.assertEqual(exercised.returncode, 0, exercised.stderr)


class DomainDiscoveryTests(unittest.TestCase):
    def test_production_catalog_routes_tasks_and_rejects_near_misses(self) -> None:
        manifest = Manifest.load(ROOT)
        positives = (
            ("adk-unit-test-embedded", "针对消息队列执行 MCU 性质测试"),
            ("adk-unit-test-embedded", "验证取消和复位的 RTOS 状态序列测试"),
            ("adk-systematic-debugging", "对已有崩溃做 sanitizer 取证"),
            ("adk-systematic-debugging", "请求 UBSan 取证，保存错误报告"),
            ("adk-performance-profiling-embedded", "评估 MCU 栈上界，栈预算 4 KiB"),
            ("adk-performance-profiling-embedded", "评估 RTOS 栈上界与 8 KiB 预算"),
        )
        negatives = (
            ("adk-unit-test-embedded", "为 Python Web API 编写性质测试，不涉及 MCU 或 RTOS"),
            ("adk-unit-test-embedded", "解释性质测试与状态序列测试的区别"),
            ("adk-unit-test-embedded", "不要执行 MCU 性质测试"),
            ("adk-systematic-debugging", "只解释 sanitizer 的基本概念，不排障、不运行工具"),
            ("adk-systematic-debugging", "当前调优不需要 UBSan，请仅说明算法复杂度"),
            ("adk-systematic-debugging", "不要进行 sanitizer 取证"),
            ("adk-performance-profiling-embedded", "仅讲解数学上的调用栈上界定义，不开展任何基准任务"),
            ("adk-performance-profiling-embedded", "不要评估 MCU 栈上界"),
        )
        for expected, rows in ((True, positives), (False, negatives)):
            for skill, prompt in rows:
                with self.subTest(skill=skill, prompt=prompt):
                    isolated = match_text(manifest, prompt, skill=skill, scope="skill")
                    automatic = match_text(manifest, prompt, scope="auto")
                    self.assertIs(isolated.get("match"), expected, isolated)
                    self.assertIs(automatic.get("match"), expected, automatic)
                    if expected:
                        self.assertEqual(automatic.get("skill"), skill, automatic)
                        self.assertEqual(automatic.get("runtime_role"), "primary", automatic)
                    else:
                        self.assertEqual(automatic.get("decision"), "abstain", automatic)
                    # Selecting a method is not authorization to write or run a board.
                    self.assertEqual(automatic.get("mutation_permission"), "deny", automatic)


if __name__ == "__main__":
    unittest.main()
