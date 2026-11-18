"""Offline execution of the release workflow's authority and publication steps."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

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

FAKE_GH = r'''
import hashlib
import json
import os
import re
import sys
from pathlib import Path

state_path = Path(os.environ["FAKE_RELEASE_STATE"])
state = json.loads(state_path.read_text())
args = sys.argv[1:]
if args[:2] == ["release", "view"]:
    release = state["releases"].get(args[2])
    if release is None:
        raise SystemExit(1)
    if "--json" in args:
        print("\n".join(release))
elif args[:2] == ["release", "create"]:
    tag = args[2]
    if tag in state["releases"]:
        raise SystemExit("release already exists")
    assets = {}
    for value in args[3:]:
        if value.startswith("--"):
            break
        path = Path(value)
        assets[path.name] = path.read_bytes().hex()
    # Reproduce the observed default that made a later historical publish latest.
    latest = next((value.split("=", 1)[1] for value in args if value.startswith("--latest=")), "true")
    if latest not in {"true", "false"}:
        raise SystemExit("invalid latest control")
    state["releases"][tag] = assets
    state["creates"].append(args)
    if latest == "true":
        state["latest"] = tag
    state_path.write_text(json.dumps(state))
elif args[:2] == ["release", "download"]:
    destination = Path(args[args.index("--dir") + 1])
    for name, content in state["releases"][args[2]].items():
        (destination / name).write_bytes(bytes.fromhex(content))
elif args[0] == "api":
    endpoint = next(value for value in args if value.startswith("repos/"))
    assets = state["releases"][endpoint.rsplit("/", 1)[1]]
    query = args[args.index("--jq") + 1]
    if query == ".immutable":
        print("true")
    elif query == ".assets[].name":
        print("\n".join(assets))
    else:
        match = re.search(r'select\(\.name == "([^"]+)"\) \| \.digest$', query)
        if match is None:
            raise SystemExit("unsupported fixture query")
        print("sha256:" + hashlib.sha256(bytes.fromhex(assets[match[1]])).hexdigest())
else:
    raise SystemExit("unsupported fixture command")
'''


def workflow_authority_block() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    segment = source.split("      - name: Validate successful main CI reuse\n", 1)[1]
    segment = segment.split("      - name: Install CI dependencies\n", 1)[0]
    code = segment.split("          python - <<'PY'\n", 1)[1]
    code = code.split("\n          PY\n", 1)[0]
    return textwrap.dedent(code) + "\n"


class ReleaseCiAuthorityTest(unittest.TestCase):
    def run_case(
        self, payload: object, run_id: str = "1234", sha: str = SHA,
        triggering_run_id: str = "1234", triggering_sha: str = SHA,
    ) -> str:
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
                "TRIGGERING_MAIN_CI_RUN_ID": triggering_run_id,
                "TRIGGERING_MAIN_CI_HEAD_SHA": triggering_sha,
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
        self.assertIn("verified_main_ci_reuse=false", self.run_case(
            payload, run_id="", triggering_run_id="5678", triggering_sha="b" * 40,
        ))

    def test_latest_selection_rejects_missing_or_mismatched_caller_identity(self) -> None:
        for overrides in (
            {"triggering_run_id": ""},
            {"triggering_run_id": "not-numeric"},
            {"triggering_run_id": "5678"},
            {"triggering_sha": ""},
            {"triggering_sha": "g" * 40},
            {"triggering_sha": "b" * 40},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(SystemExit):
                self.run_case(dict(RUN), **overrides)
        with self.assertRaises(SystemExit):
            self.run_case({"workflow_runs": [RUN]}, run_id="")

    def publish_case(self, root: Path, tag: str, outputs: dict[str, str]):
        """Run the actual Bash step; only the external GitHub service is simulated."""
        binary_dir = root / "bin"
        binary_dir.mkdir(exist_ok=True)
        gh = binary_dir / "gh"
        gh.write_text("#!" + sys.executable + "\n" + textwrap.dedent(FAKE_GH), encoding="utf-8")
        gh.chmod(0o755)
        state_path = root / "release-state.json"
        if not state_path.exists():
            state_path.write_text(json.dumps({"latest": "v11.3.15", "releases": {}, "creates": []}))
        workspace = root / tag
        dist = workspace / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        archive = dist / f"agent-dev-kit-{tag[1:]}.tar.gz"
        archive.write_bytes(b"prevalidated offline publication fixture\n")
        archive.with_suffix(archive.suffix + ".sha256").write_text(
            hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name + "\n",
        )
        (dist / "release-contract.json").write_text('{"evidence_scope":"test-only"}\n')

        workflow = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
        step = next(item for item in workflow["jobs"]["package"]["steps"]
                    if item["name"] == "Publish GitHub Release")
        env = {**os.environ, "PATH": str(binary_dir) + os.pathsep + os.environ["PATH"],
               "GITHUB_REPOSITORY": "jiying2007/agent-dev-kit", "FAKE_RELEASE_STATE": str(state_path)}
        # Resolve the real workflow wiring, so dropping or misbinding the output
        # cannot pass merely because a test injected the intended variable.
        for key, value in step["env"].items():
            output = re.fullmatch(r"\$\{\{ steps\.ci-reuse\.outputs\.([a-z_]+) \}\}", value)
            if output:
                env[key] = outputs.get(output[1], "")
            elif value == "${{ inputs.release_tag }}":
                env[key] = tag
            elif value == "${{ github.token }}":
                env[key] = "test-token-never-sent"
            else:
                self.fail("unhandled publication environment binding: " + value)
        result = subprocess.run(
            ["bash", "-c", step["run"]], cwd=workspace, env=env,
            capture_output=True, text=True, timeout=15,
        )
        return result, json.loads(state_path.read_text())

    def test_current_publication_advances_latest_and_historical_repair_preserves_it(self) -> None:
        current = dict(line.split("=", 1) for line in self.run_case(dict(RUN)).splitlines())
        historical_run = {**RUN, "id": 1200, "head_sha": "b" * 40}
        historical = dict(line.split("=", 1) for line in self.run_case(
            {"workflow_runs": [historical_run]}, run_id="", sha="b" * 40,
        ).splitlines())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, state = self.publish_case(root, "v11.4.3", current)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(state["latest"], "v11.4.3")
            self.assertIn("--latest=true", state["creates"][0])
            result, state = self.publish_case(root, "v11.4.2", historical)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(state["latest"], "v11.4.3")
            self.assertEqual(set(state["releases"]), {"v11.4.3", "v11.4.2"})
            self.assertIn("--latest=false", state["creates"][1])

    def test_existing_release_is_checked_without_republishing_or_changing_latest(self) -> None:
        outputs = dict(line.split("=", 1) for line in self.run_case(dict(RUN)).splitlines())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result, state = self.publish_case(root, "v11.4.3", outputs)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state["latest"] = "v11.4.4"
            (root / "release-state.json").write_text(json.dumps(state))
            result, state = self.publish_case(root, "v11.4.3", outputs)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(state["latest"], "v11.4.4")
            self.assertEqual(len(state["creates"]), 1)

    def test_publication_rejects_missing_or_invalid_latest_output(self) -> None:
        for outputs in ({}, {"verified_main_ci_reuse": ""},
                        {"verified_main_ci_reuse": "legacy"}, {"verified_main_ci_reuse": "TRUE"}):
            with self.subTest(outputs=outputs), tempfile.TemporaryDirectory() as temp:
                result, state = self.publish_case(Path(temp), "v11.4.3", outputs)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(state["creates"], [])
                self.assertEqual(state["latest"], "v11.3.15")

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

    def test_source_version_preflight_precedes_heavy_matrix_install(self) -> None:
        workflow = (SOURCE.parent / "ci.yml").read_text(encoding="utf-8")
        contract = workflow.split("\n  contract:\n", 1)[1].split("\n  regression:\n", 1)[0]
        regression = workflow.split("\n  regression:\n", 1)[1].split("\n  deterministic-eval-package:\n", 1)[0]
        for section, preflight, dependencies in (
            (contract, "Validate PR source version advance before dependency installation",
             "Install contract dependencies"),
            (regression, "Validate PR source version before expensive regression",
             "Install regression dependencies"),
        ):
            with self.subTest(preflight=preflight):
                self.assertIn("require-advance", section)
                self.assertIn("PYTHONPATH=src python -m agent_dev_kit.versioning", section)
                self.assertLess(section.index(preflight), section.index(dependencies))
        # Version errors never downgrade the supported Python matrix authority.
        quality = workflow.split("\n  deterministic-eval-package:\n", 1)[1]
        self.assertIn("if: ${{ always() }}", quality)
        self.assertIn("CONTRACT_MATRIX_RESULT", quality)
        self.assertIn("REGRESSION_MATRIX_RESULT", quality)

    def test_missing_or_corrupt_orphan_evidence_fails(self) -> None:
        for value in ({"workflow_runs": []}, {"workflow_runs": [{**RUN, "event": "pull_request"}]}, []):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit):
                    self.run_case(value, run_id="", triggering_run_id="5678", triggering_sha="b" * 40)
        with self.assertRaises(SystemExit):
            self.run_case({"workflow_runs": [RUN]}, run_id="", sha="b" * 40,
                          triggering_run_id="5678", triggering_sha="c" * 40)


if __name__ == "__main__":
    unittest.main()
