"""Deterministic profile-level context footprint accounting.

This module measures source bytes only. Token counts are a documented bytes/4
heuristic and must not be interpreted as provider tokenizer measurements.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .model import Asset, Manifest, ManifestError, ensure_within

SCHEMA = "adk-profile-context-footprint/v1"
SUPPORT_DIRS = ("references", "scripts", "assets")


def _main_file(asset: Asset) -> Path:
    return asset.path / ("AGENTS.md" if asset.kind == "agent" else "SKILL.md")


def _regular_file_bytes(path: Path, root: Path) -> int:
    if path.is_symlink() or not path.is_file():
        raise ManifestError(f"context_footprint_invalid_file: {path}")
    ensure_within(path, root, "context footprint source")
    return path.stat().st_size


def _support_bytes(asset: Asset) -> tuple[int, int]:
    total = 0
    files = 0
    for name in SUPPORT_DIRS:
        base = asset.path / name
        if not base.exists():
            continue
        if base.is_symlink() or not base.is_dir():
            raise ManifestError(f"context_footprint_invalid_support_dir: {base}")
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                raise ManifestError(f"context_footprint_symlink_forbidden: {path}")
            if not path.is_file():
                continue
            total += _regular_file_bytes(path, asset.path)
            files += 1
    return total, files


def _asset_record(asset: Asset) -> dict[str, Any]:
    main = _main_file(asset)
    entry_bytes = _regular_file_bytes(main, asset.path)
    support_bytes, support_files = _support_bytes(asset)
    return {
        "kind": asset.kind,
        "name": asset.name,
        "entry_bytes": entry_bytes,
        "entry_estimated_tokens": (entry_bytes + 3) // 4,
        "support_files": support_files,
        "support_bytes": support_bytes,
        "support_estimated_tokens": (support_bytes + 3) // 4,
        "potential_total_bytes": entry_bytes + support_bytes,
    }


def profile_footprint(manifest: Manifest, profile: str) -> dict[str, Any]:
    resolution = manifest.resolve_profiles([profile])
    assets = tuple(list(resolution.agents) + list(resolution.skills))
    records = [_asset_record(asset) for asset in assets]
    entry_bytes = sum(item["entry_bytes"] for item in records)
    support_bytes = sum(item["support_bytes"] for item in records)
    return {
        "schema": SCHEMA,
        "status": "pass",
        "profile": profile,
        "source_version": manifest.version,
        "accounting": {
            "method": "utf8-source-bytes",
            "token_estimate_method": "utf8-bytes-ceil-div-4",
            "token_estimate_is_provider_measurement": False,
            "progressive_disclosure": True,
        },
        "assets": {
            "agents": len(resolution.agents),
            "skills": len(resolution.skills),
            "total": len(records),
        },
        "entry_context": {
            "bytes": entry_bytes,
            "estimated_tokens": (entry_bytes + 3) // 4,
        },
        "deferred_support": {
            "files": sum(item["support_files"] for item in records),
            "bytes": support_bytes,
            "estimated_tokens": (support_bytes + 3) // 4,
        },
        "potential_full_surface": {
            "bytes": entry_bytes + support_bytes,
            "estimated_tokens": (entry_bytes + support_bytes + 3) // 4,
        },
        "largest_entries": sorted(
            records, key=lambda item: (-item["entry_bytes"], item["kind"], item["name"])
        )[:10],
        "largest_deferred_support": sorted(
            records, key=lambda item: (-item["support_bytes"], item["kind"], item["name"])
        )[:10],
    }


def compare_profiles(manifest: Manifest, baseline: str, candidate: str) -> dict[str, Any]:
    left = profile_footprint(manifest, baseline)
    right = profile_footprint(manifest, candidate)
    return {
        "schema": "adk-profile-context-comparison/v1",
        "status": "pass",
        "baseline": left,
        "candidate": right,
        "delta": {
            "assets": right["assets"]["total"] - left["assets"]["total"],
            "entry_bytes": right["entry_context"]["bytes"] - left["entry_context"]["bytes"],
            "entry_estimated_tokens": (
                right["entry_context"]["estimated_tokens"] - left["entry_context"]["estimated_tokens"]
            ),
            "deferred_support_bytes": (
                right["deferred_support"]["bytes"] - left["deferred_support"]["bytes"]
            ),
            "potential_full_surface_bytes": (
                right["potential_full_surface"]["bytes"] - left["potential_full_surface"]["bytes"]
            ),
        },
        "limitations": [
            "byte accounting is deterministic source evidence, not native runtime loading evidence",
            "token estimates use bytes/4 and are not provider tokenizer measurements",
            "deferred support bytes are potential on-demand surface, not assumed initial context",
        ],
        "lifecycle_authority": "none-evidence-only",
        "release_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure profile entry and deferred context surfaces")
    parser.add_argument("--root", default=".")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--compare")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = Manifest.load(Path(args.root).resolve())
        result = (
            compare_profiles(manifest, args.profile, args.compare)
            if args.compare
            else profile_footprint(manifest, args.profile)
        )
    except (OSError, ValueError, ManifestError, json.JSONDecodeError) as exc:
        result = {"schema": SCHEMA, "status": "fail", "error": str(exc)}
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
