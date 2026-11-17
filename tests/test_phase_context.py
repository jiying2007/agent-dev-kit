from __future__ import annotations

import json
import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit import matcher, phase_context, skill_relationships, _matcher_kernel
from agent_dev_kit.phase_context import (
    _contract,
    _load_contract,
    _resolve_selector,
    _skill_entries,
    resolve_delivery_lifecycle,
    resolve_phase_context,
)

ROOT = Path(__file__).resolve().parents[1]


class PhaseContextContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = Manifest.load(ROOT)
        cls.entries = _skill_entries(cls.manifest)

    def test_manifest_has_no_phase_to_skill_path_mirror(self) -> None:
        for section in ("context_layers", "embedded_context_layers"):
            value = self.manifest.data.get(section)
            self.assertIsInstance(value, dict)
            self.assertNotIn("L2-phase-triggered", value)

    def test_review_phase_uses_one_primary_without_language_duplicate(self) -> None:
        result = resolve_phase_context(self.manifest, "general", "review")
        self.assertEqual(result["schema"], "adk-phase-context-resolution/v2")
        self.assertEqual(result["status"], "pass")
        rows = {item["name"]: item for item in result["skills"]}
        self.assertEqual(rows["adk-code-review-loop"]["runtime_role"], "primary")
        self.assertNotIn("adk-chinese-code-review", rows)
        self.assertEqual(
            [item["name"] for item in result["skills"] if item["runtime_role"] == "primary"],
            ["adk-code-review-loop"],
        )

    def test_verify_phase_separates_test_execution_from_completion_gate(self) -> None:
        result = resolve_phase_context(self.manifest, "general", "verify")
        rows = {item["name"]: item for item in result["skills"]}
        self.assertEqual(rows["adk-test-strategy"]["runtime_role"], "primary")
        self.assertEqual(rows["adk-artifact-gating"]["runtime_role"], "governance")
        self.assertNotIn("adk-verification-before-completion", rows)

    def test_driver_phase_contains_implementation_bringup_and_interrupt_dma(self) -> None:
        result = resolve_phase_context(self.manifest, "embedded", "driver-development")
        names = {item["name"] for item in result["skills"]}
        self.assertTrue(
            {
                "adk-driver-implementation",
                "adk-driver-bringup-checklist",
                "adk-interrupt-dma-patterns",
            }.issubset(names),
            names,
        )

    def test_delivery_lifecycle_is_review_then_completion_then_commit_then_closeout(self) -> None:
        result = resolve_delivery_lifecycle(self.manifest)
        self.assertEqual(result["schema"], "adk-delivery-lifecycle-resolution/v2")
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["pre_review_requirements"], ["verification-evidence"])
        self.assertEqual(
            result["relationship_semantics_source"],
            "manifests/skill_relationship_contracts_v2.json",
        )
        self.assertEqual(
            [(item["stage"], item["name"]) for item in result["steps"]],
            [
                ("review", "adk-code-review-loop"),
                ("completion", "adk-verification-before-completion"),
                ("commit-pr", "adk-commit-pr-quality-gate"),
                ("closeout", "adk-branch-closeout"),
            ],
        )

    def test_skill_selector_fails_closed_on_role_drift(self) -> None:
        with self.assertRaisesRegex(ManifestError, "role drift"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {
                    "kind": "skill",
                    "skill": "adk-code-review-loop",
                    "expected_runtime_role": "supporting",
                },
            )

    def test_unknown_skill_fails_closed(self) -> None:
        with self.assertRaisesRegex(ManifestError, "unknown Skill"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {"kind": "skill", "skill": "adk-does-not-exist", "expected_runtime_role": "primary"},
            )

    def test_non_unique_group_cannot_be_promoted_to_exactly_one_primary(self) -> None:
        with self.assertRaisesRegex(ManifestError, "exactly one primary"):
            _resolve_selector(
                self.manifest,
                self.entries,
                {
                    "kind": "selection-group",
                    "selection_group": "debugging",
                    "include_runtime_roles": ["primary"],
                    "primary_cardinality": "exactly-one",
                },
            )

    def test_phase_resource_cannot_escape_repository_root(self) -> None:
        contract, digest = _contract(self.manifest)
        mutated = json.loads(json.dumps(contract))
        mutated["domains"]["general"]["review"]["resources"] = ["../../outside"]
        with patch("agent_dev_kit.phase_context._contract", return_value=(mutated, digest)):
            with self.assertRaisesRegex(ManifestError, "escapes allowed root"):
                resolve_phase_context(self.manifest, "general", "review")

    def test_contract_schema_rejects_unknown_top_level_field(self) -> None:
        contract_path = ROOT / "manifests" / "phase_context_contract_v2.json"
        schema_path = ROOT / "schemas" / "phase-context-contract-v2.schema.json"
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["unexpected_authority"] = True
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            bad_contract = temp_root / "contract.json"
            local_schema = temp_root / "schema.json"
            bad_contract.write_text(json.dumps(contract), encoding="utf-8")
            local_schema.write_bytes(schema_path.read_bytes())
            with self.assertRaisesRegex(ManifestError, "schema validation failed"):
                _load_contract(
                    bad_contract.read_bytes(),
                    local_schema.read_bytes(),
                )


