"""Consume published schema examples and exported blank review checklists."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import tempfile
import unittest

from jsonschema import Draft7Validator, Draft202012Validator
from jsonschema.validators import validator_for

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "skills/adk-interface-contract-design/references/details.md"
PARALLEL = ROOT / "skills/adk-parallel-agent-governance"
DRAFT7 = "http://json-schema.org/draft-07/schema#"
MODERN = "https://json-schema.org/draft/2020-12/schema"

# Literal acceptance vectors from the consumer contract, independent of the examples.
INPUTS = {
    "legitimate": {"id": 1, "mode": "safe"},
    "unknown_field": {"id": 1, "mode": "safe", "admin": True},
    "missing_id": {"mode": "safe"},
    "missing_mode": {"id": 1},
    "invalid_type": {"id": "1", "mode": "safe"},
    "invalid_enum": {"id": 1, "mode": "superuser"},
}
ACCEPTANCE = {name: name == "legitimate" for name in INPUTS}


class SchemaClosureExampleTests(unittest.TestCase):
    def setUp(self):
        schemas = [json.loads(block) for block in
                   re.findall(r"```json\n(.*?)```", INTERFACE.read_text(encoding="utf-8"), re.S)]
        self.assertEqual(2, len(schemas), "publish flat and composed executable schema examples")
        self.schemas = {schema["$schema"]: schema for schema in schemas}
        self.assertEqual({DRAFT7, MODERN}, set(self.schemas))

    def assert_acceptance(self, schema, validator_type, expected):
        self.assertIs(validator_type, validator_for(schema))
        validator_type.check_schema(schema)
        validator = validator_type(schema)
        for name, instance in INPUTS.items():
            with self.subTest(input=name):
                errors = list(validator.iter_errors(instance))
                self.assertEqual(expected[name], not errors,
                                 [error.message for error in errors])
        return validator

    def test_same_level_closure_accepts_only_contract_inputs(self):
        schema = copy.deepcopy(self.schemas[DRAFT7])
        schema["$schema"] = MODERN
        self.assert_acceptance(schema, Draft202012Validator, ACCEPTANCE)

    def test_published_composed_closure_accepts_only_contract_inputs(self):
        self.assert_acceptance(self.schemas[MODERN], Draft202012Validator, ACCEPTANCE)

    def test_closed_subschema_control_rejects_legitimate_extension(self):
        schema = copy.deepcopy(self.schemas[MODERN])
        schema.pop("unevaluatedProperties")
        schema["allOf"][0]["additionalProperties"] = False
        validator = self.assert_acceptance(schema, Draft202012Validator,
                                           {name: False for name in INPUTS})
        errors = list(validator.iter_errors(INPUTS["legitimate"]))
        self.assertTrue(any(error.validator == "additionalProperties" and "mode" in error.message
                            for error in errors), errors)

    def test_old_dialect_ignores_composition_closure_control(self):
        schema = copy.deepcopy(self.schemas[MODERN])
        schema["$schema"] = DRAFT7
        self.assert_acceptance(schema, Draft7Validator, {**ACCEPTANCE, "unknown_field": True})

    def test_published_legacy_flattening_accepts_only_contract_inputs(self):
        self.assert_acceptance(self.schemas[DRAFT7], Draft7Validator, ACCEPTANCE)


class ExportedReviewChecklistTests(unittest.TestCase):
    def test_blank_evidence_never_starts_with_a_pass(self):
        checks = {
            "Scope stayed inside `scope_write`",
            "No shared contract/schema/root config changed unexpectedly",
            "Verification commands ran",
            "Handoff summary is clear",
            "Integration risk identified",
        }
        manifest = Manifest.load(ROOT)
        with tempfile.TemporaryDirectory(prefix="adk-review-checklist-") as directory:
            for runtime in ("claude-code", "opencode"):
                with self.subTest(runtime=runtime):
                    exported = export_assets(manifest, runtime, Path(directory), ["core"])
                    self.assertEqual("pass", exported["status"])
                    consumer = Path(exported["output"])
                    skill, = [path for path in consumer.rglob("SKILL.md")
                              if path.parent.name == PARALLEL.name]
                    default = re.search(r"默认使用随包 `([^`]+)`", skill.read_text(encoding="utf-8"))
                    self.assertIsNotNone(default, "resolve the actual exported default task package")
                    package = skill.parent / default.group(1)
                    checklist_links = [link for link in re.findall(
                        r"`([^`\n]+)`", package.read_text(encoding="utf-8"))
                        if Path(link).name == "subagent-review-checklist.md"]
                    self.assertEqual(1, len(checklist_links))
                    checklist = package.parent / checklist_links[0]
                    self.assertEqual((PARALLEL / "references/subagent-review-checklist.md").read_bytes(),
                                     checklist.read_bytes())
                    section = checklist.read_text(encoding="utf-8").split(
                        "## Completion Review", 1)[1].split("## Rework Decision", 1)[0]
                    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]
                            for line in section.splitlines() if line.startswith("|")]
                    self.assertEqual(["Check", "Result", "Evidence"], rows[0])
                    self.assertEqual(["---", "---", "---"], rows[1])
                    self.assertEqual(5, len(rows[2:]))
                    self.assertEqual(checks, {row[0] for row in rows[2:]})
                    for row in rows[2:]:
                        with self.subTest(check=row[0]):
                            self.assertEqual(3, len(row))
                            self.assertEqual("", row[2], "default template has no completed review evidence")
                            self.assertIn(row[1], {"pending", "not-run"},
                                          "blank evidence cannot support a pass verdict")


if __name__ == "__main__":
    unittest.main()
