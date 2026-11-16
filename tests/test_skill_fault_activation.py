"""Calibrate the published observation branch; no device, SLA or model qualification."""
from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/adk-fault-injection-recovery/SKILL.md"
FIXTURE = ROOT / "tests/fixtures/fault-activation.c"


@unittest.skipUnless(sys.platform.startswith("linux"), "not-applicable: owned Linux/GNU ld fixture")
class FaultActivationMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shutil.which("gcc")
        if cls.compiler is None:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                raise AssertionError("host GCC required for fault-method validation")
            raise unittest.SkipTest("not-run: host GCC unavailable; no tool installed")
        cls.temporary = tempfile.TemporaryDirectory(prefix="adk-fault-method-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name)
        supported = cls.directory / "supported.c"
        supported.write_text("int main(void) { return 0; }\n", encoding="utf-8")
        command = [cls.compiler, str(supported), "-Wl,--wrap=malloc,--wrap=free",
                   "-o", str(cls.directory / "supported")]
        capability = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if capability.returncode:
            raise unittest.SkipTest("not-applicable: linker wrapping unavailable: " + capability.stderr[:300])
        startup = subprocess.run([str(cls.directory / "supported")], capture_output=True,
                                 text=True, timeout=5)
        if startup.returncode or startup.stderr:
            raise unittest.SkipTest("inconclusive: owned host executable did not start cleanly")
        cls.binaries = {}
        for variant in ("correct", "broken"):
            binary = cls.directory / variant
            command = [cls.compiler, "-std=c11", "-O0", "-Wall", "-Wextra", "-Werror"]
            if variant == "broken":
                command.append("-DBROKEN_CLEANUP")
            command += [str(FIXTURE), "-Wl,--wrap=malloc,--wrap=free", "-o", str(binary)]
            built = subprocess.run(command, capture_output=True, text=True, timeout=10)
            if built.returncode:
                raise AssertionError(built.stdout + built.stderr)
            cls.binaries[variant] = binary

    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")
        matches = re.findall(r"<!-- adk-example: fault-observation -->\s*```python\n(.*?)\n```",
                             self.text, re.S)
        self.assertEqual(1, len(matches), "missing or ambiguous published observation example")
        namespace = {}
        exec(compile(matches[0], str(SKILL), "exec"), namespace)
        self.next_check = namespace["next_check"]

    def observe(self, fail_at, *, variant="correct", observable=True):
        command = [str(self.binaries[variant]), str(fail_at), str(int(observable))]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        print(json.dumps({"host_fault_probe": {"argv": command, "exit": result.returncode,
                                                "stdout": result.stdout, "stderr": result.stderr}}))
        return json.loads(result.stdout)

    def normal_control(self, *, variant="correct"):
        control = self.observe(0, variant=variant)
        self.assertEqual((2, 0, 0, 42, 0), tuple(control[key] for key in (
            "initial_calls", "initial_injected", "initial_result", "initial_output", "live_after_initial")))
        self.assertEqual((0, 42, 0), tuple(control[key] for key in (
            "follow_up_result", "follow_up_output", "live_after_follow_up")))
        return True

    def test_configured_but_unreached_fault_is_not_evaluated(self):
        control_ok = self.normal_control()
        sample = self.observe(3)
        self.assertEqual((2, 0, 0, 42), tuple(sample[key] for key in (
            "initial_calls", "initial_injected", "initial_result", "follow_up_output")))
        self.assertEqual("not_evaluated", self.next_check(control_ok, sample["initial_injected"]))

    def test_unknown_activation_is_not_inferred_from_error_or_healthy_follow_up(self):
        control_ok = self.normal_control()
        sample = self.observe(2, observable=False)
        self.assertIsNone(sample["initial_injected"])
        self.assertEqual(errno.ENOMEM, sample["initial_result"])
        self.assertEqual((0, 42, 0), tuple(sample[key] for key in (
            "follow_up_result", "follow_up_output", "live_after_follow_up")))
        self.assertEqual("not_evaluated", self.next_check(control_ok, sample["initial_injected"]))

    def test_observed_fault_only_opens_detection_and_recovery_checks(self):
        control_ok = self.normal_control()
        sample = self.observe(2)
        self.assertEqual(1, sample["initial_injected"])
        self.assertEqual("待核检测与恢复", self.next_check(control_ok, sample["initial_injected"]))
        # Independent expectations for this fixture's public contract and resources.
        self.assertEqual((errno.ENOMEM, -1, 0), tuple(sample[key] for key in (
            "initial_result", "initial_output", "live_after_initial")))
        self.assertEqual((0, 42, 0), tuple(sample[key] for key in (
            "follow_up_result", "follow_up_output", "live_after_follow_up")))
        self.assertNotIn("detection_ms", sample)
        self.assertNotIn("recovery_ms", sample)

    def test_healthy_follow_up_cannot_hide_broken_cleanup(self):
        control_ok = self.normal_control(variant="broken")
        sample = self.observe(2, variant="broken")
        self.assertEqual("待核检测与恢复", self.next_check(control_ok, sample["initial_injected"]))
        self.assertEqual((errno.ENOMEM, -1, 1, 0, 42, 1), tuple(sample[key] for key in (
            "initial_result", "initial_output", "live_after_initial",
            "follow_up_result", "follow_up_output", "live_after_follow_up")))
        self.assertFalse(sample["live_after_initial"] == sample["live_after_follow_up"] == 0,
                         "known broken cleanup must fail the resource postcondition")

    def test_failed_control_or_unusable_count_never_opens_recovery(self):
        for control_ok, hits in ((False, 1), (True, 0), (True, None), (True, -1)):
            with self.subTest(control_ok=control_ok, hits=hits):
                self.assertEqual("not_evaluated", self.next_check(control_ok, hits))

    def test_published_scope_preserves_timing_and_hardware_limits(self):
        self.assertLessEqual(len(SKILL.read_bytes()), 3559)
        for required in ("缺时间证据不填零时延", "不判 SLA 通过", "数据一致性", "资源恢复",
                         "非 SLA/设备资格", "独立设备操作者", "停止条件", "回滚方案"):
            self.assertIn(required, self.text)


if __name__ == "__main__":
    unittest.main()
