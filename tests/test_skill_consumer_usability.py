"""Exercise published consumer interfaces; no native agent or model is invoked."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

import yaml

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.intent_boundary import TASK_PACKAGE_SCHEMA, validate_task_package
from agent_dev_kit.matcher import match_text
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
OPTIONAL = ("adk-skill-composition-governance", "adk-security-supply-chain")
WORKER_REFERENCE = "references/parallel-worktree-task-package.md"


def section(text: str, heading: str) -> str:
    return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


class SkillConsumerUsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = Manifest.load(ROOT)
        cls.temporary = tempfile.TemporaryDirectory(prefix="adk-consumer-usability-")
        cls.exports = {}
        for target in ("claude-code", "opencode"):
            result = export_assets(
                cls.manifest, target, Path(cls.temporary.name), ["team-core"], OPTIONAL,
            )
            cls.exports[target] = Path(result["output"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def entry(self, target: str, name: str) -> Path:
        return next(path for path in self.exports[target].rglob("SKILL.md")
                    if path.parent.name == name)

    def test_published_catalog_queries_cover_core_and_nested_optional(self) -> None:
        text = (ROOT / "optional-skills" / OPTIONAL[0] / "SKILL.md").read_text()
        commands = [shlex.split(line) for line in text.splitlines()
                    if line.startswith("bash scripts/devkit.sh catalog find ")]
        self.assertTrue(commands)
        observed = {}
        for command in commands:
            result = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=15,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            for line in result.stdout.splitlines()[1:]:
                kind, name, _description, path = line.split("\t", 3)
                self.assertIn(kind, {"skill", "optional-skill"})
                self.assertNotIn(name, observed, "inventory must not duplicate identities")
                observed[name] = path
        expected = {row["name"]: row["path"] for field in ("skills", "optional_skills")
                    for row in self.manifest.data[field]}
        self.assertEqual(expected, observed)
        self.assertEqual(
            "optional-skills/adk-data-fetch/adk-email-imap-fetch/SKILL.md",
            observed["adk-email-imap-fetch"],
        )

    def test_exported_optional_source_helpers_have_scoped_fallback(self) -> None:
        for target, output in self.exports.items():
            self.assertFalse((output / "scripts/devkit.sh").exists())
            self.assertFalse((output / "manifest.json").exists())
            for name in OPTIONAL:
                with self.subTest(target=target, skill=name):
                    text = self.entry(target, name).read_text()
                    commands = section(text, "## Commands")
                    preamble = commands.split("```", 1)[0]
                    # The real package lacks the helper: source-only checks
                    # need a stated entry condition and an honest missing path.
                    for required in ("已核", "ADK 源码根", "helper", "纯 Skill",
                                     "目标项目", "not-run", "不安装"):
                        self.assertIn(required, preamble)
                    self.assertIn("bash scripts/devkit.sh", commands)
                    references = self.entry(target, name).parent / "references"
                    self.assertTrue(references.is_dir())

    def test_archive_handoff_artifact_retains_readonly_authority(self) -> None:
        prompts = (
            "请检查已有归档元数据，先给只读报告。",
            "请修复归档元数据，已明确授权修改 docs/archive 的 topic 和 meta，不删除历史文件。",
        )
        for prompt in prompts:
            result = match_text(self.manifest, prompt)
            self.assertEqual("adk-archive-governance", result.get("skill"), result)
            self.assertEqual("read-only", result.get("effect_ceiling"), result)
            self.assertEqual("deny", result.get("mutation_permission"), result)
        for target in self.exports:
            with self.subTest(target=target):
                text = self.entry(target, "adk-archive-governance").read_text()
                evidence = section(text, "## Evidence Template")
                block = re.search(r"(?ms)^```(?:md|yaml)\n(.*?)^```", evidence)
                self.assertIsNotNone(block)
                template = yaml.safe_load(block.group(1))
                self.assertTrue({"issues", "checks", "remaining"} <= template.keys())
                handoff = template.get("handoff")
                self.assertIsInstance(handoff, dict, "repair needs an existing implementation owner")
                self.assertTrue({"implementation_owner", "authorized_task_ref", "candidate_patch_or_task",
                                 "verification"} <= handoff.keys())
                workflow = section(text, "## Workflow")
                for retained in ("旧 hash", "实测 hash", "可信原件", "已批准", "未知", "needs-fix"):
                    self.assertIn(retained, workflow)
                for boundary in ("只读", "既有", "不重复", "实施", "候选"):
                    self.assertIn(boundary, workflow)

    def mapped_worker(self, target: str, kind: str) -> dict:
        entry = self.entry(target, "adk-parallel-agent-governance")
        text = (entry.parent / WORKER_REFERENCE).read_text()
        blocks = re.findall(r"(?ms)^```md\n(.*?)^```", text)
        self.assertEqual(1, len(blocks))
        fields = set(re.findall(r"(?m)^([a-z_]+):", blocks[0]))
        self.assertNotIn("structured_output_schema", fields, "the default remains a human envelope")
        mappings = {}
        for source_fields, destination in re.findall(
            r"(?m)^\| ([a-z_ /]+) \| (context|constraints|done_when|verification|artifacts|blockers) \|$",
            text,
        ):
            for field in source_fields.split(" / "):
                self.assertNotIn(field, mappings)
                mappings[field] = destination
        required_scope = {"scope_read", "scope_write", "must_not_touch", "global_constraints", "interfaces"}
        self.assertTrue(required_scope <= mappings.keys(), mappings)
        self.assertTrue(all(mappings[field] == "constraints" for field in required_scope))
        self.assertEqual("context", mappings.get("owner"))
        self.assertEqual("done_when", mappings.get("ready_to_handoff"))
        payload = {
            "structured_output_schema": TASK_PACKAGE_SCHEMA,
            "strict_schema_decision": True,
            "refusal_handling": "stop if the authorized scope cannot be kept",
            "context": "Pinned source snapshot; human envelope values follow",
            "constraints": [], "done_when": [], "verification": [], "artifacts": [], "blockers": [],
            "primary_action": "review source" if kind == "research" else "implement the approved task",
            "action_mode": "read-only" if kind == "research" else "workspace-write",
            "goal": "Close the bounded task with evidence",
            "work_item_kind": kind,
            "question_to_resolve": "Does the source satisfy the approved acceptance?",
            "evidence_required": ["source snapshot and verifier output"],
            "implementation_permission": "forbidden" if kind == "research" else "approved",
            "exit_gate": "evidence-reviewed" if kind == "research" else "implementation-verified",
            "handoff_target": "parent owner",
            "retention_decision": "keep-final",
        }
        self.assertEqual(fields - payload.keys(), mappings.keys())
        sentinels = {field: f"bounded-{field}-evidence" for field in mappings}
        for field, destination in mappings.items():
            value = sentinels[field]
            if destination == "context":
                payload[destination] += f"; {field}: {value}"
            elif destination == "constraints":
                payload[destination].append(f"{field}: {value}")
            else:
                payload[destination].append(value)
        encoded = json.dumps(payload)
        for sentinel in sentinels.values():
            self.assertIn(sentinel, encoded, "mapping must retain scope, owner and handoff evidence")
        self.assertEqual((), validate_task_package(payload))
        return payload

    def test_exported_human_worker_mapping_uses_existing_strict_v2(self) -> None:
        for target in self.exports:
            for kind in ("research", "implementation"):
                with self.subTest(target=target, kind=kind):
                    payload = self.mapped_worker(target, kind)
                    for field in ("scope_read", "scope_write", "global_constraints", "interfaces",
                                  "ready_to_handoff"):
                        errors = validate_task_package({**payload, field: "extra top-level field"})
                        self.assertTrue(any("unexpected fields" in error for error in errors), errors)
                    if kind == "research":
                        errors = validate_task_package({**payload, "implementation_permission": "approved"})
                        self.assertIn("research requires implementation_permission=forbidden", errors)
            text = (self.entry(target, "adk-parallel-agent-governance").parent / WORKER_REFERENCE).read_text()
            for term in ("人类", "v2 JSON", "constraints", "context", "状态", "报告"):
                self.assertIn(term, text)

    def test_exported_recovery_note_distinguishes_envelope_and_payload(self) -> None:
        for target in self.exports:
            reference = self.entry(target, "adk-planning-execution-loop").parent / "references/long-task-recovery.md"
            line = next(line for line in reference.read_text().splitlines() if "Task Package v2" in line)
            for term in ("scope_read/scope_write/must_not_touch", "constraints", "context",
                         "人类", "JSON", "implementation"):
                self.assertIn(term, line)


if __name__ == "__main__":
    unittest.main()
