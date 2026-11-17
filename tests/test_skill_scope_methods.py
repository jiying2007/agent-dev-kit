"""Exercise published scan/export paths; source checks do not certify model behavior."""
from __future__ import annotations

import glob
import json
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

import yaml

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
COMPOSITION = ROOT / "optional-skills/adk-skill-composition-governance/SKILL.md"
ARTIFACT = ROOT / "skills/adk-artifact-gating/references/details.md"


class PublishedSkillScopeMethodsTests(unittest.TestCase):
    def test_published_trigger_scan_covers_the_manifest_including_nested_skills(self):
        commands = [line for line in COMPOSITION.read_text().splitlines()
                    if line.startswith("rg ") and "triggers:" in line]
        self.assertEqual(1, len(commands))
        # Expand the shell's glob arguments without interpreting shell operators.
        arguments = []
        for argument in shlex.split(commands[0]):
            matches = glob.glob(argument, root_dir=ROOT) if glob.has_magic(argument) else []
            arguments.extend(sorted(matches) or [argument])
        self.assertEqual("rg", arguments[0])
        observed = subprocess.run(arguments, cwd=ROOT, capture_output=True,
                                  text=True, timeout=10)
        self.assertEqual(0, observed.returncode, observed.stderr)
        paths = {line.split(":", 1)[0] for line in observed.stdout.splitlines()}
        manifest = json.loads((ROOT / "manifest.json").read_text())
        expected = {item["path"] for field in ("skills", "optional_skills")
                    for item in manifest[field]}
        self.assertEqual(expected, paths, "the published command must include nested children")
        optional = {item["path"] for item in manifest["optional_skills"]}
        self.assertEqual(optional, {path for path in paths if path.startswith("optional-skills/")})

    def test_real_team_exports_scope_nonbundled_root_helpers(self):
        manifest = Manifest.load(ROOT)
        with tempfile.TemporaryDirectory(prefix="adk-skill-scope-") as directory:
            for target in ("claude-code", "opencode"):
                with self.subTest(target=target):
                    result = export_assets(manifest, target, Path(directory), ["team-core"])
                    self.assertEqual("pass", result["status"])
                    output = Path(result["output"])
                    skill, = [path for path in output.rglob("SKILL.md")
                              if path.parent.name == "adk-artifact-gating"]
                    reference = skill.parent / "references/details.md"
                    self.assertEqual(ARTIFACT.read_bytes(), reference.read_bytes())
                    self.assertEqual([], list(output.rglob("check-adk-harden-readiness.sh")))
                    text = reference.read_text()
                    cross_repo = text.split("### 5.", 1)[1]
                    helper_lines = [line for line in cross_repo.splitlines()
                                    if "check-adk-harden-readiness.sh" in line]
                    self.assertEqual(1, len(helper_lines))
                    self.assertRegex(helper_lines[0], r"仅.{0,12}llm_agent Root")
                    self.assertIn("已核验", cross_repo)
                    self.assertIn("项目门禁", cross_repo)
                    self.assertIn("BLOCKED", cross_repo)

    def test_perf_generic_event_has_no_universal_llc_label(self):
        text = (ROOT / "skills/adk-performance-profiling-embedded/SKILL.md").read_text()
        # Linux v6.12 ARM PMUv3 maps generic CACHE_MISSES to L1D refill,
        # so the former universal LLC label is invalid even for a valid count.
        self.assertNotIn("LLC miss 用 perf stat -e cache-misses", text)
        counter_line, = [line for line in text.splitlines() if "cache-misses" in line]
        for evidence in ("CPU", "PMU", "内核", "LLC", "unavailable"):
            self.assertIn(evidence, counter_line)
        self.assertRegex(counter_line, r"cache-misses.{0,60}不默认等同 LLC")

    def test_growth_metadata_limits_promotion_to_persistent_assets(self):
        text = (ROOT / "skills/adk-engineering-growth-review/SKILL.md").read_text()
        metadata = yaml.safe_load(text.split("---", 2)[1])
        constraint, = [line for line in metadata["constraints"]
                       if "trace-feedback-eval-handoff" in line]
        self.assertTrue(constraint.startswith("仅"), constraint)
        self.assertIn("晋级", constraint)
        self.assertNotIn("改进建议进入执行层前必须", constraint)
        workflow = text.split("## Workflow", 1)[1].split("## Output", 1)[0]
        promotion, = [line for line in workflow.splitlines()
                      if "trace-feedback-eval-handoff" in line]
        self.assertRegex(promotion, r"^\d+\.\s*仅")
        for asset in ("prompt", "Skill", "Workflow", "AGENTS", "记忆"):
            self.assertIn(asset, constraint.split("晋级", 1)[0])
            self.assertIn(asset, promotion.split("时输出", 1)[0])
        self.assertIn("普通建议不需晋级", promotion)
        self.assertIn("修改仍按原任务授权", promotion)


if __name__ == "__main__":
    unittest.main()
