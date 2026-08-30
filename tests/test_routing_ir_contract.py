import copy
import unittest
from pathlib import Path

from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]


class RoutingIrContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = Manifest.load(ROOT)

    def schema_failures(self, data):
        return Manifest(ROOT, data, ROOT / "manifest.json").validate(strict=False)

    def assert_schema_failure(self, data, expected_path):
        failures = self.schema_failures(data)
        self.assertTrue(
            any(expected_path in failure for failure in failures),
            (expected_path, failures),
        )

    def test_negation_phrase_classes_are_closed_and_required(self):
        routing = self.manifest.data["routing"]
        self.assertEqual(
            set(routing["negation_phrase_classes"]),
            {
                "direct_prohibition",
                "not_required",
                "execution_denial",
                "contrastive_prohibition",
                "generic_negation",
            },
        )
        flattened = {
            phrase
            for phrases in routing["negation_phrase_classes"].values()
            for phrase in phrases
        }
        self.assertTrue({"不需要", "无需", "别", "不要", "请勿", "不过别"} <= flattened)

        missing_required_phrase = copy.deepcopy(self.manifest.data)
        missing_required_phrase["routing"]["negation_phrase_classes"]["direct_prohibition"].remove("请勿")
        self.assert_schema_failure(
            missing_required_phrase,
            "schema routing/negation_phrase_classes/direct_prohibition",
        )

        legacy_flat_markers = copy.deepcopy(self.manifest.data)
        legacy_flat_markers["routing"]["negation_markers"] = ["不"]
        self.assert_schema_failure(legacy_flat_markers, "schema routing")

    def test_negated_intent_conditions_fail_closed(self):
        invalid = copy.deepcopy(self.manifest.data)
        intent = next(
            item for item in invalid["routing"]["intents"]
            if item["intent"] == "planning_execution"
        )
        intent["negated_intents"][0]["all_of"][0]["phrase_class"] = "full_sentence_alias"
        index = invalid["routing"]["intents"].index(intent)
        self.assert_schema_failure(
            invalid,
            "schema routing/intents/{}/negated_intents/0/all_of/0/phrase_class".format(index),
        )

        invalid_polarity = copy.deepcopy(self.manifest.data)
        intent = next(
            item for item in invalid_polarity["routing"]["intents"]
            if item["intent"] == "planning_execution"
        )
        intent["negated_intents"][0]["all_of"][1]["polarity"] = "unknown"
        index = invalid_polarity["routing"]["intents"].index(intent)
        self.assert_schema_failure(
            invalid_polarity,
            "schema routing/intents/{}/negated_intents/0/all_of/1/polarity".format(index),
        )

    def test_phrase_classes_cover_readonly_and_generic_execution_synonyms(self):
        phrase_classes = self.manifest.data["routing"]["phrase_classes"]
        self.assertEqual(
            set(phrase_classes),
            {"readonly_scope", "generic_execution", "planning_action", "debugging_action", "release_action"},
        )
        self.assertIn("只分析", phrase_classes["readonly_scope"])
        self.assertTrue({"执行", "实施", "推进", "落地"} <= set(phrase_classes["generic_execution"]))

    def test_catalog_matrix_is_a_routing_ir_projection(self):
        expected = {
            "runtime_routing": "runtime_router",
            "unclear_requirement": "requirements_triage",
            "planning_only": "plan_lite",
            "task_breakdown": "task_breakdown",
            "long_execution": "planning_execution",
            "unknown_root_cause_bug": "systematic_debugging",
            "embedded_log_analysis": "embedded_remote_debug_log_triage",
            "embedded_core_dump": "offline_core_dump_triage",
            "embedded_debug_transport": "embedded_debug_transport",
            "completion_gate": "verification_before_completion",
            "commit_pr_gate": "commit_pr_quality_gate",
            "release_versioning": "release_versioning",
            "external_practice_absorption": "external_practice_absorption",
            "skill_governance": "skill_composition_governance",
        }
        matrix = self.manifest.data["skill_routing_matrix"]
        self.assertEqual(
            {entry["name"]: entry["routing_intent"] for entry in matrix},
            expected,
        )
        duplicated_semantics = {
            "primary_skill",
            "supporting_skills",
            "fallback_skills",
            "mutually_exclusive",
            "availability",
        }
        for entry in matrix:
            self.assertFalse(duplicated_semantics.intersection(entry), entry)

        legacy_parallel_ssot = copy.deepcopy(self.manifest.data)
        legacy_parallel_ssot["skill_routing_matrix"][0]["primary_skill"] = "adk-runtime-router"
        self.assert_schema_failure(legacy_parallel_ssot, "schema skill_routing_matrix/0")

        conflicting_projection = copy.deepcopy(self.manifest.data)
        conflicting_projection["skill_routing_matrix"][0]["routing_intent"] = "requirements_triage"
        self.assert_schema_failure(conflicting_projection, "schema skill_routing_matrix/0")


if __name__ == "__main__":
    unittest.main()
