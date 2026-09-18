#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from __future__ import annotations

import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path

from agent_dev_kit.distribution import validate_release_artifact, validate_release_manifest
from agent_dev_kit.distribution.release_artifacts import SOURCE_DISTRIBUTION_DIRECTORIES, SOURCE_DISTRIBUTION_FILES
from agent_dev_kit.model import canonical_json_bytes

root = Path.cwd()
assert (root / "manifest.json").is_file(), "canonical manifest.json is missing"
assert not (root / "manifest.yaml").exists(), "retired manifest.yaml surface returned"
assert not (root / "scripts/release-manager.sh").exists(), "legacy shell release manager returned"
assert (root / "src/agent_dev_kit/release.py").is_file(), "canonical Python release control plane is missing"
release_source = (root / "src/agent_dev_kit/release.py").read_text(encoding="utf-8")
release_artifacts_source = (root / "src/agent_dev_kit/distribution/release_artifacts.py").read_text(encoding="utf-8")
for retired in (
    "_install_legacy_release_bundle",
    "_previous_release_migration",
    "legacy-bundle-v2",
    "target-contract-hard-cut",
    "enforce_current_contract",
):
    assert retired not in release_source, f"retired release compatibility path returned: {retired}"
assert "schema_version\") not in {1, 2}" not in release_artifacts_source
assert "schema_version\") != 2" in release_artifacts_source
for relative in SOURCE_DISTRIBUTION_DIRECTORIES:
    assert (root / relative).is_dir(), f"declared release source directory is missing: {relative}"
for relative in SOURCE_DISTRIBUTION_FILES:
    assert (root / relative).is_file(), f"declared release source file is missing: {relative}"
assert "contexts" not in SOURCE_DISTRIBUTION_DIRECTORIES
assert "NAVIGATION.md" not in SOURCE_DISTRIBUTION_FILES
workflow = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
assert "scripts/devkit.sh release check" in workflow, "release workflow bypasses canonical release check"
assert "scripts/devkit.sh release build --out dist" in workflow, "release workflow bypasses canonical release build"
assert "release-manager.sh" not in workflow, "release workflow references retired shell release manager"
assert "manifest.yaml" not in workflow, "release workflow references retired YAML manifest"

version = "6.0.0"
source_manifest_value = {"version": version}
source_manifest = json.dumps(source_manifest_value, indent=2).encode() + b"\n"
sbom = b'{"spdxVersion":"SPDX-2.3"}\n'
sha = lambda value: hashlib.sha256(value).hexdigest()
release_manifest = {
    "schema_version": 2,
    "version": version,
    "manifest_sha256": sha(canonical_json_bytes(source_manifest_value)),
    "direct_targets": [{"target": "claude-code", "agents": 1, "skills": 1}],
    "external_targets": ["external-runtime"],
    "source_distribution": True,
    "source_file_count": 2,
    "reproducible": False,
    "release_eligible": False,
    "source_provenance": {
        "kind": "unbound-snapshot",
        "release_eligible": False,
        "commit": None,
        "tree": None,
        "dirty": None,
        "source_distribution_sha256": "0" * 64,
    },
    "sbom": {"path": "sbom.spdx.json", "sha256": sha(sbom), "validated": True},
}
assert validate_release_manifest(release_manifest)["status"] == "pass"

mismatch = json.loads(json.dumps(release_manifest))
mismatch["release_eligible"] = True
validation = validate_release_manifest(mismatch)
assert validation["status"] == "fail"
assert any("release_eligible must match" in item for item in validation["failures"])

with tempfile.TemporaryDirectory() as temp:
    artifact = Path(temp) / f"agent-dev-kit-{version}.tar.gz"
    with tarfile.open(artifact, "w:gz") as archive:
        for name, payload in (
            ("manifest.json", source_manifest),
            ("sbom.spdx.json", sbom),
            ("release-manifest.json", json.dumps(release_manifest).encode()),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    result = validate_release_artifact(artifact)
    assert result["status"] == "pass"
    assert result["manifest_sha256"] == release_manifest["manifest_sha256"]
    assert result["sbom_sha256"] == release_manifest["sbom"]["sha256"]

print("[PASS] canonical Python release control plane and release manifest identities are fail-closed")
PY
