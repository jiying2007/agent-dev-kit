"""Execute shipped synthetic examples; this is not model or scanner evaluation."""
from __future__ import annotations

from dataclasses import asdict
import contextlib
import io
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import unittest

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest


ROOT = Path(__file__).resolve().parents[1]
SKILL = "adk-security-supply-chain"
DIRECTORY = ROOT / "optional-skills" / SKILL
REFERENCE = "references/skill-scan-coverage.md"


def example(reference: Path) -> str:
    blocks = re.findall(r"(?ms)^```python\n(.*?)^```\s*$", reference.read_text(encoding="utf-8"))
    if len(blocks) != 1:
        raise AssertionError("expected one published synthetic serialization example")
    return blocks[0]


class SkillSerializationMethodTests(unittest.TestCase):
    def test_published_example_exercises_paths_without_echoing_values(self) -> None:
        code = example(DIRECTORY / REFERENCE)
        expected = {
            "repr_excluded": True,
            "direct_leak_observed": True,
            "nested_leak_observed": True,
            "allowlist_excluded": True,
            "public_fields_preserved": True,
        }
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "serialization_example.py"
            script.write_text(code, encoding="utf-8")
            for optimization in ([], ["-O"], ["-OO"]):
                with self.subTest(optimization=optimization):
                    completed = subprocess.run(
                        [sys.executable, "-I", *optimization, str(script)],
                        cwd=temporary, capture_output=True, text=True, timeout=10,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(completed.stderr, "")
                    # Exact boolean-only output rejects leaked fixture values too.
                    self.assertEqual(json.loads(completed.stdout), expected)

    def test_actual_published_allowlist_preserves_changed_nested_public_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            script = Path(temporary) / "serialization_example.py"
            script.write_text(example(DIRECTORY / REFERENCE), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                namespace = runpy.run_path(str(script))
            self.assertEqual(output.getvalue(), "")
            holder_type = namespace["CredentialHolder"]
            event_type = namespace["Event"]
            public_event = namespace["public_event"]
            for index, sentinel in enumerate(("SYNTHETIC_ALPHA", "SYNTHETIC_β", "")):
                with self.subTest(case=index):
                    endpoint = f"https://host-{index}.example.invalid"
                    holder = holder_type(endpoint, sentinel)
                    event = event_type(f"component-{index}", holder, f"status-{index}")
                    before = asdict(event)
                    if sentinel:
                        self.assertNotIn(sentinel, repr(holder))
                        self.assertIn(sentinel, json.dumps(asdict(holder), ensure_ascii=False))
                        self.assertIn(sentinel, json.dumps(before, ensure_ascii=False))
                    safe = public_event(event)
                    self.assertEqual(safe, {
                        "component": event.component,
                        "client": {"endpoint": endpoint},
                        "status": event.status,
                    })
                    encoded = json.dumps(safe, ensure_ascii=False)
                    if sentinel:
                        self.assertNotIn(sentinel, encoded)
                    self.assertNotIn("credential", safe["client"])
                    self.assertEqual(asdict(event), before, "output filtering must not mutate input")

    def test_conditional_reference_survives_explicit_optional_export(self) -> None:
        manifest = Manifest.load(ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            for target in ("claude-code", "opencode"):
                with self.subTest(target=target):
                    exported = export_assets(
                        manifest, target, Path(temporary), ["core"],
                        optional_skills=[SKILL],
                    )
                    self.assertEqual(exported["status"], "pass")
                    entry = next(path for path in Path(exported["output"]).rglob("SKILL.md")
                                 if path.parent.name == SKILL)
                    body = entry.read_text(encoding="utf-8")
                    step = next(line for line in body.splitlines() if line.startswith("7. 敏感信息审查"))
                    self.assertIn("涉及", step)
                    self.assertIn("整对象输出", step)
                    self.assertIn(REFERENCE, step)
                    reference = entry.parent / REFERENCE
                    self.assertTrue(reference.is_file())
                    self.assertEqual(example(reference), example(DIRECTORY / REFERENCE))
                    guidance = reference.read_text(encoding="utf-8")
                    self.assertIn("repr=False", guidance)
                    self.assertIn("unverified", guidance)
                    self.assertIn("diff", guidance)
                    self.assertIn("不执行", guidance)
                    self.assertIn("不回显", guidance)


if __name__ == "__main__":
    unittest.main()
