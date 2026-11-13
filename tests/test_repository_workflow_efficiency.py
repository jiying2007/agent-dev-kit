"""Tests for lean repository-workflow Skill source contracts; not runtime effects."""
from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = {
    "commit": "skills/adk-commit-pr-quality-gate/SKILL.md",
    "worktree": "skills/adk-worktree-governance/SKILL.md",
    "closeout": "skills/adk-branch-closeout/SKILL.md",
}

class RepositoryWorkflowSkillEfficiencyTests(unittest.TestCase):
    def read(self, key: str) -> str:
        return (ROOT / PATHS[key]).read_text(encoding="utf-8")

    def test_cases_are_bounded_and_not_behavior_claims(self) -> None:
        data = json.loads((ROOT / "tests/fixtures/repository_workflow_skill_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "adk-repository-workflow-skill-efficiency/v1")
        self.assertEqual(data["evaluation_status"], "not-measured")
        self.assertGreaterEqual(len(data["cases"]), 18)
        ids = [x["id"] for x in data["cases"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({x["skill"] for x in data["cases"]}, set(PATHS))
        for item in data["cases"]:
            for key in ("input", "expected", "forbidden"):
                self.assertTrue(item[key].strip())

    def test_commit_mode_and_security_boundaries(self) -> None:
        c = self.read("commit")
        for marker in ("message-only", "PR-readiness", "high-risk",
                       "Runtime Control Plane", "permission_profile_decision",
                       "deny-path test", "Config Drift Decision", "human owner"):
            self.assertIn(marker, c)
        self.assertIn("不授予 git commit", c)
        self.assertIn("不可信 PR", c)

    def test_worktree_and_closeout_are_explicitly_authorized(self) -> None:
        w,c = self.read("worktree"), self.read("closeout")
        for marker in ("stay-current", "Dirty Worktree Decision", "Automation Risk Decision",
                       "Heartbeat / Staleness Threshold", "scope_write", "destructive cleanup"):
            self.assertIn(marker, w)
        self.assertIn("不得自动 commit、stash、reset", w)
        for marker in ("status-only", "create-pr", "merge", "fresh-main",
                       "destructive cleanup approval"):
            self.assertIn(marker, c)
        self.assertIn("只读", c)
        self.assertIn("不得 PR/merge", c)

    def test_reference_paths_exist_only_on_demand(self) -> None:
        for key,ref in (
            ("commit", "references/pr-risk-gates.md"),
            ("worktree", "references/worktree-operation-boundaries.md"),
            ("closeout", "references/closeout-options.md"),
        ):
            self.assertIn(ref, self.read(key))
            self.assertTrue((ROOT / Path(PATHS[key]).parent / ref).is_file())
        desc = (ROOT / "docs/changes/20261113-repository-workflow-efficiency/design.md").read_text(encoding="utf-8")
        self.assertIn("not-measured", desc)
        self.assertIn("No new Skill/Agent/Workflow", desc)

if __name__ == "__main__":
    unittest.main()
