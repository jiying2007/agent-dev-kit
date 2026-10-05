from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_dev_kit.strict_json import StrictJSONError, loads, read
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.campaign_model import _load_json_object
from agent_dev_kit.effect_campaign_materializer import _load_effect_plan
from agent_dev_kit.agent_value_contracts import _load_json as load_value_contract
from agent_dev_kit.agent_value_trust import _json_object as load_trust_registry
from agent_dev_kit.native_campaign_contract import _load_json as load_native_campaign
from agent_dev_kit.evaluation_runtime import load_tasks, _load_effect_inputs


class StrictJSONTests(unittest.TestCase):
    def test_legal_json_and_string_brackets(self):
        self.assertEqual({"name": "[\\\"]", "x": [1, 2.5]}, loads('{"name":"[\\\\\\\"]","x":[1,2.5]}'))
        self.assertEqual([1, True, None], loads(b"[1,true,null]"))

    def test_ambiguity_nonfinite_and_budgets(self):
        for raw in ('{"x":1,"x":2}', '{"x":1,"\\u0078":2}',
                    '{"a":{"x":1,"x":2}}', 'NaN', 'Infinity', '-Infinity', '1e999'):
            with self.subTest(raw=raw), self.assertRaises(StrictJSONError):
                loads(raw)
        with self.assertRaisesRegex(StrictJSONError, "byte budget"):
            loads('{"x":1}', max_bytes=2)
        with self.assertRaisesRegex(StrictJSONError, "nesting budget"):
            loads("[" * 65 + "0" + "]" * 65)
        with self.assertRaises(StrictJSONError):
            loads(b"\xff")
        with self.assertRaises(StrictJSONError):
            loads("{}", max_bytes=True)

    def test_errors_do_not_echo_keys_values_or_paths(self):
        try:
            loads('{"private-marker":"secret-value","private-marker":0}')
        except StrictJSONError as exc:
            self.assertNotIn("private-marker", str(exc))
            self.assertNotIn("secret-value", str(exc))
        else:
            self.fail("duplicate keys accepted")

    def test_bounded_file_read_and_real_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "manifest.json"
            path.write_text('{"version":"x","version":"y"}')
            with self.assertRaisesRegex(StrictJSONError, "byte budget"):
                read(path, max_bytes=4)
            with self.assertRaises(ManifestError):
                Manifest.load(root)
            with self.assertRaises(ManifestError):
                _load_json_object(path, "campaign plan")
            with self.assertRaises(ManifestError):
                _load_effect_plan(path)
            with self.assertRaises(ManifestError):
                load_value_contract(path, "receipt")
            with self.assertRaises(ManifestError):
                load_trust_registry(path, limit=1024, label="trust registry")
            with self.assertRaises(ManifestError):
                load_native_campaign(path, "native receipt")

    def test_task_and_effect_jsonl_consumers_reject_nonfinite_and_depth(self):
        import json
        task = {"id": "case", "category": "test", "prompt": "test", "expected_skill": "adk-test-strategy", "expected_safe": True}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "tasks.jsonl"
            prefix = json.dumps(task)[:-1]
            for value in ("NaN", "Infinity", "1e999", "[" * 65 + "0" + "]" * 65):
                path.write_text(prefix + ',"extra":' + value + "}\n")
                with self.subTest(value=value), self.assertRaises(ManifestError):
                    load_tasks(path)
                with self.subTest(value=value), self.assertRaises(ManifestError):
                    _load_effect_inputs(path)


if __name__ == "__main__":
    unittest.main()
