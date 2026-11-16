"""Execute the published host tick-range example; no RTOS/HIL qualification."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]

VECTORS = r"""
#include <stdio.h>
int main(void) {
    const struct {
        uint64_t ms;
        uint32_t hz, maximum;
        int ok;
        uint32_t ticks;
    } cases[] = {
        {0, 1000, UINT32_MAX, 0, 0},
        {1, 0, UINT32_MAX, 0, 0},
        {1, 100, UINT32_MAX, 0, 0},
        {9, 100, UINT32_MAX, 0, 0},
        {10, 100, UINT32_MAX, 1, 1},
        {11, 100, UINT32_MAX, 1, 1},
        {1000, 100, UINT32_MAX, 1, 100},
        {1, 1000, UINT32_MAX, 1, 1},
        {10, 128, UINT32_MAX, 1, 1},
        {65535, 1000, UINT16_MAX, 1, 65535},
        {65536, 1000, UINT16_MAX, 0, 0},
        {UINT32_MAX, 1000, UINT32_MAX, 1, UINT32_MAX},
        {UINT64_C(4294967296), 1000, UINT32_MAX, 0, 0},
        {UINT64_C(4294967297), 1000, UINT32_MAX, 0, 0},
        {UINT64_MAX, 2, UINT32_MAX, 0, 0},
        {UINT64_MAX, 1, UINT32_MAX, 0, 0},
        {1, 1000, 0, 0, 0},
        {1, UINT32_MAX, UINT32_MAX, 1, 4294967},
        {UINT32_MAX, 1, UINT32_MAX, 1, 4294967},
    };
    const uint32_t untouched = UINT32_C(0xa5a5a5a5);
    unsigned int i;
    for (i = 0; i < sizeof cases / sizeof cases[0]; ++i) {
        uint32_t out = untouched;
        int ok = period_ticks(cases[i].ms, cases[i].hz, cases[i].maximum, &out);
        uint32_t expected = cases[i].ok ? cases[i].ticks : untouched;
        if (ok != cases[i].ok || out != expected) {
            fprintf(stderr, "case %u: ok=%d out=%llu expected_ok=%d expected_out=%llu\n",
                    i, ok, (unsigned long long)out, cases[i].ok, (unsigned long long)expected);
            return 1;
        }
    }
    if (period_ticks(1, 1000, UINT32_MAX, NULL) != 0) return 1;
    puts("19 literal conversion/range cases and null-output rejection passed; host arithmetic only");
    return 0;
}
"""


class RtosPeriodMethodTests(unittest.TestCase):
    def setUp(self):
        self.compiler = shutil.which("cc")
        if self.compiler is None:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail("native C compiler required for period-method validation")
            self.skipTest("native C compiler unavailable")
        text = (ROOT / "skills/adk-rtos-task-design/SKILL.md").read_text(encoding="utf-8")
        matches = re.findall(r"<!-- adk-example: period-ticks -->\s*```c\n(.*?)\n```", text, re.S)
        self.assertEqual(1, len(matches), "missing or ambiguous published period example")
        self.published = matches[0]

    def execute(self, implementation):
        with tempfile.TemporaryDirectory(prefix="adk-period-test-") as directory:
            source, binary = Path(directory) / "period.c", Path(directory) / "period"
            source.write_text(implementation + "\n" + VECTORS, encoding="utf-8")
            built = subprocess.run([self.compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                                    str(source), "-o", str(binary)],
                                   capture_output=True, text=True, timeout=10)
            self.assertEqual(0, built.returncode, built.stdout + built.stderr)
            return subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)

    def test_published_example_rejects_zero_overflow_and_preserves_output(self):
        result = self.execute(self.published)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("19 literal conversion/range cases", result.stdout)

    def test_oracle_rejects_accepting_a_quantized_zero_period(self):
        needle = "if (!n || n > tick_max)"
        self.assertEqual(1, self.published.count(needle))
        mutant = self.published.replace(needle, "if (n > tick_max)")
        result = self.execute(mutant)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("case 2:", result.stderr)

    def test_oracle_rejects_narrowing_before_range_validation(self):
        needle = "uint64_t n = ms * hz / 1000u;"
        self.assertEqual(1, self.published.count(needle))
        mutant = self.published.replace(needle, "uint32_t n = (uint32_t)(ms * hz / 1000u);")
        result = self.execute(mutant)
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("case 13:", result.stderr)


if __name__ == "__main__":
    unittest.main()
