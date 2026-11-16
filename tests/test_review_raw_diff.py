"""Execute published review/preflight recipes against real Git configuration."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

from agent_dev_kit.model import Manifest
from agent_dev_kit.targets import load_target_contract, render_asset


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS: list[dict[str, object]] = []


class ReviewRawDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.git_binary = shutil.which("git")
        cls.bash_binary = shutil.which("bash")
        if cls.git_binary is None or cls.bash_binary is None:
            raise AssertionError("Git and Bash are required to exercise published recipes")
        manifest = Manifest.load(ROOT)
        asset = next(item for item in manifest.all_assets("skill")
                     if item.name == "adk-code-review-loop")
        rendered = render_asset(manifest, load_target_contract(manifest, "claude-code"), asset)
        reference = next(item for item in rendered if item.destination.endswith(
            "/references/review-evidence-template.md"))
        cls.reference_sha256 = hashlib.sha256(reference.content).hexdigest()
        block = re.search(r"```bash\n(.*?)\n```", reference.content.decode(), re.DOTALL)
        if block is None:
            raise AssertionError("Published snapshot recipe is missing")
        cls.commands = block.group(1).split("<project-lint-cmd>", 1)[0]

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="adk-raw-review-")
        self.addCleanup(temporary.cleanup)
        self.area = Path(temporary.name)
        self.repo = self.area / "consumer"
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update({"LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
                         "GIT_CONFIG_GLOBAL": os.devnull})
        self.git("init", "-q")
        self.git("config", "user.name", "ADK fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "diff.autoRefreshIndex", "true")
        (self.repo / "payload.txt").write_text("original required value\n", encoding="utf-8")
        (self.repo / "stat-only.txt").write_text("unchanged\n", encoding="utf-8")
        (self.repo / ".gitattributes").write_text("payload.txt diff=opaque\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "baseline")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *arguments: str, cwd: Path | None = None) -> str:
        result = subprocess.run([self.git_binary, *arguments], cwd=cwd or self.repo,
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def helper(self, name: str, response: str) -> tuple[Path, Path]:
        marker = self.area / (name + ".called")
        script = self.area / (name + ".sh")
        script.write_text("#!/bin/sh\nprintf 'called\\n' >> " + shlex.quote(str(marker))
                          + "\n" + response + "\n", encoding="utf-8")
        script.chmod(0o700)
        return script, marker

    def snapshot(self, target: str, *, cwd: Path | None = None) -> str:
        index = self.repo / ".git/index"
        before_index = index.read_bytes()
        before_files = {str(path.relative_to(self.repo)): path.read_bytes()
                        for path in self.repo.rglob("*")
                        if path.is_file() and ".git" not in path.relative_to(self.repo).parts}
        before_head = self.git("rev-parse", "HEAD")
        result = subprocess.run(
            [self.bash_binary, "--noprofile", "--norc", "-euc", self.commands],
            cwd=cwd or self.repo,
            env={**self.env, "review_target": target, "review_base": self.base},
            capture_output=True, text=True, timeout=10,
        )
        RECEIPTS.append({"test": self.id(), "target": target,
                         "reference_sha256": self.reference_sha256,
                         "command": self.commands, "exit": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr,
                         "index_preserved": index.read_bytes() == before_index})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(index.read_bytes(), before_index, "Snapshot refreshed the index")
        self.assertEqual(self.git("rev-parse", "HEAD"), before_head)
        after_files = {str(path.relative_to(self.repo)): path.read_bytes()
                       for path in self.repo.rglob("*")
                       if path.is_file() and ".git" not in path.relative_to(self.repo).parts}
        self.assertEqual(after_files, before_files, "Snapshot changed the worktree")
        return result.stdout

    def test_textconv_and_external_diff_do_not_hide_selected_changes(self) -> None:
        for kind in ("textconv", "external"):
            helper, marker = self.helper(kind, "printf 'same projection\\n'" if kind == "textconv" else "exit 0")
            key = "diff.opaque.textconv" if kind == "textconv" else "diff.external"
            self.git("config", key, str(helper))
            (self.repo / "payload.txt").write_text("staged actual change\n", encoding="utf-8")
            self.git("add", "payload.txt")
            (self.repo / "payload.txt").write_text("working tree actual change\n", encoding="utf-8")
            (self.repo / "untracked.txt").write_text("UNTRACKED_BODY\n", encoding="utf-8")
            for target, expected, excluded in (
                ("staged", "+staged actual change", "+working tree actual change"),
                ("working-tree", "+working tree actual change", "+staged actual change"),
            ):
                with self.subTest(helper=kind, target=target):
                    output = self.snapshot(target)
                    self.assertIn(expected, output)
                    self.assertNotIn(excluded, output)
                    self.assertIn("MM payload.txt", output)
                    self.assertIn("?? untracked.txt", output)
                    self.assertNotIn("UNTRACKED_BODY", output)
                    self.assertFalse(marker.exists(), f"Snapshot executed {kind}")
            self.git("-c", "diff.external=", "commit", "-qm", "selected committed change")
            with self.subTest(helper=kind, target="whole-branch"):
                output = self.snapshot("whole-branch")
                self.assertIn("+staged actual change", output)
                self.assertNotIn("+working tree actual change", output)
                self.assertIn("base " + self.base + " merge-base " + self.base, output)
                self.assertFalse(marker.exists(), f"Snapshot executed {kind}")
            self.git("config", "--unset", key)
            # Restore this fixture between independent driver variants.
            self.git("reset", "--hard", self.base)
            (self.repo / "untracked.txt").unlink()
            if marker.exists():
                marker.unlink()

    def test_relative_and_color_configuration_do_not_reduce_raw_scope(self) -> None:
        nested = self.repo / "inside"
        nested.mkdir()
        self.git("config", "diff.relative", "true")
        self.git("config", "color.ui", "always")
        (self.repo / "payload.txt").write_text("outside nested directory\n", encoding="utf-8")
        output = self.snapshot("working-tree", cwd=nested)
        self.assertIn("+outside nested directory", output)
        self.assertNotIn("\x1b[", output)

    def test_configured_submodule_omission_does_not_hide_gitlink_update(self) -> None:
        child = self.area / "dependency-source"
        child.mkdir()
        self.git("init", "-q", cwd=child)
        (child / "version.txt").write_text("before\n", encoding="utf-8")
        self.git("add", ".", cwd=child)
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "dependency before", cwd=child)
        old = self.git("rev-parse", "HEAD", cwd=child).strip()
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "dependency")
        self.git("commit", "-qm", "add dependency")
        dependency = self.repo / "dependency"
        (dependency / "version.txt").write_text("after\n", encoding="utf-8")
        self.git("add", "version.txt", cwd=dependency)
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "dependency after", cwd=dependency)
        new = self.git("rev-parse", "HEAD", cwd=dependency).strip()
        self.git("add", "dependency")
        self.git("config", "diff.ignoreSubmodules", "all")
        output = self.snapshot("staged")
        self.assertIn("-Subproject commit " + old, output)
        self.assertIn("+Subproject commit " + new, output)

    def test_fsmonitor_is_not_called_by_the_snapshot(self) -> None:
        helper, marker = self.helper("fsmonitor", "printf 'fixture-token\\0/\\0'")
        self.git("config", "core.fsmonitor", str(helper))
        self.git("config", "core.fsmonitorHookVersion", "2")
        (self.repo / "payload.txt").write_text("actual change\n", encoding="utf-8")
        output = self.snapshot("working-tree")
        self.assertIn("+actual change", output)
        self.assertFalse(marker.exists(), "Snapshot executed FSMonitor")

    def test_shipped_status_preflights_preserve_index_and_do_not_run_fsmonitor(self) -> None:
        paths = (
            "skills/adk-branch-closeout/SKILL.md",
            "skills/adk-worktree-governance/SKILL.md",
            "skills/adk-worktree-governance/references/worktree-operation-boundaries.md",
            "skills/adk-repo-drift-remediation/SKILL.md",
        )
        helper, marker = self.helper("preflight-fsmonitor", "printf 'fixture-token\\0/\\0'")
        self.git("config", "core.fsmonitor", str(helper))
        self.git("config", "core.fsmonitorHookVersion", "2")
        untouched = self.repo / "stat-only.txt"
        index = self.repo / ".git/index"
        for relative in paths:
            source = (ROOT / relative).read_text(encoding="utf-8")
            commands = re.findall(r"(?m)(?:^|`)(git [^`\n]*\bstatus\b[^`\n]*)(?:`|$)", source)
            self.assertTrue(commands, relative)
            for command in commands:
                with self.subTest(source=relative, command=command):
                    info = untouched.stat()
                    os.utime(untouched, ns=(info.st_atime_ns, info.st_mtime_ns + 2_000_000_000))
                    before = index.read_bytes()
                    if marker.exists():
                        marker.unlink()
                    result = subprocess.run(shlex.split(command), cwd=self.repo, env=self.env,
                                            capture_output=True, text=True, timeout=10)
                    RECEIPTS.append({"test": self.id(), "source": relative, "command": command,
                                     "exit": result.returncode, "stdout": result.stdout,
                                     "stderr": result.stderr,
                                     "index_preserved": index.read_bytes() == before,
                                     "fsmonitor_called": marker.exists()})
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(index.read_bytes(), before, "Preflight refreshed index")
                    self.assertFalse(marker.exists(), "Preflight executed FSMonitor")


if __name__ == "__main__":
    unittest.main()
