"""Skill content v2 checks without obsolete line-count or fixed-heading constraints."""
from __future__ import annotations
import json
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


class SkillContentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

    def test_all_registered_skill_frontmatter_and_body(self) -> None:
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        self.assertEqual(len({item["name"] for item in items}), len(items))
        for item in items:
            path = ROOT / item["path"]
            with self.subTest(path=item["path"]):
                content = path.read_text(encoding="utf-8")
                self.assertTrue(content.startswith("---\n"))
                _, header, body = content.split("---", 2)
                meta = yaml.safe_load(header)
                self.assertIsInstance(meta, dict)
                self.assertEqual(meta.get("name"), item["name"])
                self.assertTrue(isinstance(meta.get("description"), str) and meta["description"].strip())
                self.assertLessEqual(len(meta["description"]), 1024)
                self.assertTrue(body.strip())
                self.assertTrue(isinstance(meta.get("triggers"), list) and meta["triggers"])
                self.assertIsInstance(meta.get("non_triggers"), list)

    def test_registered_skill_markdown_fences_closed(self) -> None:
        """Regression for a real unclosed shell fence in interface-contract-design."""
        def balanced(text: str) -> bool:
            open_fence = False
            for line in text.splitlines():
                if line.lstrip().startswith("```"):
                    open_fence = not open_fence
            return not open_fence

        self.assertFalse(balanced("## Example\n```bash\necho one\n"))
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        for item in items:
            with self.subTest(skill=item["name"]):
                source = (ROOT / item["path"]).read_text(encoding="utf-8")
                self.assertTrue(balanced(source), item["path"])

    def test_skill_method_cases_are_not_fabricated_model_results(self) -> None:
        fixture = json.loads((ROOT / "tests/fixtures/skill_method_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(fixture["schema"], "adk-skill-method-review-cases/v1")
        self.assertEqual(fixture["behavior_status"], "not-measured")
        cases = fixture["cases"]
        self.assertGreaterEqual(len(cases), 8)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        expected = {"debug-feedback", "tdd-public-seam", "architecture-deep-module",
                    "domain-counterexample", "tracer-slice", "throwaway-prototype",
                    "skill-red-green", "approval-negative"}
        self.assertTrue(expected <= {c["id"] for c in cases})
        for case in cases:
            self.assertIn(case["mode"], {"positive", "negative", "adversarial"})
            for field in ("prompt", "target_skill", "expected_behavior", "reject_behavior"):
                self.assertTrue(isinstance(case[field], str) and case[field].strip(), (case["id"], field))
        refs = [
            "skills/adk-interface-contract-design/references/design-quality-methods.md",
            "skills/adk-code-simplification/references/deep-module-design.md",
            "skills/adk-systematic-debugging/references/tight-feedback-loop.md",
            "skills/adk-test-strategy/references/high-value-tdd.md",
            "skills/adk-task-breakdown/references/vertical-slice-planning.md",
            "skills/adk-structured-requirements-questioning/references/prototype-as-experiment.md",
            "optional-skills/adk-skill-composition-governance/references/skill-behavior-evaluation.md",
            "docs/evals/skill-method-parity.md",
        ]
        for path in refs:
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn("not-measured", (ROOT / "docs/evals/skill-method-parity.md").read_text(encoding="utf-8"))

    def test_no_language_duplicate_skill_and_counts_match(self) -> None:
        names = {v["name"] for t in ("skills", "optional_skills") for v in self.manifest[t]}
        self.assertFalse(any(n.startswith(("adk-chinese-", "adk-english-")) for n in names))
        for n in ("adk-chinese-code-review", "adk-chinese-commit-conventions"):
            self.assertFalse((ROOT / "skills" / n).exists())
        policy = json.loads((ROOT / "manifests/content_architecture_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(len(self.manifest["skills"]), policy["identity_baseline"]["core_skill_count"])
        self.assertEqual(len(self.manifest["optional_skills"]), policy["identity_baseline"]["optional_skill_count"])


    def test_review_skill_entries_have_real_goal_and_no_placeholder(self) -> None:
        # Targeted regression for reviewed defects, not a new global heading/length gate.
        for name in ("adk-repo-prompt-analysis", "adk-skill-deep-analysis"):
            with self.subTest(skill=name):
                content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                body = content.split("---", 2)[2]
                self.assertEqual(body.count("## Goal\n"), 1)
                self.assertNotIn("## Goal\n## Prerequisites", body)
                self.assertNotIn("<what-to-do>", body)
                self.assertNotIn("</what-to-do>", body)
                self.assertNotIn("<supporting-info>", body)
                self.assertNotIn("</supporting-info>", body)
                self.assertIn("## Workflow", body)
        skill = (ROOT / "skills/adk-skill-deep-analysis/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("# Skill 设计深度审查", skill)


    def test_all_skill_shell_references_use_declared_adk_commands(self) -> None:
        import re
        from agent_dev_kit.cli_runtime import PUBLIC_COMMANDS

        allowed = {command for command, _ in PUBLIC_COMMANDS}
        items = [*self.manifest["skills"], *self.manifest["optional_skills"]]
        for item in items:
            text = (ROOT / item["path"]).read_text(encoding="utf-8")
            blocks = re.findall(r"```(?:bash|sh)\n([\s\S]*?)\n```", text)
            with self.subTest(skill=item["name"]):
                for block in blocks:
                    for command in re.findall(r"scripts/devkit\.sh\s+([a-z][a-z-]*)", block):
                        self.assertIn(command, allowed, (item["name"], command))
                    for script in re.findall(
                        r"(?m)^(?:rtk\s+)?(?:bash|python3?)\s+(scripts/[A-Za-z0-9_./-]+\.(?:sh|py))\b",
                        block,
                    ):
                        self.assertTrue((ROOT / script).is_file(), (item["name"], script))
                self.assertNotRegex(text, r"devkit\.sh\s+verify\s+--analysis")

    def test_exported_review_commands_run_without_optional_wrapper(self) -> None:
        """Exercise shipped instructions in a target repo without ADK or rtk."""
        import os
        import re
        import shutil
        import subprocess
        import tempfile
        from agent_dev_kit.model import Manifest
        from agent_dev_kit.targets import load_target_contract, render_asset

        manifest = Manifest.load(ROOT)
        contract = load_target_contract(manifest, "claude-code")
        asset = next(item for item in manifest.all_assets("skill")
                     if item.name == "adk-code-review-loop")
        files = render_asset(manifest, contract, asset)
        reference = next(item for item in files
                         if item.destination.endswith("/references/review-evidence-template.md"))
        block = re.search(r"```bash\n(.*?)\n```", reference.content.decode(), re.DOTALL)
        self.assertIsNotNone(block)
        commands = block.group(1).split("<project-lint-cmd>", 1)[0]
        self.assertIn("git rev-parse HEAD", commands)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            subprocess.run(["git", "init", "-q", str(target)], check=True)
            subprocess.run(["git", "-C", str(target), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "commit", "-qm",
                            "fixture", "--allow-empty"], check=True)
            binary = target / "bin"
            binary.mkdir()
            git = shutil.which("git")
            bash = shutil.which("bash")
            self.assertIsNotNone(git)
            self.assertIsNotNone(bash)
            (binary / "git").symlink_to(git)
            environment = {**os.environ, "PATH": str(binary), "LC_ALL": "C"}
            self.assertIsNone(shutil.which("rtk", path=environment["PATH"]))
            run = subprocess.run([bash, "--noprofile", "--norc", "-euc", commands],
                                 cwd=target, env=environment, capture_output=True,
                                 text=True, timeout=10)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertRegex(run.stdout.splitlines()[0], r"^[0-9a-f]{40,64}$")

    def test_distributed_skill_commands_have_no_undeclared_rtk_requirement(self) -> None:
        import re
        from agent_dev_kit.model import Manifest
        from agent_dev_kit.targets import load_target_contract, render_asset

        manifest = Manifest.load(ROOT)
        contract = load_target_contract(manifest, "claude-code")
        assets = manifest.all_assets("skill")  # Includes core and optional assets.
        self.assertTrue(any(asset.optional for asset in assets))
        for asset in assets:
            for rendered in render_asset(manifest, contract, asset):
                if not rendered.destination.endswith(".md"):
                    continue
                for block in re.findall(r"```(?:bash|sh)\n(.*?)\n```",
                                        rendered.content.decode(), re.DOTALL):
                    self.assertNotRegex(block, r"(?m)^\s*rtk\s+", rendered.destination)

    def test_fault_injection_defaults_never_write_live_device(self) -> None:
        import re

        text = (ROOT / "skills/adk-fault-injection-recovery/SKILL.md").read_text(encoding="utf-8")
        section = text.split("## Commands", 1)[1].split("## Evidence Template", 1)[0]
        for pattern in (
            r"(?m)^\s*echo\s+.*>\s*/sys/kernel/debug",
            r"(?m)^\s*echo\s+.*>\s*/dev/watchdog",
            r"(?m)^\s*stress-ng\s+.*--vm",
        ):
            self.assertIsNone(re.search(pattern, section))
        self.assertIn("独立设备操作者", section)
        self.assertIn("not_evaluated", section)

    def test_aar_templates_follow_standalone_skill_and_references_are_balanced(self) -> None:
        aar = ROOT / "skills/adk-after-action-review"
        instructions = (aar / "SKILL.md").read_text(encoding="utf-8")
        for name, canonical in (
            ("memory-candidate.md", "templates/memory/memory-candidate.md"),
            ("after-action-review.md", "templates/memory/after-action-review.md"),
            ("codify-decision.md", "templates/governance/codify-decision.md"),
        ):
            self.assertIn("references/" + name, instructions)
            self.assertEqual((aar / "references" / name).read_bytes(), (ROOT / canonical).read_bytes())
        details = ROOT / "skills/adk-pilot-framework/references/details.md"
        self.assertEqual(
            sum(line.lstrip().startswith("```") for line in details.read_text(encoding="utf-8").splitlines()) % 2,
            0,
        )

    def test_details_are_supplemental_not_duplicate_skills(self) -> None:
        for parent in ("skills", "optional-skills"):
            for path in ROOT.glob(parent + "/*/references/details.md"):
                with self.subTest(path=path.relative_to(ROOT)):
                    content = path.read_text(encoding="utf-8")
                    self.assertFalse(content.startswith("---\n"))
                    self.assertNotIn("## Workflow\n", content)
