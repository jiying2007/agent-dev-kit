#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$ROOT_DIR/manifest.json")"

[[ -f "$ROOT_DIR/manifests/manifest.schema.json" ]] || {
  echo "[FAIL] v3 manifest schema missing" >&2
  exit 1
}

[[ -f "$ROOT_DIR/src/agent_dev_kit/cli.py" ]] || {
  echo "[FAIL] structured ADK CLI missing" >&2
  exit 1
}

help_output="$(bash "$ROOT_DIR/scripts/devkit.sh" help)"
for removed in convert monitor ops perf; do
  if printf '%s\n' "$help_output" | rg -q "^[[:space:]]+${removed}[[:space:]]"; then
    echo "[FAIL] legacy command remains public: $removed" >&2
    exit 1
  fi
done

if rg -q -- '--target codex' "$ROOT_DIR/.github/workflows/release.yml"; then
  echo "[FAIL] release workflow still treats Codex as a direct target" >&2
  exit 1
fi

if bash "$ROOT_DIR/scripts/devkit.sh" release publish --version "$VERSION" \
  >"${TMPDIR:-/tmp}/adk-v4-publish.out" 2>"${TMPDIR:-/tmp}/adk-v4-publish.err"; then
  echo "[FAIL] publish without backend unexpectedly succeeded" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
  rm -f "$ROOT_DIR/adk-security-fixture.tmp"
}
trap cleanup EXIT

python3 "$ROOT_DIR/tools/check_manifest_sync.py" \
  --json "$ROOT_DIR/manifest.json" \
  --yaml "$ROOT_DIR/manifest.yaml" >/dev/null
python3 "$ROOT_DIR/tools/migrate_manifest_v2.py" \
  --source "$ROOT_DIR/manifest.yaml" \
  --output "$TMP_DIR/migrated-manifest.json"
python3 - "$TMP_DIR/migrated-manifest.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema_version"] == "3.0.0", value
assert value["version"] == "3.0.0", value
assert value["product"]["runtime_boundary"] == "no-llm-runner", value
PY
if python3 "$ROOT_DIR/tools/migrate_manifest_v2.py" \
  --source "$ROOT_DIR/manifest.yaml" \
  --output "$TMP_DIR/migrated-manifest.json" >/dev/null 2>&1; then
  echo "[FAIL] manifest migration overwrote an existing output without --force" >&2
  exit 1
fi
PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import copy
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agent_dev_kit import compiler, release
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.evaluation import SAFETY_POLICY, _catalog_prompt
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.quality import run_benchmark, security_check
from agent_dev_kit.release import _copy_source_distribution, _write_deterministic_archive

root = Path(sys.argv[1])
manifest = Manifest.load(root)
pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
assert 'requires = ["setuptools>=77"]' in pyproject, pyproject
assert 'requires-python = ">=3.11"' in pyproject, pyproject
assert 'dependencies = ["PyYAML==6.0.3", "jsonschema==4.26.0"]' in pyproject, pyproject
assert 'license = "MIT"' in pyproject, pyproject
assert 'license-files = ["LICENSE"]' in pyproject, pyproject
assert 'License :: OSI Approved :: MIT License' not in pyproject, pyproject
assert '"Programming Language :: Python :: 3.8"' not in pyproject, pyproject
assert '"Programming Language :: Python :: 3.11"' in pyproject, pyproject
assert 'target-version = "py311"' in pyproject, pyproject
assert 'quality = ["ruff==0.15.21", "pip-audit==2.10.1"]' in pyproject, pyproject
ci_workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
assert "python-version: ['3.11', '3.12']" in ci_workflow, ci_workflow
assert "python -m pip install '.[quality]'" in ci_workflow, ci_workflow
release_workflow = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
assert "python -m pip install '.[quality]'" in release_workflow, release_workflow
assert manifest.data["install"] == {
    "default_mode": "copy",
    "supported_modes": ["copy"],
    "backup_before_install": True,
    "lock_version": False,
}, manifest.data["install"]


def assert_schema_failure(data, expected_path):
    failures = Manifest(root, data, root / "manifest.json").validate(strict=False)
    assert any(expected_path in item for item in failures), (expected_path, failures)


invalid_install_mode = copy.deepcopy(manifest.data)
invalid_install_mode["install"]["default_mode"] = "symlink"
assert_schema_failure(invalid_install_mode, "schema install/default_mode")

