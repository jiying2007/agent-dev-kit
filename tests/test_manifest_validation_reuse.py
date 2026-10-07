"""Validation reuse must observe data, schema and filesystem changes."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

from agent_dev_kit.model import Manifest, _compiled_schema_bundle
from agent_dev_kit.validation_contract import validate_repository


ROOT = Path(__file__).resolve().parents[1]


class ValidationReuseTests(unittest.TestCase):
    def test_identical_schema_bytes_at_two_roots_compile_once(self):
        _compiled_schema_bundle.cache_clear()
        with tempfile.TemporaryDirectory() as temp:
            roots = [Path(temp) / name for name in ("first", "second")]
            for root in roots:
                (root / "manifests").mkdir(parents=True)
                shutil.copyfile(ROOT / "manifest.json", root / "manifest.json")
                shutil.copyfile(ROOT / "manifests/manifest.schema.json", root / "manifests/manifest.schema.json")
            with mock.patch.object(Draft202012Validator, "check_schema", wraps=Draft202012Validator.check_schema) as check:
                for root in roots:
                    Manifest.load(root)
                self.assertEqual(1, check.call_count)

    def test_unchanged_loaded_data_reuses_only_schema_success(self):
        manifest = Manifest.load(ROOT)
        with mock.patch.object(Draft202012Validator, "iter_errors", side_effect=AssertionError("repeat")):
            self.assertEqual([], manifest._json_schema_failures())

    def test_nested_data_mutation_is_revalidated(self):
        manifest = Manifest.load(ROOT)
        manifest.data["product"]["runtime_boundary"] = "llm-runner"
        self.assertTrue(manifest._json_schema_failures())

    def test_tuple_cannot_reuse_list_validation(self):
        manifest = Manifest.load(ROOT)
        manifest.data["skills"] = tuple(manifest.data["skills"])
        self.assertTrue(manifest._json_schema_failures())

    def test_schema_file_change_invalidates_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifests").mkdir()
            shutil.copyfile(ROOT / "manifest.json", root / "manifest.json")
            schema_path = root / "manifests/manifest.schema.json"
            shutil.copyfile(ROOT / "manifests/manifest.schema.json", schema_path)
            manifest = Manifest.load(root)
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["properties"]["version"] = {"const": "0.0.0"}
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            self.assertTrue(manifest._json_schema_failures())

    def test_filesystem_checks_are_not_cached(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "manifests").mkdir()
            shutil.copyfile(ROOT / "manifest.json", root / "manifest.json")
            shutil.copyfile(ROOT / "manifests/manifest.schema.json", root / "manifests/manifest.schema.json")
            manifest = Manifest.load(root)
            relative = manifest.data["skills"][0]["path"]
            target = root / relative
            target.parent.mkdir(parents=True)
            target.write_text("asset", encoding="utf-8")
            before = manifest.validate()
            target.unlink()
            after = manifest.validate()
            self.assertGreater(len(after), len(before))
            self.assertTrue(any(relative in item for item in after if item not in before))

    def test_repository_validation_loads_manifest_once(self):
        with mock.patch.object(Manifest, "load", wraps=Manifest.load) as load:
            result = validate_repository(ROOT, strict=False, quick=True)
            self.assertEqual("pass", result["status"])
            self.assertEqual(1, load.call_count)

    def test_invalid_identity_blocks_governance_without_claiming_pass(self):
        with mock.patch("agent_dev_kit.validation_contract.version_identity_failures", return_value=["forced identity mismatch"]), \
             mock.patch("agent_dev_kit.validation_contract._governance_gate_failure", side_effect=AssertionError("blocked gate ran")):
            result = validate_repository(ROOT, strict=True, quick=False)
        self.assertEqual("fail", result["status"])
        self.assertIn("forced identity mismatch", result["failures"])
        self.assertEqual("blocked", result["governance_checks"]["status"])
        self.assertEqual(0, result["governance_checks"]["checked"])

    def test_valid_identity_executes_all_governance_and_preserves_failure(self):
        with mock.patch("agent_dev_kit.validation_contract._governance_gate_failure", return_value="forced governance failure") as gate:
            result = validate_repository(ROOT, strict=True, quick=False)
        self.assertEqual("fail", result["status"])
        self.assertEqual(5, gate.call_count)
        self.assertEqual(5, result["governance_checks"]["checked"])
        self.assertIn("forced governance failure", result["failures"])

    def test_asset_failure_is_separate_from_passing_governance(self):
        with mock.patch("agent_dev_kit.validation_contract._validate_loaded_assets", return_value={"failures": ["forced asset failure"]}), \
             mock.patch("agent_dev_kit.validation_contract._governance_gate_failure", return_value=None):
            result = validate_repository(ROOT, strict=True, quick=False)
        self.assertEqual("fail", result["status"])
        self.assertEqual("pass", result["governance_checks"]["status"])
        self.assertEqual(5, result["governance_checks"]["checked"])

    def test_cold_help_does_not_import_domain_dependencies(self):
        code = (
            "import sys,importlib.abc;"
            "exec('class Block(importlib.abc.MetaPathFinder):\\n"
            " def find_spec(self,fullname,path=None,target=None):\\n"
            "  if fullname.split(\".\")[0] in (\"yaml\",\"jsonschema\"):\\n"
            "   raise ImportError(\"unexpected dependency\")');"
            "sys.meta_path.insert(0,Block());"
            "from agent_dev_kit.cli import main; raise SystemExit(main(['help']))"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Commands:", result.stdout)

    def test_cold_task_cost_does_not_import_asset_domains(self):
        code = (
            "import sys,importlib.abc;"
            "exec('class Block(importlib.abc.MetaPathFinder):\\n"
            " def find_spec(self,fullname,path=None,target=None):\\n"
            "  if fullname.split(\".\")[0] in (\"yaml\",\"jsonschema\"):\\n"
            "   raise ImportError(\"unexpected dependency\")');"
            "sys.meta_path.insert(0,Block());"
            "from agent_dev_kit.cli import main; rc=main(['task-cost','--task','offline']);"
            "raise SystemExit(0 if rc in (0,2) else 3)"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("skill_usage", json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
