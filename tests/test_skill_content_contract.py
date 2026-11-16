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
            environment = {**os.environ, "PATH": str(binary), "LC_ALL": "C", "review_target": "staged"}
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

    def test_exported_review_snapshot_captures_selected_target_without_staging(self) -> None:
        """Exercise the shipped snapshot, including committed and mixed changes."""
        import os
        import re
        import shutil
        import subprocess
        import tempfile
        from agent_dev_kit.model import Manifest
        from agent_dev_kit.targets import load_target_contract, render_asset

        manifest = Manifest.load(ROOT)
        asset = next(item for item in manifest.all_assets("skill")
                     if item.name == "adk-code-review-loop")
        git, bash = shutil.which("git"), shutil.which("bash")
        self.assertIsNotNone(git)
        self.assertIsNotNone(bash)
        for runtime in ("claude-code", "opencode"):
            files = render_asset(manifest, load_target_contract(manifest, runtime), asset)
            reference = next(item for item in files if item.destination.endswith(
                "/references/review-evidence-template.md"))
            block = re.search(r"```bash\n(.*?)\n```", reference.content.decode(), re.DOTALL)
            self.assertIsNotNone(block)
            commands = block.group(1).split("<project-lint-cmd>", 1)[0]
            for scenario, review_target in (
                ("staged", "staged"), ("unstaged", "working-tree"),
                ("committed", "whole-branch"), ("mixed", "working-tree"),
            ):
                with self.subTest(runtime=runtime, scenario=scenario), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    target = root / "consumer"
                    target.mkdir()
                    binary = root / "bin"
                    binary.mkdir()
                    (binary / "git").symlink_to(git)
                    environment = {**os.environ, "PATH": str(binary), "LC_ALL": "C",
                                   "review_target": review_target}
                    environment.pop("review_base", None)

                    def checked(*args: str) -> str:
                        result = subprocess.run([git, *args], cwd=target, capture_output=True,
                                                text=True, timeout=10)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        return result.stdout

                    def commit(message: str) -> None:
                        checked("add", "fixture.py")
                        checked("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                                "commit", "-qm", message)

                    checked("init", "-q")
                    fixture = target / "fixture.py"
                    fixture.write_text("def dollars(cents):\n    return cents / 100\n", encoding="utf-8")
                    if scenario == "unstaged":
                        unchanged = target / "stat-only.txt"
                        unchanged.write_text("same content\n", encoding="utf-8")
                        checked("add", "stat-only.txt")
                        checked("config", "diff.autoRefreshIndex", "true")
                    commit("baseline")
                    baseline = checked("rev-parse", "HEAD").strip()
                    if scenario == "mixed":
                        fixture.write_text("def dollars(cents):\n    return cents / 100.0  # STAGED_ONLY\n",
                                           encoding="utf-8")
                        checked("add", "fixture.py")
                    fixture.write_text("def dollars(cents):\n    return cents / 1000  # TARGET_REGRESSION\n",
                                       encoding="utf-8")
                    if scenario == "staged":
                        checked("add", "fixture.py")
                    if scenario == "committed":
                        commit("branch change")
                        environment["review_base"] = baseline
                        self.assertEqual(checked("status", "--porcelain"), "")
                    if scenario == "unstaged":
                        (target / "untracked.py").write_text("UNTRACKED_BODY\n", encoding="utf-8")
                        previous = unchanged.stat()
                        unchanged.write_text("same content\n", encoding="utf-8")
                        os.utime(unchanged, ns=(previous.st_atime_ns, previous.st_mtime_ns + 2_000_000_000))
                    # Even a mixed tree must remain byte-for-byte unchanged by review.
                    index = target / ".git" / "index"
                    before_index = index.read_bytes()
                    before_source = fixture.read_bytes()
                    run = subprocess.run([bash, "--noprofile", "--norc", "-euc", commands],
                                         cwd=target, env=environment, capture_output=True,
                                         text=True, timeout=10)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    self.assertIn("+    return cents / 1000  # TARGET_REGRESSION", run.stdout)
                    self.assertIn("-    return cents / 100", run.stdout)
                    self.assertNotIn("+    return cents / 100.0  # STAGED_ONLY", run.stdout)
                    self.assertEqual(index.read_bytes(), before_index)
                    self.assertEqual(fixture.read_bytes(), before_source)
                    if scenario == "unstaged":
                        self.assertIn("?? untracked.py", run.stdout)
                        self.assertNotIn("UNTRACKED_BODY", run.stdout)
                    if scenario == "committed":
                        # Branch review must keep later dirty content separate from its patch.
                        fixture.write_text("def dollars(cents):\n    return 0  # LOCAL_OVERLAY\n",
                                           encoding="utf-8")
                        overlay = subprocess.run([bash, "--noprofile", "--norc", "-euc", commands],
                                                 cwd=target, env=environment, capture_output=True,
                                                 text=True, timeout=10)
                        self.assertEqual(overlay.returncode, 0, overlay.stdout + overlay.stderr)
                        self.assertIn(" M fixture.py", overlay.stdout)
                        self.assertIn("+    return cents / 1000  # TARGET_REGRESSION", overlay.stdout)
                        self.assertNotIn("LOCAL_OVERLAY", overlay.stdout)
                        self.assertEqual(index.read_bytes(), before_index)
                        for absent in ("", "refs/heads/unavailable-review-base"):
                            rejected = subprocess.run(
                                [bash, "--noprofile", "--norc", "-euc", commands], cwd=target,
                                env={**environment, "review_base": absent}, capture_output=True,
                                text=True, timeout=10)
                            self.assertNotEqual(rejected.returncode, 0, rejected.stdout)
                            self.assertNotIn("TARGET_REGRESSION", rejected.stdout)
                        self.assertEqual(index.read_bytes(), before_index)

    def test_exported_context_defaults_are_self_contained(self) -> None:
        """Inspect actual consumer packages, which intentionally omit ADK source aids."""
        import re
        import tempfile
        from agent_dev_kit.compiler import export_assets
        from agent_dev_kit.model import Manifest

        manifest = Manifest.load(ROOT)
        cases = {
            "adk-context-engineering": (
                "schemas/agent-handoff-v1.schema.json", "Objective / Phase"),
            "adk-context-compress-handoff": (
                "templates/context/continuity-attestation.md", "Latest Goal"),
        }
        required = {"Confirmed Facts", "State / Blockers", "Scope / Permission",
                    "Evidence / Fallback", "Next Actions"}
        with tempfile.TemporaryDirectory() as directory:
            for runtime in ("claude-code", "opencode"):
                exported = export_assets(manifest, runtime, Path(directory), ["core"])
                self.assertEqual(exported["status"], "pass")
                consumer = Path(exported["output"])
                for name, (source_aid, goal) in cases.items():
                    with self.subTest(runtime=runtime, skill=name):
                        skill = next(path for path in consumer.rglob("SKILL.md")
                                     if path.parent.name == name)
                        self.assertFalse((consumer / source_aid).exists())
                        self.assertFalse((skill.parent / source_aid).exists())
                        body = skill.read_text(encoding="utf-8")
                        # A source-only aid cannot be an unconditional instruction.
                        aid_line = next(line for line in body.splitlines() if source_aid in line)
                        self.assertIn("源码根已确认且文件可读", aid_line)
                        self.assertIn("默认使用下方模板", body)
                        template = body.split("## Evidence Template", 1)[1]
                        fields = set(re.findall(r"(?m)^- ([^:\n]+):", template))
                        self.assertTrue(required | {goal} <= fields, (name, fields))
                        self.assertIn("不扩大权限", body)

    def test_exported_parallel_worker_package_is_self_contained(self) -> None:
        """Resolve the published default from actual packages without ADK source aids."""
        import re
        import tempfile
        from agent_dev_kit.compiler import export_assets
        from agent_dev_kit.model import Manifest

        manifest = Manifest.load(ROOT)
        required = {"id", "goal", "owner", "work_item_kind", "implementation_permission",
                    "scope_read", "scope_write", "must_not_touch", "verification_commands",
                    "blocked_conditions", "report_schema", "context_noise_budget"}
        source_aid = "templates/planning/worker-contract.md"
        with tempfile.TemporaryDirectory() as directory:
            for runtime in ("claude-code", "opencode"):
                with self.subTest(runtime=runtime):
                    exported = export_assets(manifest, runtime, Path(directory), ["core"])
                    consumer = Path(exported["output"])
                    skill = next(path for path in consumer.rglob("SKILL.md")
                                 if path.parent.name == "adk-parallel-agent-governance")
                    body = skill.read_text(encoding="utf-8")
                    self.assertFalse((consumer / source_aid).exists())
                    self.assertFalse((skill.parent / source_aid).exists())
                    default = re.search(r"默认使用随包 `([^`]+)`", body)
                    self.assertIsNotNone(default, "default package must resolve in the export")
                    package = skill.parent / default.group(1)
                    self.assertTrue(package.is_file())
                    text = package.read_text(encoding="utf-8")
                    fields = set(re.findall(r"(?m)^([a-z_]+):", text))
                    self.assertTrue(required <= fields, required - fields)
                    aid_line = next(line for line in body.splitlines() if source_aid in line)
                    self.assertIn("源码根已核验且文件可读", aid_line)
                    self.assertIn("可选", aid_line)
                    helper = next(line for line in text.splitlines() if source_aid in line)
                    self.assertIn("optional", helper)
                    self.assertIn("verified ADK source root", helper)
                    self.assertIn("file exists", helper)
                    checklist = package.parent / "subagent-review-checklist.md"
                    self.assertTrue(checklist.is_file())

    def test_feedback_snapshot_uses_readonly_canonical_commands(self) -> None:
        """A secondary shipped example must not refresh the real Git index."""
        import os
        import re
        import shutil
        import subprocess
        import tempfile
        from agent_dev_kit.model import Manifest
        from agent_dev_kit.targets import load_target_contract, render_asset

        manifest = Manifest.load(ROOT)
        asset = next(item for item in manifest.all_assets("skill")
                     if item.name == "adk-code-review-loop")
        bash = shutil.which("bash")
        self.assertIsNotNone(bash)
        for runtime in ("claude-code", "opencode"):
            with self.subTest(runtime=runtime), tempfile.TemporaryDirectory() as directory:
                files = render_asset(manifest, load_target_contract(manifest, runtime), asset)
                feedback = next(item for item in files
                                if item.destination.endswith("/references/review-feedback-fixtures.md"))
                text = feedback.content.decode()
                link = re.search(r"\[[^\]]+\]\((review-evidence-template\.md)(?:#[^)]*)?\)", text)
                if link is not None:
                    destination = (Path(feedback.destination).parent / link.group(1)).as_posix()
                    text = next(item.content.decode() for item in files
                                if item.destination == destination)
                # Baseline fallback executes its old published block, exposing the mutation.
                block = re.search(r"```bash\n(.*?)\n```", text, re.DOTALL)
                self.assertIsNotNone(block)
                commands = block.group(1).split("<project-", 1)[0].replace("<path>", "fixture.txt")
                target = Path(directory)
                subprocess.run(["git", "init", "-q", str(target)], check=True)
                fixture = target / "fixture.txt"
                fixture.write_text("unchanged content\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(target), "add", "fixture.txt"], check=True)
                subprocess.run(["git", "-C", str(target), "-c", "user.name=Test",
                                "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"],
                               check=True)
                info = fixture.stat()
                os.utime(fixture, ns=(info.st_atime_ns, info.st_mtime_ns + 3_000_000_000))
                index = target / ".git/index"
                before = index.read_bytes()
                run = subprocess.run([bash, "--noprofile", "--norc", "-euc", commands], cwd=target,
                                     env={**os.environ, "LC_ALL": "C", "review_target": "working-tree"},
                                     capture_output=True, text=True, timeout=10)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertEqual(index.read_bytes(), before, "published snapshot changed the index")
                self.assertEqual(fixture.read_text(encoding="utf-8"), "unchanged content\n")
                self.assertIsNotNone(link, "secondary examples must reuse the canonical snapshot")

    def test_growth_scope_metadata_matches_bounded_body(self) -> None:
        """Source consistency only; no model reading-cost claim."""
        skill = ROOT / "skills/adk-engineering-growth-review"
        content = (skill / "SKILL.md").read_text(encoding="utf-8")
        _, header, body = content.split("---", 2)
        constraints = "\n".join(yaml.safe_load(header)["constraints"])
        for label, surface in (("metadata", constraints), ("body", body),
                               ("readme", (skill / "README.md").read_text(encoding="utf-8"))):
            with self.subTest(surface=label):
                self.assertNotIn("允许本地宽读", surface)
                self.assertNotIn("不限制单一项目", surface)
                for term in ("index-first", "已授权", "跨项目", "明确"):
                    self.assertIn(term, surface)

    def test_fetch_parent_preserves_child_result_states(self) -> None:
        """Check the shipped result contract, not a real network/IMAP fetch."""
        import re

        directory = ROOT / "optional-skills/adk-data-fetch"
        statuses = r"pass|partial|needs-fix|not-verified"
        children = set()
        for name in ("adk-fetch-url-content", "adk-email-imap-fetch"):
            source = (directory / name / "SKILL.md").read_text(encoding="utf-8")
            declared = re.search(r"(?m)^- (?:获取|提取)状态: (.+)$", source)
            self.assertIsNotNone(declared)
            children.update(re.findall(statuses, declared.group(1)))
        self.assertEqual(children, {"pass", "partial", "needs-fix", "not-verified"})
        parent = (directory / "SKILL.md").read_text(encoding="utf-8")
        mapping = dict(re.findall(r"(?m)^\| (" + statuses + r") \| (" + statuses + r") \|$", parent))
        self.assertEqual(set(mapping), children)
        for child_status in children:
            self.assertEqual(mapping[child_status], child_status)
        template = parent.split("## Evidence Template", 1)[1].split("## ", 1)[0]
        for field in ("已取得内容", "未取得范围与原因", "逐项错误"):
            self.assertIn(field, template)
        self.assertIn("缺少子 Skill 时必须停止", parent)

    def test_archive_unknown_hash_mismatch_keeps_original_evidence(self) -> None:
        """Static recovery guidance; this does not replay a production archive incident."""
        source = (ROOT / "skills/adk-archive-governance/SKILL.md").read_text(encoding="utf-8")
        guidance = next((line for line in source.splitlines()
                         if "hash mismatch" in line and "可信" in line), "")
        for term in ("旧 hash", "实测 hash", "可信原件", "已批准", "未知", "needs-fix"):
            self.assertIn(term, guidance)
        self.assertLess(guidance.index("旧 hash"), guidance.index("已批准"))
        self.assertNotIn("登记 topic、更新 hash", source)

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
