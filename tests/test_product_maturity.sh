#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ ! -e "$ROOT_DIR/tests/test_product_maturity_v5.sh" ]] || { echo "[FAIL] retired product maturity v5 test name returned" >&2; exit 1; }
VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])' "$ROOT_DIR/manifest.json")"
TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
  rm -f "$ROOT_DIR/adk-security-fixture.tmp"
}
trap cleanup EXIT

[[ -f "$ROOT_DIR/manifest.json" ]] || { echo "[FAIL] canonical manifest.json missing" >&2; exit 1; }
[[ ! -e "$ROOT_DIR/manifest.yaml" ]] || { echo "[FAIL] retired manifest.yaml projection exists" >&2; exit 1; }
[[ -f "$ROOT_DIR/manifests/manifest.schema.json" ]] || { echo "[FAIL] manifest schema missing" >&2; exit 1; }
[[ -f "$ROOT_DIR/src/agent_dev_kit/cli.py" ]] || { echo "[FAIL] structured ADK CLI missing" >&2; exit 1; }

bash "$ROOT_DIR/scripts/devkit.sh" validate --strict --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass", d'

help_output="$(bash "$ROOT_DIR/scripts/devkit.sh" help)"
for removed in convert monitor ops perf; do
  if printf '%s\n' "$help_output" | rg -q "^[[:space:]]+${removed}[[:space:]]"; then
    echo "[FAIL] retired public command remains: $removed" >&2
    exit 1
  fi
done
if bash "$ROOT_DIR/scripts/devkit.sh" release publish --version "$VERSION" \
  >"$TMP_DIR/publish.out" 2>"$TMP_DIR/publish.err"; then
  echo "[FAIL] publish without an explicit backend unexpectedly succeeded" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import copy
import json
import sys
import tempfile
import tomllib
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from agent_dev_kit import compiler, release
from agent_dev_kit.distribution import release_artifacts
from agent_dev_kit.distribution.release_artifacts import SOURCE_DISTRIBUTION_DIRECTORIES, SOURCE_DISTRIBUTION_FILES
from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.quality import run_benchmark, security_check
from agent_dev_kit.distribution.release_artifacts import _copy_source_distribution, _write_deterministic_archive

root = Path(sys.argv[1])
manifest = Manifest.load(root)
assert manifest.validate(strict=True) == [], manifest.validate(strict=True)
assert manifest.source.name == "manifest.json"
assert not (root / "manifest.yaml").exists()

pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
pyproject_data = tomllib.loads(pyproject)
assert pyproject_data["project"]["requires-python"] == ">=3.11", pyproject_data

def exact_pin_names(items):
    assert all(isinstance(item, str) and item.count("==") == 1 for item in items), items
    pairs = [item.split("==", 1) for item in items]
    assert all(name and version for name, version in pairs), items
    return [name for name, _version in pairs]

assert exact_pin_names(pyproject_data["project"]["dependencies"]) == [
    "PyYAML",
    "jsonschema",
], pyproject_data
assert exact_pin_names(pyproject_data["project"]["optional-dependencies"]["quality"]) == [
    "ruff",
    "pip-audit",
    "mypy",
    "types-jsonschema",
    "types-PyYAML",
], pyproject_data
assert pyproject_data["tool"]["mypy"] == {
    "python_version": "3.11",
    "strict": True,
    "warn_unreachable": True,
    "show_error_codes": True,
}, pyproject_data
ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
assert "python-version: ['3.11', '3.12']" in ci, ci
assert "Run focused strict type analysis" in ci, ci

assert manifest.data["install"] == {
    "default_mode": "copy",
    "supported_modes": ["copy"],
    "backup_before_install": True,
    "lock_version": False,
}, manifest.data["install"]


def assert_schema_failure(data, expected):
    failures = Manifest(root, data, root / "manifest.json").validate(strict=False)
    assert any(expected in item for item in failures), (expected, failures)

invalid = copy.deepcopy(manifest.data)
invalid["install"]["default_mode"] = "symlink"
assert_schema_failure(invalid, "schema install/default_mode")

invalid = copy.deepcopy(manifest.data)
invalid["routing"]["ir_version"] = "routing-ir/v1"
assert_schema_failure(invalid, "schema routing/ir_version")

invalid = copy.deepcopy(manifest.data)
invalid["routing"]["task_modes"][0]["mutation_permission"] = "workspace-write"
assert_schema_failure(invalid, "schema routing/task_modes/0")

invalid = copy.deepcopy(manifest.data)
invalid["reference_sources"]["anthropic-official"]["runtime_enablement"] = "false"
assert_schema_failure(invalid, "schema reference_sources/anthropic-official/runtime_enablement")

slow = {"iterations": 1, "median_ms": 999.0, "p95_ms": 999.0, "min_ms": 999.0, "max_ms": 999.0}
with mock.patch("agent_dev_kit.quality._measure", return_value=slow):
    benchmark = run_benchmark(manifest, iterations=1)
assert benchmark["status"] == "fail", benchmark

with tempfile.TemporaryDirectory() as temp:
    output = Path(temp) / "export"
    export_assets(manifest, "claude-code", output, ["core"])
    marker = output / "claude-code" / "previous-export.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    real_replace = compiler.os.replace

    def fail_replace(source, destination):
        if Path(destination) == output / "claude-code" and Path(source).name == "claude-code":
            raise OSError("injected export replacement failure")
        return real_replace(source, destination)

    with mock.patch.object(compiler.os, "replace", side_effect=fail_replace):
        try:
            export_assets(manifest, "claude-code", output, ["core"], clean=True)
        except OSError:
            pass
        else:
            raise AssertionError("injected export failure did not propagate")
    assert marker.read_text(encoding="utf-8") == "preserve\n"

