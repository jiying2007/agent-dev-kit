"""Execute domain formulas published in Skills against independent examples."""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RegisterResetExpressionTests(unittest.TestCase):
    def test_published_reset_formula_distinguishes_defined_and_undefined_bits(self):
        compiler = shutil.which("cc")
        if compiler is None:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                self.fail("native C compiler required for domain expression validation")
            self.skipTest("native C compiler unavailable")
        text = (ROOT / "skills/adk-register-map-design/SKILL.md").read_text()
        expressions = [value for value in re.findall(r"`([^`\n]+)`", text)
                       if all(name in value for name in ("observed", "expected", "known_mask"))]
        self.assertEqual(1, len(expressions), expressions)
        code = r"""
#include <stdint.h>
#include <stdio.h>
int main(void) {
    const uint32_t cases[][4] = {
        /* observed, expected, defined-bit mask, expected comparison */
        {0x0503u, 0x0503u, 0x0f0fu, 1u},
        {0x8503u, 0x0503u, 0x0f0fu, 1u},
        {0x850bu, 0x0503u, 0x0f0fu, 0u},
        {0x80000000u, 0u, 0x80000000u, 0u},
        {0x7fffffffu, 0u, 0x80000000u, 1u},
        {0xffffffffu, 0xffffffffu, 0xffffffffu, 1u},
    };
    unsigned int index;
    for (index = 0; index < sizeof cases / sizeof cases[0]; ++index) {
        uint32_t observed = cases[index][0];
        uint32_t expected = cases[index][1];
        uint32_t known_mask = cases[index][2];
        int actual = EXPRESSION;
        if (actual != (int)cases[index][3]) {
            fprintf(stderr, "case %u: actual=%d expected=%u\n", index, actual, cases[index][3]);
            return 1;
        }
    }
    puts("six defined-bit comparisons passed; no hardware access");
    return 0;
}
""".replace("EXPRESSION", expressions[0])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, binary = root / "reset.c", root / "reset"
            source.write_text(code)
            built = subprocess.run([compiler, "-std=c99", "-Wall", "-Wextra", "-pedantic",
                                    str(source), "-o", str(binary)],
                                   capture_output=True, text=True, timeout=10)
            self.assertEqual(0, built.returncode, built.stdout + built.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("six defined-bit comparisons passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
