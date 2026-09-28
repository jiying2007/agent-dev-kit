"""Bulk Skill trigger matrix plus one real CLI smoke without shared temp files."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "tests/fixtures/skill_trigger_cases.tsv"


def _cases() -> list[tuple[int, str, str, bool, str]]:
    lines = CASES.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "skill\tscope\texpected\tinput":
        raise AssertionError("Skill trigger matrix header is invalid")
    parsed: list[tuple[int, str, str, bool, str]] = []
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t", 3)
        if len(fields) != 4:
            raise AssertionError("Skill trigger matrix line {} has invalid columns".format(line_number))
        skill, scope, expected, prompt = fields
        if not skill or scope not in ("auto", "skill", "optional-skill") or expected not in ("0", "1") or not prompt:
            raise AssertionError("Skill trigger matrix line {} has invalid labels".format(line_number))
        parsed.append((line_number, skill, scope, expected == "1", prompt))
    if not parsed:
        raise AssertionError("Skill trigger matrix has no cases")
    return parsed


class SkillTriggerMatrixTests(unittest.TestCase):
    def test_all_cases_match_once_loaded_manifest(self) -> None:
        manifest = Manifest.load(ROOT)
        for line_number, skill, scope, expected, prompt in _cases():
            with self.subTest(line=line_number, skill=skill, scope=scope):
                actual = match_text(manifest, prompt, skill=skill, scope=scope).get("match") is True
                self.assertEqual(actual, expected)

    def test_cli_smoke_uses_same_contract(self) -> None:
        _, skill, scope, _, prompt = next(item for item in _cases() if item[3])
        completed = subprocess.run(
            ["bash", str(ROOT / "scripts/devkit.sh"), "match", "--skill", skill, "--scope", scope, "--text", prompt],
            cwd=str(ROOT), check=False, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)


if __name__ == "__main__":
    unittest.main()