with tempfile.TemporaryDirectory() as temp:
    fake_root = Path(temp) / "source"
    for relative in SOURCE_DISTRIBUTION_DIRECTORIES:
        (fake_root / relative).mkdir(parents=True, exist_ok=True)
    for relative in SOURCE_DISTRIBUTION_FILES:
        source_file = fake_root / relative
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("fixture\n", encoding="utf-8")
    (fake_root / "src" / "agent_dev_kit").mkdir(parents=True, exist_ok=True)
    (fake_root / "src" / "agent_dev_kit" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (fake_root / "src" / "agent_dev_kit.egg-info").mkdir()
    (fake_root / "src" / "agent_dev_kit.egg-info" / "PKG-INFO").write_text("residue\n", encoding="utf-8")
    destination = Path(temp) / "distribution"
    _copy_source_distribution(SimpleNamespace(root=fake_root), destination)
    assert (destination / "src" / "agent_dev_kit" / "core.py").is_file()
    assert not (destination / "src" / "agent_dev_kit.egg-info").exists()

with tempfile.TemporaryDirectory() as temp:
    source = Path(temp) / "source"
    source.mkdir()
    (source / "content.txt").write_text("candidate\n", encoding="utf-8")
    archive = Path(temp) / "artifact.tar.gz"
    archive.write_bytes(b"previous-valid-artifact")
    with mock.patch.object(release_artifacts.shutil, "copyfileobj", side_effect=OSError("injected archive failure")):
        try:
            _write_deterministic_archive(source, archive)
        except OSError:
            pass
        else:
            raise AssertionError("archive failure did not propagate")
    assert archive.read_bytes() == b"previous-valid-artifact"

try:
    release_artifacts._validate_sbom({
        "spdxVersion": "SPDX-2.3",
        "documentDescribes": ["SPDXRef-Package-agent-dev-kit"],
        "packages": [],
        "relationships": [],
    })
except ManifestError:
    pass
else:
    raise AssertionError("invalid SBOM unexpectedly passed")

with mock.patch(
    "agent_dev_kit.quality.subprocess.run",
    return_value=SimpleNamespace(returncode=1, stdout=b"", stderr=b"not a git checkout"),
):
    fallback = security_check(manifest)
assert fallback["status"] == "pass", fallback
assert fallback["inventory_source"] == "bounded-filesystem-fallback", fallback
PY

TARGET="$TMP_DIR/live"
PLAN="$TMP_DIR/install-plan.json"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code --target "$TARGET" --profile core --output "$PLAN" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$PLAN" --summary-json >/dev/null
RECEIPT="$TARGET/.adk-install-receipt.json"
[[ -f "$RECEIPT" ]] || { echo "[FAIL] install receipt missing" >&2; exit 1; }
bash "$ROOT_DIR/scripts/devkit.sh" install rollback --receipt "$RECEIPT" --summary-json >/dev/null
[[ ! -e "$TARGET/skills/adk-runtime-router" ]] || { echo "[FAIL] rollback left managed asset" >&2; exit 1; }

release_source_args=()
if [[ ! -e "$ROOT_DIR/.git" ]] || [[ -n "$(git -C "$ROOT_DIR" status --porcelain=v1 --untracked-files=all -- .github agents contexts docs manifests optional-skills scripts schemas skills src templates tests tools workflows .version-lock .adk/harness-readiness.json AGENTS.md CONTEXT.md LICENSE NAVIGATION.md OWNERS README.md manifest.json pyproject.toml)" ]]; then
  release_source_args+=(--allow-unbound-snapshot)
fi
bash "$ROOT_DIR/scripts/devkit.sh" release build --version "$VERSION" --out "$TMP_DIR/release-a" "${release_source_args[@]}" >/dev/null
bash "$ROOT_DIR/scripts/devkit.sh" release build --version "$VERSION" --out "$TMP_DIR/release-b" "${release_source_args[@]}" >/dev/null
cmp "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" "$TMP_DIR/release-b/agent-dev-kit-$VERSION.tar.gz"
tar -tzf "$TMP_DIR/release-a/agent-dev-kit-$VERSION.tar.gz" >"$TMP_DIR/release-files.txt"
for required in source/manifest.json source/OWNERS source/src/agent_dev_kit/cli.py source/scripts/devkit.sh sbom.spdx.json; do
  rg -qx -- "$required" "$TMP_DIR/release-files.txt" || {
    echo "[FAIL] release source distribution missing: $required" >&2
    exit 1
  }
done
if rg -q 'source/manifest\.yaml$' "$TMP_DIR/release-files.txt"; then
  echo "[FAIL] release contains retired Manifest YAML projection" >&2
  exit 1
fi
if rg -q '(__pycache__|\.egg-info)' "$TMP_DIR/release-files.txt"; then
  echo "[FAIL] release contains local build residue" >&2
  exit 1
fi

bash "$ROOT_DIR/scripts/devkit.sh" eval run --suite deterministic --output "$TMP_DIR/eval.json" >/dev/null
python3 - "$TMP_DIR/eval.json" <<'PY'
import json
import sys
report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["status"] == "pass", report
assert report["total"] == 30 and report["passed"] == 30, report
PY

echo "[PASS] ADK product maturity contracts hold"