class ContentCacheIdentityTests(unittest.TestCase):
    """A saved timestamp cannot stand in for the bytes a consumer is using."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = Manifest(self.root, Manifest.load(ROOT).data, self.root / "manifest.json")
        for relative in (
            phase_context._CONTRACT, phase_context._CONTRACT_SCHEMA,
            skill_relationships._CONTRACT, skill_relationships._CONTRACT_SCHEMA,
            matcher._CONTRACT,
        ):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        for section in ("skills", "optional_skills"):
            for entry in self.manifest.data[section]:
                destination = self.root / entry["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / entry["path"], destination)
        for loader in (phase_context._load_contract, skill_relationships._load_contract,
                       matcher._load_contract, _matcher_kernel._frontmatter_cached):
            loader.cache_clear()
            self.addCleanup(loader.cache_clear)

    def replace_preserving_stat(self, path: Path, old: bytes, new: bytes) -> bytes:
        raw, before = path.read_bytes(), path.stat()
        self.assertEqual(len(old), len(new))
        self.assertIn(old, raw)
        changed = raw.replace(old, new, 1)
        path.write_bytes(changed)
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = path.stat()
        self.assertEqual((before.st_size, before.st_mtime_ns), (after.st_size, after.st_mtime_ns))
        return changed

    def test_phase_valid_replacement_refreshes_semantics_and_matching_digest(self) -> None:
        before = resolve_phase_context(self.manifest, "general", "route")
        self.assertEqual(before["skills"][0]["name"], "adk-runtime-router")
        raw = self.replace_preserving_stat(self.root / phase_context._CONTRACT,
                                          b'"runtime-routing"', b'"goal-authoring" ')
        after = resolve_phase_context(self.manifest, "general", "route")
        self.assertEqual(after["skills"][0]["name"], "adk-goal-authoring")
        self.assertEqual(after["contract_sha256"], hashlib.sha256(raw).hexdigest())

    def test_relationship_valid_replacement_refreshes_semantics_and_digest(self) -> None:
        before = skill_relationships.resolve_skill_relationships(self.manifest)
        self.assertEqual(before["typed_relationships"][0]["type"], "handoff")
        raw = self.replace_preserving_stat(self.root / skill_relationships._CONTRACT,
                                          b'"requirement": "when-applicable"',
                                          b'"requirement": "required"       ')
        after = skill_relationships.resolve_skill_relationships(self.manifest)
        self.assertEqual(after["typed_relationships"][0]["requirement"], "required")
        self.assertEqual(after["contract_sha256"], hashlib.sha256(raw).hexdigest())

    def test_content_contract_valid_replacement_updates_selection_group(self) -> None:
        self.assertEqual(matcher.resolve_skill_content(self.manifest, "adk-runtime-router")["selection_group"],
                         "runtime-routing")
        self.replace_preserving_stat(self.root / matcher._CONTRACT,
                                     b'"runtime-routing"', b'"updated-routing"')
        self.assertEqual(matcher.resolve_skill_content(self.manifest, "adk-runtime-router")["selection_group"],
                         "updated-routing")

    def test_frontmatter_valid_and_invalid_replacements_are_read(self) -> None:
        path = self.root / "skills/adk-runtime-router/SKILL.md"
        self.assertEqual(_matcher_kernel._frontmatter(path)["name"], "adk-runtime-router")
        self.replace_preserving_stat(path, b"name: adk-runtime-router", b"name: adk-updated-router")
        self.assertEqual(_matcher_kernel._frontmatter(path)["name"], "adk-updated-router")
        self.replace_preserving_stat(path, b"---", b"xxx")
        with self.assertRaisesRegex(ManifestError, "frontmatter is missing"):
            _matcher_kernel._frontmatter(path)

    def test_changed_invalid_contracts_cannot_reuse_previous_success(self) -> None:
        for module in (phase_context, skill_relationships, matcher):
            with self.subTest(module=module.__name__):
                module._contract(self.manifest)
                self.replace_preserving_stat(self.root / module._CONTRACT, b'/v2"', b'/v9"')
                with self.assertRaises(ManifestError):
                    module._contract(self.manifest)

    def test_changed_schema_cannot_reuse_previous_validation(self) -> None:
        for module in (phase_context, skill_relationships):
            with self.subTest(module=module.__name__):
                module._contract(self.manifest)
                self.replace_preserving_stat(self.root / module._CONTRACT_SCHEMA,
                                             b'"type": "object"', b'"type": "string"')
                with self.assertRaisesRegex(ManifestError, "schema validation failed"):
                    module._contract(self.manifest)

    def test_unchanged_input_reuses_bounded_parsing_cache(self) -> None:
        for module in (phase_context, skill_relationships, matcher):
            with self.subTest(module=module.__name__):
                first = module._contract(self.manifest)
                stats = module._load_contract.cache_info()
                self.assertEqual(module._contract(self.manifest), first)
                after = module._load_contract.cache_info()
                self.assertEqual(after.misses, stats.misses)
                self.assertEqual(after.hits, stats.hits + 1)
                self.assertEqual(after.maxsize, 8)
        path = self.root / "skills/adk-runtime-router/SKILL.md"
        first = _matcher_kernel._frontmatter(path)
        stats = _matcher_kernel._frontmatter_cached.cache_info()
        self.assertEqual(_matcher_kernel._frontmatter(path), first)
        after = _matcher_kernel._frontmatter_cached.cache_info()
        self.assertEqual(after.misses, stats.misses)
        self.assertEqual(after.hits, stats.hits + 1)
        self.assertEqual(after.maxsize, 512)

    def test_removed_and_non_utf8_inputs_fail_after_warming(self) -> None:
        for module in (phase_context, skill_relationships, matcher):
            with self.subTest(module=module.__name__):
                module._contract(self.manifest)
                path = self.root / module._CONTRACT
                raw = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ManifestError, "missing"):
                    module._contract(self.manifest)
                path.write_bytes(b"\xff" + raw[1:])
                with self.assertRaises(ManifestError):
                    module._contract(self.manifest)

    def test_frontmatter_read_errors_and_invalid_utf8_are_manifest_errors(self) -> None:
        path = self.root / "skills/adk-runtime-router/SKILL.md"
        _matcher_kernel._frontmatter(path)
        original = path.read_bytes()
        self.replace_preserving_stat(path, original[:1], b"\xff")
        with self.assertRaisesRegex(ManifestError, "frontmatter is unreadable"):
            _matcher_kernel._frontmatter(path)
        path.unlink()
        with self.assertRaisesRegex(ManifestError, "frontmatter is unreadable"):
            _matcher_kernel._frontmatter(path)


if __name__ == "__main__":
    unittest.main()