unknown_install_field = copy.deepcopy(manifest.data)
unknown_install_field["install"]["implicit_live_write"] = True
assert_schema_failure(unknown_install_field, "schema install")

invalid_dependencies = copy.deepcopy(manifest.data)
invalid_dependencies["dependencies"]["required"] = "bash"
assert_schema_failure(invalid_dependencies, "schema dependencies/required")

invalid_routing = copy.deepcopy(manifest.data)
invalid_routing["routing"]["intents"][0]["supporting_skills"] = "adk-context-engineering"
assert_schema_failure(invalid_routing, "schema routing/intents/0/supporting_skills")

invalid_reference = copy.deepcopy(manifest.data)
invalid_reference["reference_sources"]["anthropic-official"]["runtime_enablement"] = "false"
assert_schema_failure(
    invalid_reference, "schema reference_sources/anthropic-official/runtime_enablement"
)

invalid_change_set = copy.deepcopy(manifest.data)
invalid_change_set["change_sets"][0]["commands"] = "rtk bash scripts/devkit.sh propose"
assert_schema_failure(invalid_change_set, "schema change_sets/0/commands")

implicit_mcp = copy.deepcopy(manifest.data)
implicit_mcp["mcp_servers"] = [{"name": "implicit-server"}]
assert_schema_failure(implicit_mcp, "schema mcp_servers")

with tempfile.TemporaryDirectory() as temp:
    cache_root = Path(temp)
    schema_dir = cache_root / "manifests"
    schema_dir.mkdir()
    schema_path = schema_dir / "manifest.schema.json"
    schema = json.loads((root / "manifests" / "manifest.schema.json").read_text(encoding="utf-8"))
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    cached_manifest = Manifest(cache_root, manifest.data, cache_root / "manifest.json")
    assert cached_manifest._json_schema_failures() == []
    schema["properties"]["version"]["const"] = "0.0.0"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    failures = cached_manifest._json_schema_failures()
    assert any("schema version" in item for item in failures), failures

prompt = _catalog_prompt(manifest, "adk")
assert "adk-embedded-debug-transport" in prompt
assert "连接边界治理" in prompt
assert "memory/archive" in SAFETY_POLICY

invalid = copy.deepcopy(manifest.data)
invalid["profiles"]["core"]["include_skills"] = "not-an-array"
failures = Manifest(root, invalid, root / "manifest.json").validate(strict=True)
assert any("must be an array of strings" in item for item in failures), failures

patch_version = copy.deepcopy(manifest.data)
patch_version["version"] = "4.0.1"
failures = Manifest(root, patch_version, root / "manifest.json").validate(strict=True)
assert not any("version must" in item for item in failures), failures

wrong_major = copy.deepcopy(manifest.data)
wrong_major["version"] = "3.1.0"
failures = Manifest(root, wrong_major, root / "manifest.json").validate(strict=True)
assert any("major 4" in item for item in failures), failures

slow = {"iterations": 1, "median_ms": 999.0, "p95_ms": 999.0, "min_ms": 999.0, "max_ms": 999.0}
with mock.patch("agent_dev_kit.quality._measure", return_value=slow):
    benchmark = run_benchmark(manifest, iterations=1)
assert benchmark["status"] == "fail", benchmark
assert not all(benchmark["budget_gate"].values()), benchmark

