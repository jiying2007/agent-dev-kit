"""Bulk Skill trigger matrix plus one real CLI smoke without shared temp files."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from agent_dev_kit._matcher_kernel import _frontmatter
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



CATALOG_CASES = ROOT / "tests/fixtures/skill_catalog_competition.tsv"


def _catalog_cases() -> list[tuple[int, str, str, str, str, str]]:
    lines = CATALOG_CASES.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "case_id\tkind\texpected_skill\tcompetitor\tinput":
        raise AssertionError("Skill catalog competition header is invalid")
    cases: list[tuple[int, str, str, str, str, str]] = []
    identifiers: set[str] = set()
    for line_number, line in enumerate(lines[1:], start=2):
        fields = line.split("\t", 4)
        if len(fields) != 5:
            raise AssertionError("Skill catalog competition line {} has invalid columns".format(line_number))
        identifier, kind, expected, competitor, prompt = fields
        if (
            not identifier or identifier in identifiers
            or kind not in ("primary", "collision", "negated", "abstain")
            or not expected or not competitor or not prompt.strip()
        ):
            raise AssertionError("Skill catalog competition line {} has invalid values".format(line_number))
        if kind in ("negated", "abstain") and expected != "-":
            raise AssertionError("Abstention cases must not name a primary Skill")
        if kind in ("collision", "negated") and competitor == "-":
            raise AssertionError("Competition and negation cases require a competitor")
        identifiers.add(identifier)
        cases.append((line_number, identifier, kind, expected, competitor, prompt))
    if len(cases) < 20 or {item[2] for item in cases} != {"primary", "collision", "negated", "abstain"}:
        raise AssertionError("Skill catalog competition coverage has regressed")
    return cases


class SkillTriggerMatrixTests(unittest.TestCase):
    def test_all_cases_match_once_loaded_manifest(self) -> None:
        manifest = Manifest.load(ROOT)
        for line_number, skill, scope, expected, prompt in _cases():
            with self.subTest(line=line_number, skill=skill, scope=scope):
                actual = match_text(manifest, prompt, skill=skill, scope=scope).get("match") is True
                self.assertEqual(actual, expected)


    def test_source_only_routing_inventory_has_minimum_case_coverage(self) -> None:
        # These are deterministic matcher tests, never native runtime/effect evidence.
        isolated = _cases()
        competition = _catalog_cases()
        self.assertGreaterEqual(len(isolated) + len(competition), 100)
        self.assertIn(True, {case[3] for case in isolated})
        self.assertIn(False, {case[3] for case in isolated})
        self.assertEqual({case[2] for case in competition},
                         {"primary", "collision", "negated", "abstain"})

    def test_cli_smoke_uses_same_contract(self) -> None:
        _, skill, scope, _, prompt = next(item for item in _cases() if item[3])
        completed = subprocess.run(
            ["bash", str(ROOT / "scripts/devkit.sh"), "match", "--skill", skill, "--scope", scope, "--text", prompt],
            cwd=str(ROOT), check=False, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)



    def test_catalog_auto_selection_and_abstention(self) -> None:
        manifest = Manifest.load(ROOT)
        for line, identifier, kind, expected, competitor, prompt in _catalog_cases():
            with self.subTest(line=line, case=identifier, kind=kind):
                # Use the production public matcher across the *whole* catalog;
                # never substitute per-Skill scoring or a fixture-only selector.
                result = match_text(manifest, prompt, scope="auto")
                if expected == "-":
                    self.assertIs(result.get("match"), False, result)
                    self.assertEqual(result.get("decision"), "abstain", result)
                    self.assertEqual(result.get("mutation_permission"), "deny", result)
                else:
                    self.assertIs(result.get("match"), True, result)
                    self.assertEqual(result.get("skill"), expected, result)
                    self.assertEqual(result.get("runtime_role"), "primary", result)
                if competitor != "-":
                    self.assertNotEqual(result.get("skill"), competitor, result)
                    explicit = match_text(manifest, prompt, skill=competitor, scope="skill")
                    if kind == "collision":
                        # The losing Skill really could have matched, so this
                        # proves automatic selection rather than a trivial hit.
                        self.assertIs(explicit.get("match"), True, explicit)
                    elif kind == "negated":
                        self.assertIs(explicit.get("match"), False, explicit)


    def test_portable_description_discovery_boundaries(self) -> None:
        """Only source metadata preflight; never native host routing evidence."""
        manifest = Manifest.load(ROOT)
        entries = {
            item["name"]: item["path"]
            for section in ("skills", "optional_skills")
            for item in manifest.data[section]
        }
        pairs = (
            ("adk-requirements-triage", "adk-lightweight-planning", ("需求不清", "验收"), "已明确", "需求不清"),
            ("adk-unit-test-embedded", "adk-test-strategy", ("单元测试", "断言"), "非", "断言"),
            ("adk-performance-profiling-embedded", "adk-code-simplification", ("性能分析", "真实负载"), "无指标", "真实负载"),
            ("adk-archive-governance", "adk-knowledge-archive", ("检查", "元数据"), "不负责", "检查"),
            ("adk-knowledge-archive", "adk-archive-governance", ("新建", "归档候选"), "不处理", "归档候选"),
            ("adk-task-breakdown", "adk-lightweight-planning", ("拆解", "并行边界"), "无需", "并行边界"),
            ("adk-commit-pr-quality-gate", "adk-code-review-loop", ("提交 PR", "测试证据"), "不能替代", "测试证据"),
            ("adk-release-versioning", "adk-embedded-release-orchestration", ("版本号", "发布基线"), "不执行", "Changelog"),
        )
        for owner, neighbor, signals, exclusion, distinct_signal in pairs:
            with self.subTest(owner=owner, neighbor=neighbor):
                own = _frontmatter(ROOT / entries[owner])
                other = _frontmatter(ROOT / entries[neighbor])
                self.assertEqual(own["name"], owner)
                self.assertEqual(other["name"], neighbor)
                description = own["description"]
                self.assertIsInstance(description, str)
                self.assertGreater(len(description.strip()), 10)
                self.assertLessEqual(len(description), 1024)
                for signal in signals:
                    self.assertIn(signal, description, (owner, signal))
                self.assertIn(exclusion, description, owner)
                self.assertNotIn(distinct_signal, other["description"], (owner, neighbor))


    def test_full_inventory_description_and_isolated_trigger_contract(self) -> None:
        """All declared Skills have both discovery boundaries and executable isolated match cases.

        This exercises the deterministic ADK matcher, not native host discovery or task success.
        """
        manifest = Manifest.load(ROOT)
        seen = set()
        for section, scope in (("skills", "skill"), ("optional_skills", "optional-skill")):
            for item in manifest.data[section]:
                name = item["name"]
                with self.subTest(name=name, scope=scope):
                    self.assertNotIn(name, seen)
                    seen.add(name)
                    metadata = _frontmatter(ROOT / item["path"])
                    self.assertEqual(metadata.get("name"), name)
                    description = metadata.get("description")
                    self.assertIsInstance(description, str)
                    self.assertGreaterEqual(len(description.strip()), 30)
                    self.assertLessEqual(len(description), 1024)
                    self.assertTrue(
                        any(marker in description for marker in ("用于", "适用", "面向")),
                        (name, "missing use-when language"),
                    )
                    self.assertTrue(
                        any(marker in description for marker in
                            ("不用于", "不负责", "不处理", "不执行", "不能替代", "无需", "不自动")),
                        (name, "missing exclusion language"),
                    )
                    positives = metadata.get("triggers")
                    negatives = metadata.get("non_triggers")
                    self.assertIsInstance(positives, list)
                    self.assertIsInstance(negatives, list)
                    self.assertTrue(positives)
                    self.assertTrue(negatives)
                    self.assertTrue(all(isinstance(value, str) and value.strip() for value in positives))
                    self.assertTrue(all(isinstance(value, str) and value.strip() for value in negatives))
                    positive = match_text(manifest, positives[0], skill=name, scope=scope)
                    negative = match_text(manifest, negatives[0], skill=name, scope=scope)
                    self.assertIs(positive.get("match"), True, (name, "positive", positive))
                    self.assertIs(negative.get("match"), False, (name, "negative", negative))
        self.assertEqual(len(seen), len(manifest.data["skills"]) + len(manifest.data["optional_skills"]))

    def test_repo_drift_local_commands_refer_to_real_scripts(self) -> None:
        """Reject stale in-repository script references without guessing target project paths."""
        import re

        content = (ROOT / "skills/adk-repo-drift-remediation/SKILL.md").read_text(encoding="utf-8")
        commands = content.split("## Commands", 1)[1].split("## Evidence Template", 1)[0]
        paths = re.findall(r"\brtk bash (scripts/[A-Za-z0-9_-]+\.sh)\b", commands)
        self.assertTrue(paths)
        for relative in paths:
            with self.subTest(script=relative):
                self.assertTrue((ROOT / relative).is_file(), relative)


    def test_interactive_discovery_modes_and_routing(self) -> None:
        """Source-only routing/contract checks, not native E2/E4 evidence."""
        import json

        manifest = Manifest.load(ROOT)
        corpus = json.loads((ROOT / "tests/fixtures/interactive_discovery_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(corpus["schema"], "adk-interactive-discovery-cases/v1")
        self.assertEqual(corpus["evidence_layer"], "source-test")
        self.assertGreaterEqual(len(corpus["cases"]), 8)
        skill = (ROOT / "skills/adk-structured-requirements-questioning/SKILL.md").read_text(encoding="utf-8")
        metadata = _frontmatter(ROOT / "skills/adk-structured-requirements-questioning/SKILL.md")
        contract = json.loads((ROOT / "manifests/skill_content_contracts_v2.json").read_text(encoding="utf-8"))
        definition = contract["overrides"]["adk-structured-requirements-questioning"]
        self.assertEqual(definition["runtime_role"], "primary")
        self.assertEqual(definition["effect_ceiling"], "read-only")
        self.assertIn("brainstorm", metadata["description"].lower())
        self.assertIn("Grill Me", metadata["description"])
        for marker in ("Explore protocol", "Challenge protocol", "Frontier", "Look before asking",
                       "User-confirmed decisions", "Cross-mode convergence"):
            self.assertIn(marker, skill)
        for case in corpus["cases"]:
            with self.subTest(case=case["id"]):
                result = match_text(manifest, case["prompt"], scope="auto")
                if case["expected_primary"] is None:
                    self.assertIs(result.get("match"), False, result)
                else:
                    self.assertIs(result.get("match"), True, result)
                    self.assertEqual(result.get("skill"), case["expected_primary"], result)
                self.assertEqual(result.get("mutation_permission"), case["expected_mutation"], result)
                self.assertTrue(case["behavior_obligation"].strip())

if __name__ == "__main__":
    unittest.main()
