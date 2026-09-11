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
from agent_dev_kit.model import canonical_json_bytes

version = "5.0.0-rc.2"
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

print("[PASS] release manifest v2 and archive identities are fail-closed")
PY