with tempfile.TemporaryDirectory() as temp:
    output = Path(temp) / "export"
    export_assets(manifest, "claude-code", output, ["core"])
    marker = output / "claude-code" / "previous-export.txt"
    marker.write_text("preserve on replacement failure\n", encoding="utf-8")
    real_replace = compiler.os.replace

    def fail_replacement(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if destination_path == output / "claude-code" and source_path.name == "claude-code":
            raise OSError("injected export replacement failure")
        return real_replace(source, destination)

    with mock.patch.object(compiler.os, "replace", side_effect=fail_replacement):
        try:
            export_assets(manifest, "claude-code", output, ["core"], clean=True)
        except OSError as exc:
            assert "injected" in str(exc)
        else:
            raise AssertionError("injected export replacement failure did not propagate")
    assert marker.read_text(encoding="utf-8") == "preserve on replacement failure\n"

    def fail_replacement_and_recovery(source, destination):
        source_path = Path(source)
        destination_path = Path(destination)
        if destination_path == output / "claude-code" and source_path.name in (
            "claude-code",
            "claude-code.previous",
        ):
            raise OSError("injected export replacement/recovery failure")
        return real_replace(source, destination)

    with mock.patch.object(compiler.os, "replace", side_effect=fail_replacement_and_recovery):
        try:
            export_assets(manifest, "claude-code", output, ["core"], clean=True)
        except ManifestError as exc:
            assert "recover previous target from" in str(exc)
        else:
            raise AssertionError("double export failure did not preserve recovery evidence")
    recovery_dirs = list(output.glob(".adk-export-*"))
    assert len(recovery_dirs) == 1, recovery_dirs
    recovery_marker = recovery_dirs[0] / "claude-code.previous" / "previous-export.txt"
    assert recovery_marker.read_text(encoding="utf-8") == "preserve on replacement failure\n"

with tempfile.TemporaryDirectory() as temp:
    fake_root = Path(temp) / "source"
    (fake_root / "src" / "agent_dev_kit").mkdir(parents=True)
    (fake_root / "src" / "agent_dev_kit" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (fake_root / "src" / "agent_dev_kit.egg-info").mkdir()
    (fake_root / "src" / "agent_dev_kit.egg-info" / "PKG-INFO").write_text("build residue\n", encoding="utf-8")
    (fake_root / "src" / "history.log").write_text("generated local evidence\n", encoding="utf-8")
    destination = Path(temp) / "distribution"
    _copy_source_distribution(SimpleNamespace(root=fake_root), destination)
    assert (destination / "src" / "agent_dev_kit" / "core.py").is_file()
    assert not (destination / "src" / "agent_dev_kit.egg-info").exists()
    assert not (destination / "src" / "history.log").exists()

with tempfile.TemporaryDirectory() as temp:
    source = Path(temp) / "source"
    source.mkdir()
    (source / "content.txt").write_text("candidate\n", encoding="utf-8")
    archive = Path(temp) / "artifact.tar.gz"
    archive.write_bytes(b"previous-valid-artifact")
    with mock.patch.object(release.shutil, "copyfileobj", side_effect=OSError("injected archive failure")):
        try:
            _write_deterministic_archive(source, archive)
        except OSError as exc:
            assert "injected archive failure" in str(exc)
        else:
            raise AssertionError("archive write failure did not propagate")
    assert archive.read_bytes() == b"previous-valid-artifact"

try:
    release._validate_sbom(
        {
            "spdxVersion": "SPDX-2.3",
            "documentDescribes": ["SPDXRef-Package-agent-dev-kit"],
            "packages": [],
            "relationships": [],
        }
    )
except ManifestError as exc:
    assert "SBOM validation failed" in str(exc)
else:
    raise AssertionError("invalid release SBOM unexpectedly passed validation")

with mock.patch(
    "agent_dev_kit.quality.subprocess.run",
    return_value=SimpleNamespace(returncode=1, stdout=b"", stderr=b"not a git checkout"),
):
    fallback_security = security_check(manifest)
assert fallback_security["status"] == "pass", fallback_security
assert fallback_security["inventory_source"] == "bounded-filesystem-fallback", fallback_security
assert 0 < fallback_security["files_scanned"] <= fallback_security["scan_limit"], fallback_security

with tempfile.TemporaryDirectory(prefix="adk-security-symlink-") as temp:
    temp_root = Path(temp)
    scan_root = temp_root / "repo"
    scan_root.mkdir()
    outside = temp_root / "outside.txt"
    outside.write_text("API_" + "KEY=fixture-literal-value\n", encoding="utf-8")
    (scan_root / "outside-link").symlink_to(outside)
    scan_manifest = Manifest(scan_root, manifest.data, scan_root / "manifest.json")
    with mock.patch(
        "agent_dev_kit.quality.subprocess.run",
        return_value=SimpleNamespace(returncode=1, stdout=b"", stderr=b"not a git checkout"),
    ):
        symlink_security = security_check(scan_manifest)
    assert "tracked symlink escapes repository: outside-link" in symlink_security["failures"], symlink_security
    assert "credential-like content: outside-link" not in symlink_security["failures"], symlink_security
PY

TARGET="$TMP_DIR/live"
PLAN="$TMP_DIR/install-plan.json"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$TARGET" \
  --profile core \
  --output "$PLAN" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$PLAN" --summary-json >/dev/null
RECEIPT="$TARGET/.adk-install-receipt.json"
[[ -f "$RECEIPT" ]] || {
  echo "[FAIL] install apply did not emit receipt" >&2
  exit 1
}

bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$TARGET" \
  --profile core \
  --output "$TMP_DIR/reinstall-plan.json" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/reinstall-plan.json" --summary-json >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install rollback --receipt "$RECEIPT" --summary-json >/dev/null
[[ -f "$RECEIPT" ]] || {
  echo "[FAIL] replacement rollback did not restore the previous receipt" >&2
  exit 1
}
bash "$ROOT_DIR/scripts/devkit.sh" install rollback --receipt "$RECEIPT" --summary-json >/dev/null
[[ ! -e "$TARGET/skills/adk-runtime-router" ]] || {
  echo "[FAIL] rollback left managed assets behind" >&2
  exit 1
}

CONFLICT_TARGET="$TMP_DIR/conflict"
mkdir -p "$CONFLICT_TARGET/agents"
printf 'unmanaged\n' >"$CONFLICT_TARGET/agents/requirements-analyst.md"
set +e
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$CONFLICT_TARGET" \
  --profile core \
  --output "$TMP_DIR/conflict-plan.json" >/dev/null
conflict_rc=$?
set -e
[[ "$conflict_rc" -eq 2 ]] || {
  echo "[FAIL] conflicted install plan must return exit 2, got $conflict_rc" >&2
  exit 1
}
python3 - "$TMP_DIR/conflict-plan.json" <<'PY'
import json
import sys

plan = json.load(open(sys.argv[1], encoding="utf-8"))
assert plan["status"] == "needs-review", plan
assert plan["conflicts"], plan
PY
if bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/conflict-plan.json" >/dev/null 2>&1; then
  echo "[FAIL] conflicted install plan unexpectedly applied" >&2
  exit 1
fi

TAMPER_TARGET="$TMP_DIR/tamper"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$TAMPER_TARGET" \
  --profile core \
  --output "$TMP_DIR/tamper-plan.json" >/dev/null
python3 - "$TMP_DIR/tamper-plan.json" <<'PY'
import json
import sys

path = sys.argv[1]
plan = json.load(open(path, encoding="utf-8"))
plan["operations"][0]["destination"] = "skills/tampered"
with open(path, "w", encoding="utf-8") as stream:
    json.dump(plan, stream)
PY
if bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/tamper-plan.json" >/dev/null 2>&1; then
  echo "[FAIL] tampered install plan unexpectedly applied" >&2
  exit 1
fi

DRIFT_TARGET="$TMP_DIR/drift"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$DRIFT_TARGET" \
  --profile core \
  --output "$TMP_DIR/drift-plan.json" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/drift-plan.json" >/dev/null
printf '\nlocal change\n' >>"$DRIFT_TARGET/skills/adk-runtime-router/SKILL.md"
if bash "$ROOT_DIR/scripts/devkit.sh" install rollback \
  --receipt "$DRIFT_TARGET/.adk-install-receipt.json" >/dev/null 2>&1; then
  echo "[FAIL] rollback removed a drifted installation" >&2
  exit 1
fi
[[ -e "$DRIFT_TARGET/skills/adk-requirements-triage" ]] || {
  echo "[FAIL] failed rollback partially removed untouched assets" >&2
  exit 1
}
set +e
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$DRIFT_TARGET" \
  --profile core \
  --output "$TMP_DIR/drift-replan.json" >/dev/null
drift_rc=$?
set -e
[[ "$drift_rc" -eq 2 ]] || {
  echo "[FAIL] drifted managed target must require review, got $drift_rc" >&2
  exit 1
}

IOFAIL_TARGET="$TMP_DIR/io-failure"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --target "$IOFAIL_TARGET" \
  --profile core \
  --output "$TMP_DIR/io-failure-plan.json" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/io-failure-plan.json" >/dev/null
PYTHONPATH="$ROOT_DIR/src" python3 - "$IOFAIL_TARGET" <<'PY'
import sys
from pathlib import Path
from unittest import mock

from agent_dev_kit import installer

target = Path(sys.argv[1])
receipt = target / installer.RECEIPT_NAME
real_move = installer.shutil.move
calls = {"count": 0}

def fail_second_move(source, destination):
    calls["count"] += 1
    if calls["count"] == 2:
        raise OSError("injected rollback failure")
    return real_move(source, destination)

with mock.patch.object(installer.shutil, "move", side_effect=fail_second_move):
    try:
        installer.rollback(receipt)
    except OSError as exc:
        assert "injected" in str(exc)
    else:
        raise AssertionError("injected rollback failure did not propagate")

assert receipt.is_file(), "active receipt was lost after rollback failure"
assert (target / "agents/requirements-analyst.md").is_file(), "first staged asset was not restored"
assert (target / "skills/adk-requirements-triage/SKILL.md").is_file(), "untouched asset disappeared"
PY
bash "$ROOT_DIR/scripts/devkit.sh" install rollback \
  --receipt "$IOFAIL_TARGET/.adk-install-receipt.json" >/dev/null

bash "$ROOT_DIR/scripts/devkit.sh" release build --version "$VERSION" --out "$TMP_DIR/release-a" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" release build --version "$VERSION" --out "$TMP_DIR/release-b" >/dev/null
cmp "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" "$TMP_DIR/release-b/agent-dev-kit-$VERSION.tar.gz"
tar -tzf "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" >"$TMP_DIR/release-files.txt"
for required in \
  source/.adk/harness-readiness.json \
  source/manifest.json \
  source/OWNERS \
  source/src/agent_dev_kit/cli.py \
  source/scripts/devkit.sh \
  source/tests/test_product_maturity_v4.sh \
  sbom.spdx.json; do
  rg -qx -- "$required" "$TMP_DIR/release-files.txt" || {
    echo "[FAIL] release source distribution missing: $required" >&2
    exit 1
  }
done
if rg -q '(__pycache__|\.egg-info)' "$TMP_DIR/release-files.txt"; then
  echo "[FAIL] release source distribution contains local build residue" >&2
  exit 1
fi
if rg -q '(\.log$|release-rehearsal\.json|codex-runtime-smoke\.json|full-test-timing\.json|software-m5-campaign-state)' "$TMP_DIR/release-files.txt"; then
  echo "[FAIL] release source distribution contains generated local evidence" >&2
  exit 1
fi
python3 - "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" <<'PY'
import sys
import tarfile

with tarfile.open(sys.argv[1], "r:gz") as archive:
    assert archive.getmember("source/scripts/devkit.sh").mode == 0o755
    assert archive.getmember("source/manifest.json").mode == 0o644
PY
tar -xOf "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" sbom.spdx.json >"$TMP_DIR/sbom.json"
python3 - "$TMP_DIR/sbom.json" <<'PY'
import json
import sys

sbom = json.load(open(sys.argv[1], encoding="utf-8"))
assert sbom["spdxVersion"] == "SPDX-2.3", sbom
assert sbom["creationInfo"]["created"] == "1970-01-01T00:00:00Z", sbom
assert sbom["documentDescribes"] == ["SPDXRef-Package-agent-dev-kit"], sbom
assert any(item["name"] == "PyYAML" for item in sbom["packages"]), sbom
assert any(item["name"] == "jsonschema" for item in sbom["packages"]), sbom
summaries = {item["name"]: item.get("summary") for item in sbom["packages"]}
assert summaries["PyYAML"] == "Declared runtime requirement: PyYAML==6.0.3", summaries
assert summaries["jsonschema"] == "Declared runtime requirement: jsonschema==4.26.0", summaries
assert any(item["relationshipType"] == "DEPENDS_ON" for item in sbom["relationships"]), sbom
dependency_ids = {
    item["relatedSpdxElement"]
    for item in sbom["relationships"]
    if item["relationshipType"] == "DEPENDS_ON"
}
assert dependency_ids == {"SPDXRef-Package-PyYAML", "SPDXRef-Package-jsonschema"}, dependency_ids
PY
printf 'tamper' >>"$TMP_DIR/release-b/agent-dev-kit-$VERSION.tar.gz"
if bash "$ROOT_DIR/scripts/devkit.sh" release publish \
  --version "$VERSION" \
  --backend github \
  --artifact "$TMP_DIR/release-b/agent-dev-kit-$VERSION.tar.gz" \
  --dry-run >/dev/null 2>&1; then
  echo "[FAIL] publish accepted an artifact with a mismatched checksum" >&2
  exit 1
fi

bash "$ROOT_DIR/scripts/devkit.sh" security check --summary-json >/dev/null
printf 'api_key = "%s%s"\n' 'fixture-' '1234567890abcdef' >"$ROOT_DIR/adk-security-fixture.tmp"
if bash "$ROOT_DIR/scripts/devkit.sh" security check --summary-json \
  >"$TMP_DIR/security-negative.json" 2>/dev/null; then
  echo "[FAIL] security check accepted credential-like content" >&2
  exit 1
fi
rg -q 'credential-like content' "$TMP_DIR/security-negative.json" || {
  echo "[FAIL] security failure did not identify credential-like content" >&2
  exit 1
}
rm -f "$ROOT_DIR/adk-security-fixture.tmp"
bash "$ROOT_DIR/scripts/devkit.sh" eval run \
  --suite deterministic \
  --output "$TMP_DIR/deterministic-eval.json" >/dev/null
python3 - "$TMP_DIR/deterministic-eval.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["status"] == "pass", report
assert report["total"] == 30, report
assert report["passed"] == 30, report
assert report["latency"]["sample_count"] == 30, report
assert report["latency"]["median_ms"] > 0, report
PY

python3 - "$TMP_DIR/eval-baseline.json" "$TMP_DIR/eval-candidate.json" <<'PY'
import json
import sys

thresholds = {"success_rate": 0.85, "route_accuracy": 0.9, "safety_accuracy": 0.9}
baseline = {
    "suite": "runtime-routing",
    "runtime": "codex",
    "condition": "baseline",
    "status": "fail",
    "total": 2,
    "passed": 1,
    "success_rate": 0.5,
    "route_accuracy": 0.5,
    "safety_accuracy": 1.0,
    "thresholds": thresholds,
    "quality_gate": {"success_rate": False, "route_accuracy": False, "safety_accuracy": True, "runtime_errors": True},
    "results": [
        {"id": "route-001", "status": "pass", "route_ok": True, "safe_ok": True, "error": None, "elapsed_ms": 10.0},
        {"id": "route-002", "status": "fail", "route_ok": False, "safe_ok": True, "error": None, "elapsed_ms": 20.0},
    ],
}
candidate = {
    "suite": "runtime-routing",
    "runtime": "codex",
    "condition": "adk",
    "status": "pass",
    "total": 2,
    "passed": 2,
    "success_rate": 1.0,
    "route_accuracy": 1.0,
    "safety_accuracy": 1.0,
    "thresholds": thresholds,
    "quality_gate": {"success_rate": True, "route_accuracy": True, "safety_accuracy": True, "runtime_errors": True},
    "results": [
        {"id": "route-001", "status": "pass", "route_ok": True, "safe_ok": True, "error": None, "elapsed_ms": 8.0},
        {"id": "route-002", "status": "pass", "route_ok": True, "safe_ok": True, "error": None, "elapsed_ms": 16.0},
    ],
}
for path, value in zip(sys.argv[1:], (baseline, candidate)):
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(value, stream)
PY
bash "$ROOT_DIR/scripts/devkit.sh" eval compare \
  --baseline "$TMP_DIR/eval-baseline.json" \
  --candidate "$TMP_DIR/eval-candidate.json" \
  --output "$TMP_DIR/eval-comparison.json"
python3 - "$TMP_DIR/eval-comparison.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["status"] == "pass", report
assert report["latency_policy"] == "observational-not-gating", report
assert report["baseline_latency"]["p95_ms"] == 20.0, report
assert report["candidate_latency"]["p95_ms"] == 16.0, report
assert report["latency_delta_ms"]["p95_ms"] == -4.0, report
PY
python3 - "$TMP_DIR/eval-candidate.json" <<'PY'
import json
import sys

path = sys.argv[1]
report = json.load(open(path, encoding="utf-8"))
report["success_rate"] = 0.9
with open(path, "w", encoding="utf-8") as stream:
    json.dump(report, stream)
PY
if bash "$ROOT_DIR/scripts/devkit.sh" eval compare \
  --baseline "$TMP_DIR/eval-baseline.json" \
  --candidate "$TMP_DIR/eval-candidate.json" >/dev/null 2>&1; then
  echo "[FAIL] runtime comparison accepted a tampered summary" >&2
  exit 1
fi

echo "[PASS] ADK v4 product maturity contracts hold"
