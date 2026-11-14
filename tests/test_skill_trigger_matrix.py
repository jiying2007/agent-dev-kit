"""Bulk Skill trigger matrix plus one real CLI smoke without shared temp files."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from agent_dev_kit._matcher_kernel import _frontmatter
from agent_dev_kit.matcher import format_result, match_text
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
        optional_names = {item["name"] for item in manifest.data["optional_skills"]}
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
                    competitor_scope = "optional-skill" if competitor in optional_names else "skill"
                    explicit = match_text(manifest, prompt, skill=competitor, scope=competitor_scope)
                    if kind == "collision":
                        # The losing Skill really could have matched, so this
                        # proves automatic selection rather than a trivial hit.
                        self.assertIs(explicit.get("match"), True, explicit)
                    elif kind == "negated":
                        self.assertIs(explicit.get("match"), False, explicit)



    def test_optional_skill_is_not_implicitly_installed_by_a_catalog_hit(self) -> None:
        """Production matcher: routed and lexical Optional matches both need installation.

        Static catalog routing is not proof that the current target runtime
        contains the selected optional asset.  This tests the public structured
        response and the human-facing CLI formatter, not a native host install.
        """
        manifest = Manifest.load(ROOT)
        optional = "adk-external-practice-absorption"
        for prompt, source in (
            ("请评估参考实现，并吸收外部实践中的设计方法", "routing"),
            ("继续吸收外部成熟方法，提升已有 Skills 的实际执行效果",
             "optional_skill_trigger"),
        ):
            with self.subTest(prompt=prompt):
                result = match_text(manifest, prompt, scope="auto")
                self.assertIs(result.get("match"), True, result)
                self.assertEqual(result.get("skill"), optional, result)
                self.assertEqual(result.get("source"), source, result)
                self.assertEqual(result.get("profile_availability"),
                                 "optional-skill-required", result)
                self.assertEqual(result.get("mutation_permission"), "deny", result)
                self.assertIn("profile_availability=optional-skill-required",
                              format_result(result))

        explicit = match_text(manifest, "继续吸收外部成熟方法",
                              skill=optional, scope="optional-skill")
        self.assertIs(explicit.get("match"), True, explicit)
        self.assertEqual(explicit.get("profile_availability"), "optional-skill-required",
                         explicit)

        core = match_text(manifest, "对标优质 Skills，先只读研究具体文件方法", scope="auto")
        self.assertEqual(core.get("skill"), "adk-skill-deep-analysis", core)
        self.assertNotEqual(core.get("profile_availability"), "optional-skill-required")

        refused = match_text(manifest, "不要吸收外部成熟方法", scope="auto")
        self.assertIs(refused.get("match"), False, refused)
        self.assertEqual(refused.get("mutation_permission"), "deny", refused)


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

    def test_goal_skill_route_positive_negative_and_no_generic_hijack(self) -> None:
        # Source-only matcher regression. Not evidence of native host invocation
        # or actual token savings.
        manifest = Manifest.load(ROOT)
        direct = (
            ("adk-goal-authoring", "生成Goal合同并保留原验收", True),
            ("adk-goal-authoring", "Goal怎么写才可以验证？", True),
            ("adk-goal-authoring", "已有Goal继续执行，不要重建", False),
            ("adk-goal-authoring", "只查看CI状态", False),
            ("adk-planning-execution-loop", "按现有计划继续执行并验证", True),
            ("adk-planning-execution-loop", "分阶段执行现有任务包", True),
            ("adk-planning-execution-loop", "计划审查和风险说明", False),
            ("adk-planning-execution-loop", "恢复摘要", False),
            ("adk-planning-execution-loop", "生成Goal合同", False),
            ("adk-planning-execution-loop", "仅查询CI状态", False),
        )
        for skill, prompt, expected in direct:
            with self.subTest(skill=skill, prompt=prompt):
                answer = match_text(manifest, prompt, skill=skill, scope="skill")
                self.assertIs(answer.get("match"), expected, answer)
        for prompt, expected in (
            ("生成Goal合同并保留原验收", "adk-goal-authoring"),
            ("按现有计划继续执行并验证", "adk-planning-execution-loop"),
        ):
            with self.subTest(auto=prompt):
                actual = match_text(manifest, prompt, scope="auto")
                self.assertIs(actual.get("match"), True, actual)
                self.assertEqual(actual.get("skill"), expected, actual)
        author = _frontmatter(ROOT / "skills/adk-goal-authoring/SKILL.md")
        execute = _frontmatter(ROOT / "skills/adk-planning-execution-loop/SKILL.md")
        self.assertNotIn("长期不收敛", author["triggers"])
        self.assertFalse({"计划审查", "长任务", "恢复摘要"} & set(execute["triggers"]))
        self.assertIn("不用于", author["description"])
        self.assertIn("不用于", execute["description"])

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


    def test_negation_scope_and_paraphrase_regressions(self) -> None:
        """Source-only routing checks: negated actions are not selected as primary."""
        manifest = Manifest.load(ROOT)
        cases = (
            ("不要做性能分析，请只进行代码审查", "adk-code-review-loop", "adk-performance-profiling-embedded"),
            ("Do not brainstorm. Implement the approved plan.", None, "adk-structured-requirements-questioning"),
            ("按照已有方案推进，不要重新头脑风暴", None, "adk-structured-requirements-questioning"),
            ("先不用做代码审查，给我整理需求和验收标准", None, "adk-code-review-loop"),
            ("只读审查代码，不要修改文件", "adk-code-review-loop", None),
            ("排查偶发死锁，先不要修改代码", "adk-systematic-debugging", None),
            ("先聊聊方案和边界，不要直接实现", "adk-structured-requirements-questioning", None),
        )
        for prompt, expected, prohibited in cases:
            with self.subTest(prompt=prompt):
                result = match_text(manifest, prompt, scope="auto")
                if expected is not None:
                    self.assertEqual(result.get("skill"), expected, result)
                if prohibited is not None:
                    self.assertNotEqual(result.get("skill"), prohibited, result)
                if "不要修改" in prompt:
                    self.assertEqual(result.get("mutation_permission"), "deny", result)

    def test_embedded_domain_routing_uses_intent_not_bare_nouns(self) -> None:
        """Source-only regression: specialist noun must not grant migration/build action."""
        manifest = Manifest.load(ROOT)
        cases = (
            ("SSC305 的 /dev/root 是 squashfs，df 显示100%，这正常吗？",
             "adk-systematic-debugging"),
            ("只分析UBIFS只读故障，不做OTA布局迁移",
             "adk-systematic-debugging"),
            ("UBIFS 并发写后变只读，先定位根因，不要修改分区",
             "adk-systematic-debugging"),
            ("Buildroot 交叉编译 exfatprogs 失败，提示缺少 aclocal",
             "adk-systematic-debugging"),
            ("FreeRTOS 的 FromISR 偶发断言，中断优先级设为0",
             "adk-interrupt-dma-patterns"),
            ("DMA偶发读到旧数据，buffer加volatile可以吗？",
             "adk-interrupt-dma-patterns"),
            ("Linux DMA cache coherency issue during receive",
             "adk-interrupt-dma-patterns"),
            ("MM32SPIN023C 随机 HardFault，怎么收集现场？",
             "adk-hardware-debugging"),
            ("GD32L235 进入低功耗后无法唤醒",
             "adk-hardware-debugging"),
            ("MQTT DNS resolution failed，WiFi仍然连接，怎么排查？",
             "adk-systematic-debugging"),
            ("SPI屏背光亮无图，初始化没报错", "adk-driver-bringup-checklist"),
            ("用 CMake 交叉编译 ARM 工程", "adk-cmake-cross-build"),
            ("Buildroot 的 CMake package 交叉编译失败", "adk-cmake-cross-build"),
            ("评估 UBIFS转SquashFS 的数据保留及迁移回滚方案",
             "adk-embedded-storage-layout-migration"),
            ("只评估OTA布局迁移风险，不执行迁移",
             "adk-embedded-storage-layout-migration"),
        )
        for prompt, expected in cases:
            with self.subTest(prompt=prompt):
                result = match_text(manifest, prompt, scope="auto")
                self.assertIs(result.get("match"), True, result)
                self.assertEqual(result.get("skill"), expected, result)
                self.assertEqual(result.get("runtime_role"), "primary", result)
                self.assertEqual(result.get("mutation_permission"), "deny", result)

        for prompt in ("只读解释SquashFS概念", "普通交叉编译概念介绍"):
            with self.subTest(prompt=prompt):
                result = match_text(manifest, prompt, scope="auto")
                self.assertNotEqual(result.get("skill"), "adk-embedded-storage-layout-migration")
                self.assertNotEqual(result.get("skill"), "adk-cmake-cross-build")
                self.assertEqual(result.get("mutation_permission"), "deny")

    def test_embedded_audit_method_and_reference_boundaries(self) -> None:
        """Source-only policy checks, not claimed board or native-runtime evidence."""
        def body(path: str) -> str:
            return (ROOT / path).read_text(encoding="utf-8")

        irq = body("skills/adk-interrupt-dma-patterns/references/details.md")
        self.assertNotIn("devmem2 <NVIC", irq)
        self.assertIn("不是直接测 IRQ entry latency", irq)
        self.assertIn("rtos-isr-dma-diagnostics.md", irq)

        hil = body("skills/adk-integration-hil-sil/SKILL.md")
        self.assertNotIn("-DTARGET_SIM=ON", hil)
        self.assertNotIn("scripts/ci_test.sh --", hil)
        self.assertIn("compile-only", hil)
        self.assertIn("not-run", hil)

        protocol = body("skills/adk-protocol-stack-integration/SKILL.md")
        self.assertNotIn('scapy.all.sniff(filter=', protocol)
        self.assertIn("Python API", protocol)

        unit = body("skills/adk-unit-test-embedded/SKILL.md")
        self.assertIn("MC/DC", unit)
        self.assertIn("不等于 MC/DC", unit)
        self.assertNotIn("≥80%", unit)

        cmake = body("skills/adk-cmake-cross-build/SKILL.md")
        self.assertIn("CROSSCOMPILING_EMULATOR", cmake)
        self.assertIn("compile-only", cmake)
        self.assertIn("not-run", cmake)

        static = body("skills/adk-static-analysis-c-cpp/SKILL.md")
        self.assertIn("--error-exitcode=1", static)
        self.assertIn("--warnings-as-errors", static)
        self.assertIn("BASE_SHA", static)
        self.assertIn("非零", static)

        production = body("skills/adk-embedded-release-orchestration/SKILL.md")
        self.assertIn("multi-mcu-ota-recovery.md", production)
        fault = body("skills/adk-hardware-debugging/SKILL.md")
        self.assertIn("mcu-fault-reset-wakeup.md", fault)
        self.assertIn("Cortex-M0", fault)
        sysdebug = body("skills/adk-systematic-debugging/SKILL.md")
        self.assertIn("embedded-diagnosis-branches.md", sysdebug)
        perf = body("skills/adk-performance-profiling-embedded/SKILL.md")
        self.assertIn("mcu-memory-footprint.md", perf)

        for reference in (
            "skills/adk-hardware-debugging/references/mcu-fault-reset-wakeup.md",
            "skills/adk-interrupt-dma-patterns/references/rtos-isr-dma-diagnostics.md",
            "skills/adk-systematic-debugging/references/embedded-diagnosis-branches.md",
            "skills/adk-embedded-release-orchestration/references/multi-mcu-ota-recovery.md",
            "skills/adk-performance-profiling-embedded/references/mcu-memory-footprint.md",
        ):
            with self.subTest(reference=reference):
                self.assertTrue((ROOT / reference).is_file())

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
