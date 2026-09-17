from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from agent_dev_kit.matcher_vnext import match_text, resolve_skill_content
from agent_dev_kit.model import Manifest

ROOT = Path(__file__).resolve().parents[1]


class SkillGovernanceV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = Manifest.load(ROOT)
        cls.entries: list[dict[str, Any]] = []
        for section in ("skills", "optional_skills"):
            values = cls.manifest.data.get(section, [])
            assert isinstance(values, list)
            cls.entries.extend(item for item in values if isinstance(item, dict))
        cls.by_name = {str(item["name"]): item for item in cls.entries}

    def test_dependency_graph_is_valid_acyclic_and_forward_only(self) -> None:
        names = set(self.by_name)
        graph: dict[str, tuple[str, ...]] = {}
        for name, item in self.by_name.items():
            deps = item.get("depends_on", [])
            self.assertIsInstance(deps, list, name)
            self.assertEqual(len(deps), len(set(deps)), f"duplicate depends_on for {name}")
            missing = [dep for dep in deps if dep not in names]
            self.assertEqual(missing, [], f"dangling depends_on for {name}: {missing}")
            self.assertNotIn(name, deps, f"self dependency for {name}")
            current_order = (int(item["lifecycle_order"]), int(item["stage_order"]))
            for dep in deps:
                dependency = self.by_name[str(dep)]
                dep_order = (int(dependency["lifecycle_order"]), int(dependency["stage_order"]))
                self.assertLess(
                    dep_order,
                    current_order,
                    f"dependency must precede consumer: {dep} {dep_order} !< {name} {current_order}",
                )
            graph[name] = tuple(str(dep) for dep in deps)

        visiting: set[str] = set()
        visited: set[str] = set()

        def walk(node: str, chain: tuple[str, ...]) -> None:
            if node in visited:
                return
            if node in visiting:
                raise AssertionError("skill dependency cycle: " + " -> ".join(chain + (node,)))
            visiting.add(node)
            for dep in graph[node]:
                walk(dep, chain + (node,))
            visiting.remove(node)
            visited.add(node)

        for name in sorted(graph):
            walk(name, ())

    def test_routing_primaries_resolve_to_primary_runtime_role(self) -> None:
        routing = self.manifest.data.get("routing")
        self.assertIsInstance(routing, dict)
        intents = routing.get("intents", [])
        self.assertIsInstance(intents, list)
        for intent in intents:
            if not isinstance(intent, dict) or not intent.get("primary_skill"):
                continue
            skill = str(intent["primary_skill"])
            metadata = resolve_skill_content(self.manifest, skill)
            self.assertEqual(metadata["runtime_role"], "primary", f"routing primary must be v2 primary: {skill}")

    def test_supporting_implicit_promotion_has_exactly_one_same_group_primary(self) -> None:
        metadata = {name: resolve_skill_content(self.manifest, name) for name in self.by_name}
        for name, value in metadata.items():
            if value["runtime_role"] != "supporting":
                continue
            policy = value["implicit_trigger_policy"]
            self.assertIn(policy, {"promote-same-group", "explicit-only"}, name)
            if policy == "explicit-only":
                continue
            group = value["selection_group"]
            primaries = [
                candidate
                for candidate, candidate_value in metadata.items()
                if candidate_value["runtime_role"] == "primary"
                and candidate_value["selection_group"] == group
            ]
            self.assertEqual(len(primaries), 1, f"supporting skill {name} requires one same-group primary: {primaries}")

    def test_requirements_supporting_trigger_promotes_only_to_requirements_primary(self) -> None:
        result = match_text(self.manifest, "帮我理清需求")
        self.assertTrue(result.get("match"), result)
        self.assertEqual(result.get("skill"), "adk-requirements-triage", result)
        self.assertEqual(result.get("selection_group"), "requirements-intake", result)
        self.assertTrue(result.get("selection_group_promoted"), result)

    def test_review_routing_uses_review_loop_not_language_overlay(self) -> None:
        result = match_text(self.manifest, "代码审查")
        self.assertTrue(result.get("match"), result)
        self.assertEqual(result.get("skill"), "adk-code-review-loop", result)
        self.assertEqual(result.get("selection_group"), "code-review", result)

    def test_driver_bringup_exposes_live_device_escalation_without_granting_it(self) -> None:
        result = match_text(self.manifest, "驱动开发")
        self.assertTrue(result.get("match"), result)
        self.assertEqual(result.get("skill"), "adk-driver-bringup-checklist", result)
        self.assertEqual(result.get("effect_scope"), "workspace", result)
        self.assertEqual(result.get("effect_operation"), "write", result)
        self.assertEqual(result.get("live_device_authorization"), "explicit-required", result)
        self.assertIn("live-device:register-write", result.get("escalation_effects", ()))
        self.assertIn("target-identity", result.get("live_device_authorization_requirements", ()))

    def test_bsp_porting_exposes_flash_and_storage_escalation(self) -> None:
        result = match_text(self.manifest, "BSP移植")
        self.assertTrue(result.get("match"), result)
        self.assertEqual(result.get("skill"), "adk-bsp-porting-playbook", result)
        self.assertEqual(result.get("live_device_authorization"), "explicit-required", result)
        effects = set(result.get("escalation_effects", ()))
        self.assertIn("live-device:flash", effects)
        self.assertIn("live-device:storage-write", effects)

    def test_field_readiness_stays_read_only(self) -> None:
        result = match_text(self.manifest, "量产产测和OTA回滚 readiness")
        self.assertTrue(result.get("match"), result)
        self.assertEqual(result.get("skill"), "adk-production-field-readiness", result)
        self.assertEqual(result.get("effect_ceiling"), "read-only", result)
        self.assertEqual(result.get("mutation_permission"), "deny", result)
        self.assertEqual(result.get("live_device_authorization"), "not-required", result)

    def test_release_orchestration_requires_separate_publish_and_device_authority(self) -> None:
        metadata = resolve_skill_content(self.manifest, "adk-embedded-release-orchestration")
        effects = set(metadata["escalation_effects"])
        self.assertEqual(metadata["effect_ceiling"], "release-preparation")
        self.assertIn("release-target:publish", effects)
        self.assertIn("live-device:flash", effects)

    def test_embedded_skills_do_not_embed_unauthorized_live_mutation_commands(self) -> None:
        paths = (
            "skills/adk-driver-bringup-checklist/SKILL.md",
            "skills/adk-bsp-porting-playbook/SKILL.md",
            "skills/adk-embedded-storage-layout-migration/SKILL.md",
        )
        forbidden = ("devmem2 <phys_addr> w", "fastboot flash", "dd if=boot.img of=/dev/", "flashcp ")
        for relative in paths:
            text = (ROOT / relative).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"unauthorized mutation command in {relative}: {token}")
            self.assertIn("explicit", text.lower(), relative)

    def test_realtime_skills_use_target_budgets_not_fixed_thresholds(self) -> None:
        irq = (ROOT / "skills/adk-interrupt-dma-patterns/SKILL.md").read_text(encoding="utf-8")
        rtos = (ROOT / "skills/adk-rtos-task-design/SKILL.md").read_text(encoding="utf-8")
        for forbidden in ("<10KB/s", "50%"):
            self.assertNotIn(forbidden, irq)
        self.assertIn("ownership", irq.lower())
        self.assertIn("non-coherent", irq)
        self.assertIn("response-time", rtos.lower())
        self.assertIn("ISR interference", rtos)
        self.assertNotIn("RMA/DMA", rtos)

    def test_driver_implementation_declares_runtime_model_and_live_device_handoff(self) -> None:
        text = (ROOT / "skills/adk-driver-implementation/SKILL.md").read_text(encoding="utf-8")
        for token in ("linux-kernel", "rtos", "bare-metal", "Live-device Handoff", "explicit authorization"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
