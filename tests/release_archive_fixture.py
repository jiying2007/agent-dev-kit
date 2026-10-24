"""Small real source/export fixture shared by release archive boundary tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
from functools import lru_cache
from pathlib import Path

from agent_dev_kit.compiler import export_assets
from agent_dev_kit.model import Manifest, sha256_tree

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _rendered_fixture():
    data = json.loads((ROOT / "manifest.json").read_bytes())
    data["version"] = "7.0.0"
    data["agents"] = [item for item in data["agents"] if item["name"] == "requirements-analyst"]
    data["skills"] = [item for item in data["skills"] if item["name"] == "adk-requirements-triage"]
    data["optional_skills"] = []
    data["tool_targets"] = {"claude-code": data["tool_targets"]["claude-code"]}
    data["default_profile"] = "embedded-fullstack"
    data["profiles"] = {
        "embedded-fullstack": {
            "description": "Minimal real release fixture",
            "trigger_examples": [],
            "include_agents": ["requirements-analyst"],
            "include_skills": ["adk-requirements-triage"],
        }
    }
    data["workflows"] = data["workflows"][:1]
    source_manifest = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    sbom = b'{"spdxVersion":"SPDX-2.3"}\n'
    with tempfile.TemporaryDirectory(prefix="adk-release-fixture-") as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        paths = ["manifests/manifest.schema.json", "manifests/target-contract.schema.json",
                 data["tool_targets"]["claude-code"]["contract"]]
        paths.extend(item["path"] for key in ("agents", "skills", "workflows") for item in data[key])
        for name in paths:
            destination = source / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / name).read_bytes())
            destination.chmod(0o644)
        (source / "manifest.json").write_bytes(source_manifest)
        (source / "README.md").write_bytes(b"source inventory fixture\n")
        manifest = Manifest.load(source)
        failures = manifest.validate(strict=True)
        if failures:
            raise AssertionError("invalid release fixture: " + "; ".join(failures))
        output = Path(temporary) / "bundles"
        result = export_assets(manifest, "claude-code", output, ["embedded-fullstack"])
        source_files = sorted(path for path in source.rglob("*") if path.is_file())
        release_manifest = {
            "schema_version": 2, "version": manifest.version,
            "manifest_sha256": manifest.digest,
            "direct_targets": [{"target": "claude-code", "agents": result["agents"],
                                "skills": result["skills"]}],
            "external_targets": sorted(manifest.external_targets()), "source_distribution": True,
            "source_file_count": len(source_files), "reproducible": False, "release_eligible": False,
            "source_provenance": {"kind": "unbound-snapshot", "release_eligible": False,
                                  "commit": None, "tree": None, "dirty": None,
                                  "source_distribution_sha256": sha256_tree(source)},
            "sbom": {"path": "sbom.spdx.json", "sha256": hashlib.sha256(sbom).hexdigest(),
                     "validated": True},
        }
        members = [("manifest.json", source_manifest)]
        members.extend(("source/" + path.relative_to(source).as_posix(), path.read_bytes())
                       for path in source_files)
        members.extend(("bundles/" + path.relative_to(output).as_posix(), path.read_bytes())
                       for path in sorted(output.rglob("*")) if path.is_file())
        members.append(("sbom.spdx.json", sbom))
    return release_manifest, members


def release_fixture():
    """Return independent metadata and member bytes; every fixture file is 0644."""
    manifest, members = _rendered_fixture()
    return copy.deepcopy(manifest), list(members)
