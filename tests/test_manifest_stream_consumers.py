"""Exercise real Manifest producers with bounded large streams and failed producers."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MATCH = "probe-match"
SPECIAL = "probe.match[*]"
OPTION = "-probe-option"
HELPERS = (
    "adk_tool_exists",
    "adk_external_handoff_target_exists",
    "adk_profile_exists",
    "adk_optional_skill_exists",
    "adk_routing_intent_exists",
)


class ManifestStreamConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="adk-manifest-stream-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        sources = (
            "scripts/lib-manifest.sh",
            "scripts/check-goal-contracts.sh",
            "scripts/check-capability-health.sh",
            "src/agent_dev_kit/__init__.py",
            "src/agent_dev_kit/manifest_query.py",
            "manifests/adk_goal_contracts.json",
            "manifests/adk_capability_health_contracts.json",
        )
        for relative in sources:
            destination = cls.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        cls.contracts = {
            name: json.loads((cls.root / "manifests" / name).read_text(encoding="utf-8"))
            for name in ("adk_goal_contracts.json", "adk_capability_health_contracts.json")
        }

        def copy_referenced_files(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ("path", "script", "test", "doc") and isinstance(item, str):
                        destination = cls.root / item
                        if not destination.exists():
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(ROOT / item, destination)
                    copy_referenced_files(item)
            elif isinstance(value, list):
                for item in value:
                    copy_referenced_files(item)

        for contract in cls.contracts.values():
            copy_referenced_files(contract)
        # These are query-protocol fixtures, not complete schema-qualified assets.
        # Each collection has over 1 MiB of unmatched output after the early hits.
        names = [MATCH, SPECIAL, OPTION] + [
            "stream-tail-{:04d}-{}".format(index, "x" * 512) for index in range(2048)
        ]
        cls.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        for section in ("tool_targets", "external_handoff_targets", "profiles"):
            cls.manifest[section] = dict(
                [(name, {}) for name in names[:3]]
                + list(cls.manifest.get(section, {}).items())
                + [(name, {}) for name in names[3:]]
            )
        for section in ("optional_skills", "agents", "skills", "workflows"):
            cls.manifest[section] = (
                [{"name": name} for name in names[:3]]
                + cls.manifest.get(section, [])
                + [{"name": name} for name in names[3:]]
            )
        cls.manifest["routing"]["intents"] = (
            [{"intent": name} for name in names[:3]]
            + cls.manifest["routing"]["intents"]
            + [{"intent": name} for name in names[3:]]
        )
        cls.env = os.environ.copy()
        cls.env.pop("BASH_ENV", None)
        cls.env["PYTHONUNBUFFERED"] = "1"
        cls.env["PYTHONPATH"] = str(cls.root / "src")

    def setUp(self):
        self.write_manifest(self.manifest)
        for name, contract in self.contracts.items():
            (self.root / "manifests" / name).write_text(
                json.dumps(contract, indent=2) + "\n", encoding="utf-8"
            )

    def write_manifest(self, data):
        (self.root / "manifest.json").write_text(json.dumps(data), encoding="utf-8")

    def shell(self, code, *arguments):
        return subprocess.run(
            ["bash", "-o", "pipefail", "-c", code, "manifest-stream-test"] + list(arguments),
            cwd=str(self.root), env=self.env, capture_output=True, text=True,
            timeout=20, check=False,
        )

    def helper(self, helper, name, prefix=""):
        return self.shell(
            'source scripts/lib-manifest.sh; ' + prefix + '"$1" "$2"', helper, name
        )

    def test_early_matches_drain_large_real_producer_output(self):
        for helper in HELPERS:
            with self.subTest(helper=helper):
                result = self.helper(helper, MATCH)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)
                self.assertEqual("", result.stderr)

    def test_exact_literal_and_option_like_names(self):
        for helper in HELPERS:
            for name in (SPECIAL, OPTION):
                with self.subTest(helper=helper, name=name):
                    result = self.helper(helper, name)
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual("", result.stdout)
            for name in ("missing-name", "probe-mat", "probe.*"):
                with self.subTest(helper=helper, absent=name):
                    result = self.helper(helper, name)
                    self.assertEqual(1, result.returncode, result.stderr)
                    self.assertEqual("", result.stdout)
                    self.assertEqual("", result.stderr)

    def test_empty_collections_remain_absent(self):
        self.write_manifest({})
        for helper in HELPERS:
            with self.subTest(helper=helper):
                result = self.helper(helper, MATCH)
                self.assertEqual(1, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_invalid_json_is_not_success(self):
        (self.root / "manifest.json").write_text("{invalid", encoding="utf-8")
        for helper in HELPERS:
            with self.subTest(helper=helper):
                result = self.helper(helper, MATCH)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("[FAIL]", result.stderr)
                self.assertEqual("", result.stdout)

    def test_matching_output_cannot_hide_producer_failure(self):
        for helper in HELPERS:
            with self.subTest(helper=helper):
                result = self.helper(
                    helper, MATCH,
                    '_adk_manifest_query() { printf "%s\\n" probe-match; return 23; }; ',
                )
                self.assertEqual(23, result.returncode, result.stderr)
                self.assertEqual("", result.stdout)

    def test_goal_and_capability_checks_accept_large_collections(self):
        for name in ("goal-contracts", "capability-health"):
            with self.subTest(checker=name):
                result = self.shell('bash "scripts/check-$1.sh" --summary-json', name)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("pass", json.loads(result.stdout)["status"])
                self.assertEqual("", result.stderr)

    def test_capability_optional_skill_fallback_drains_output(self):
        data = copy.deepcopy(self.manifest)
        skill = self.contracts["adk_capability_health_contracts.json"]["capabilities"][0]["skill"]
        data["skills"] = [item for item in data["skills"] if item["name"] != skill]
        data["optional_skills"].insert(0, {"name": skill})
        self.write_manifest(data)
        result = self.shell("bash scripts/check-capability-health.sh --summary-json")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("pass", json.loads(result.stdout)["status"])
        self.assertEqual("", result.stderr)

    def test_goal_and_capability_checks_reject_unknown_references(self):
        cases = (
            ("goal-contracts", "profiles"),
            ("goal-contracts", "workflows"),
            ("capability-health", "agents"),
            ("capability-health", "skills"),
            ("capability-health", "workflows"),
        )
        for checker, section in cases:
            with self.subTest(checker=checker, section=section):
                data = copy.deepcopy(self.manifest)
                data[section] = {} if section == "profiles" else []
                if section == "skills":
                    data["optional_skills"] = []
                self.write_manifest(data)
                result = self.shell('bash "scripts/check-$1.sh" --summary-json', checker)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("fail", json.loads(result.stdout)["status"])
                self.assertGreater(json.loads(result.stdout)["failures"], 0)


if __name__ == "__main__":
    unittest.main()
