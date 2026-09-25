"""Isolated source-layout discovery/load probe for direct targets.

Passing this probe proves exported files are discoverable/loadable from the ADK
target layout. It never launches the target runtime and therefore cannot produce
native or certified runtime evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from .compiler import export_assets
from .model import Manifest, ManifestError, canonical_json_bytes, ensure_within, sha256_bytes

SCHEMA = "adk-target-source-probe/v1"


def probe_target_source(manifest: Manifest, target: str, profile: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="adk-source-probe-") as temp:
        root = Path(temp).resolve()
        result = export_assets(manifest, target, root, [profile])
        target_root = ensure_within(root / target, root, "source probe target")
        inventory_path = target_root / "adk-export-manifest.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        if inventory.get("schema") != "adk-export-manifest/v2":
            raise ManifestError("source_probe_invalid_inventory_schema")
        observed = []
        for item in inventory["files"]:
            path = ensure_within(target_root / item["path"], target_root, "source probe file")
            if path.is_symlink() or not path.is_file():
                raise ManifestError(f"source_probe_missing_regular_file: {item['path']}")
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest != item["sha256"]:
                raise ManifestError(f"source_probe_digest_mismatch: {item['path']}")
            if path.name in ("SKILL.md", "AGENTS.md"):
                data.decode("utf-8")
            observed.append(
                {
                    "kind": item["kind"],
                    "name": item["name"],
                    "path": item["path"],
                    "bytes": len(data),
                    "sha256": digest,
                }
            )
        if len(observed) != len(result["files"]):
            raise ManifestError("source_probe_inventory_count_mismatch")
    return {
        "schema": SCHEMA,
        "status": "pass",
        "target": target,
        "profile": profile,
        "source_version": manifest.version,
        "source_discovery": "pass",
        "source_load": "pass",
        "files": len(observed),
        "bytes": sum(item["bytes"] for item in observed),
        "by_kind": {
            kind: {
                "files": sum(item["kind"] == kind for item in observed),
                "bytes": sum(item["bytes"] for item in observed if item["kind"] == kind),
            }
            for kind in sorted({item["kind"] for item in observed})
        },
        "observed_index_sha256": sha256_bytes(canonical_json_bytes(observed)),
        "evidence_level": "source-layout",
        "native_runtime_evidence": False,
        "certification": "not-certified",
        "lifecycle_authority": "none-evidence-only",
        "release_authorized": False,
        "limitations": [
            "probe uses an isolated temporary export, not a user live directory",
            "probe does not launch or inspect a native target runtime",
            "native discovery/load/trigger certification still requires runtime evidence",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe direct-target source discovery/load in isolation")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = Manifest.load(Path(args.root).resolve())
        result = probe_target_source(manifest, args.target, args.profile or manifest.default_profile)
    except (OSError, ValueError, ManifestError, json.JSONDecodeError) as exc:
        result = {"schema": SCHEMA, "status": "fail", "error": str(exc)}
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
