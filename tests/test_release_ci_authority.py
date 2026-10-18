"""Offline negative tests for the real release workflow's CI-authority Python block."""
from __future__ import annotations

import io
import json
import os
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / ".github/workflows/release.yml"
SHA = "a" * 40
RUN = {
    "id": 1234,
    "name": "agent-dev-kit-ci",
    "status": "completed",
    "conclusion": "success",
    "event": "push",
    "head_branch": "main",
    "head_sha": SHA,
    "path": ".github/workflows/ci.yml",
}


def workflow_authority_block() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    segment = source.split("      - name: Validate successful main CI reuse\n", 1)[1]
    segment = segment.split("      - name: Install CI dependencies\n", 1)[0]
    code = segment.split("          python - <<'PY'\n", 1)[1]
    code = code.split("\n          PY\n", 1)[0]
    return textwrap.dedent(code) + "\n"


class ReleaseCiAuthorityTest(unittest.TestCase):
    def run_case(self, payload: object, run_id: str = "1234", sha: str = SHA) -> str:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "github-output"
            data = json.dumps(payload).encode("utf-8")
            env = {
                "GITHUB_OUTPUT": str(out),
                "GITHUB_REPOSITORY": "jiying2007/agent-dev-kit",
                "GITHUB_API_URL": "https://api.github.com",
                "GH_TOKEN": "test-token-never-sent",
                "REQUESTED_MAIN_CI_RUN_ID": run_id,
                "CALLED_RELEASE_COMMIT": sha,
            }
            with patch.dict(os.environ, env), patch("urllib.request.urlopen", return_value=io.BytesIO(data)):
                exec(compile(workflow_authority_block(), str(SOURCE), "exec"), {"__name__": "__main__"})
            return out.read_text(encoding="utf-8")

    def test_exact_main_run_allows_quick_reuse(self) -> None:
        self.assertIn("verified_main_ci_reuse=true", self.run_case(dict(RUN)))

    def test_orphan_repair_requires_historical_main_ci_and_full_suite(self) -> None:
        payload = {"workflow_runs": [
            {**RUN, "event": "pull_request"},
            dict(RUN),
        ]}
        self.assertIn("verified_main_ci_reuse=false", self.run_case(payload, run_id=""))

    def test_forged_main_ci_and_untrusted_run_id_fail(self) -> None:
        for field, invalid in (
            ("id", 4321),
            ("name", "fake-workflow"),
            ("path", "untrusted.yml"),
            ("event", "pull_request"),
            ("head_branch", "feature"),
            ("head_sha", "b" * 40),
            ("status", "in_progress"),
            ("conclusion", "skipped"),
        ):
            with self.subTest(field=field):
                with self.assertRaises(SystemExit):
                    self.run_case({**RUN, field: invalid})
        with self.assertRaises(SystemExit):
            self.run_case(RUN, run_id="not-numeric")

    def test_missing_or_corrupt_orphan_evidence_fails(self) -> None:
        for value in ({"workflow_runs": []}, {"workflow_runs": [{**RUN, "event": "pull_request"}]}, []):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    self.run_case(value, run_id="")
        with self.assertRaises(SystemExit):
            self.run_case({"workflow_runs": [RUN]}, run_id="", sha="b" * 40)


if __name__ == "__main__":
    unittest.main()
