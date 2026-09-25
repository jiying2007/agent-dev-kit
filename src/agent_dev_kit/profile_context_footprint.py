"""Deterministic profile-level source context surface accounting.

This module measures repository bytes only. It does not claim which files a
runtime places in the initial prompt. Token counts are bytes/4 heuristics, not
provider tokenizer measurements.
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


def _regular_file_bytes(path: Path, root: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ManifestError(f"context_footprint_invalid_file: {path}")
    ensure_within(path, root, "context footprint source")
    return path.read_bytes()


def _entry_parts(path: Path, root: Path) -> tuple[int, int, int]:
    raw = _regular_file_bytes(path, root)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError(f"context_footprint_non_utf8_entry: {path}") from exc
    metadata_bytes = 0
    if text.startswith("---\n"):
        marker = text.find("\n---\n", 4)
        if marker < 0:
            raise ManifestError(f"context_footprint_invalid_frontmatter: {path}")
        metadata_bytes = len(text[: marker + 5].encode("utf-8"))
    body_bytes = len(raw) - metadata_bytes
    return len(raw), metadata_bytes, body_bytes


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
            total += len(_regular_file_bytes(path, asset.path))
            files += 1
    return total, files


def _asset_record(asset: Asset) -> dict[str, Any]:
    entry_bytes, metadata_bytes, body_bytes = _entry_parts(_main_file(asset), asset.path)
    support_bytes, support_files = _support_bytes(asset)
    return {
        "kind": asset.kind,
        "name": asset.name,
        "entry_bytes": entry_bytes,
        "frontmatter_bytes": metadata_bytes,
        "body_bytes": body_bytes,
        "support_files": support_files,
        "support_bytes": support_bytes,
        "potential_total_bytes": entry_bytes + support_bytes,
    }


def _surface(bytes_value: int) -> dict[str, Any]:
    return {
        "bytes": bytes_value,
        "estimated_tokens": (bytes_value + 3) // 4,
        "token_estimate_method": "utf8-bytes-ceil-div-4",
        "token_estimate_is_provider_measurement": False,
    }


def profile_footprint(manifest: Manifest, profile: str) -> dict[str, Any]:
    resolution = manifest.resolve_profiles([profile])
    assets = tuple(list(resolution.agents) + list(resolution.skills))
    records = [_asset_record(asset) for asset in assets]
    entry_bytes = sum(item["entry_bytes"] for item in records)
    metadata_bytes = sum(item["frontmatter_bytes"] for item in records)
    body_bytes = sum(item["body_bytes"] for item in records)
    support_bytes = sum(item["support_bytes"] for item in records)
    return {
        "schema": SCHEMA,
        "status": "pass",
        "profile": profile,
        "source_version": manifest.version,
        "accounting": {
            "method": "utf8-source-bytes",
            "runtime_initial_context_measured": False,
            "progressive_disclosure_surfaces_separated": True,
        },
        "assets": {
            "agents": len(resolution.agents),
            "skills": len(resolution.skills),
            "total": len(records),
        },
        "frontmatter_surface": _surface(metadata_bytes),
        "entry_body_surface": _surface(body_bytes),
        "entry_file_surface": _surface(entry_bytes),
        "deferred_support_surface": {
            **_surface(support_bytes),
            "files": sum(item["support_files"] for item in records),
        },
        "potential_full_source_surface": _surface(entry_bytes + support_bytes),
        "largest_entry_files": sorted(
            records, key=lambda item: (-item["entry_bytes"], item["kind"], item["name"])
        )[:10],
        "largest_deferred_support": sorted(
            records, key=lambda item: (-item["support_bytes"], item["kind"], item["name"])
        )[:10],
        "limitations": [
            "source byte surfaces do not prove what a native runtime injects into initial context",
            "frontmatter is a deterministic metadata proxy, not proof that a runtime loads all metadata",
            "token estimates use bytes/4 and are not provider tokenizer measurements",
            "deferred support is a potential on-demand surface, not assumed loaded context",
        ],
    }


def enforce_profile_ratchet(manifest: Manifest, profile: str) -> dict[str, Any]:
    path = manifest.root / "manifests" / "profile_context_ratchets.json"
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("profile_context_ratchet_invalid") from exc
    if policy.get("schema") != "adk-profile-context-ratchets/v1":
        raise ManifestError("profile_context_ratchet_schema_invalid")
    expected = policy.get("profiles", {}).get(profile)
    if not isinstance(expected, dict):
        raise ManifestError(f"profile_context_ratchet_missing: {profile}")
    actual = profile_footprint(manifest, profile)
    failures = []
    checks = {
        "entry_file_bytes": actual["entry_file_surface"]["bytes"],
        "potential_full_source_bytes": actual["potential_full_source_surface"]["bytes"],
    }
    for name, value in checks.items():
        limit = expected.get(name)
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            raise ManifestError(f"profile_context_ratchet_limit_invalid: {profile}:{name}")
        if value > limit:
            failures.append(f"{name} grew: actual={value} ratchet={limit}")
    return {
        "schema": "adk-profile-context-ratchet-result/v1",
        "status": "fail" if failures else "pass",
        "profile": profile,
        "actual": checks,
        "ratchet": {
            "entry_file_bytes": expected["entry_file_bytes"],
            "potential_full_source_bytes": expected["potential_full_source_bytes"],
        },
        "asset_count": actual["assets"]["total"],
        "asset_count_baseline": expected.get("assets"),
        "failures": failures,
        "semantics": policy.get("semantics"),
        "runtime_initial_context_claim": False,
        "release_authorized": False,
    }


def compare_profiles(manifest: Manifest, baseline: str, candidate: str) -> dict[str, Any]:
    left = profile_footprint(manifest, baseline)
    right = profile_footprint(manifest, candidate)

    def delta(surface: str) -> int:
        return right[surface]["bytes"] - left[surface]["bytes"]

    return {
        "schema": "adk-profile-context-comparison/v1",
        "status": "pass",
        "baseline": left,
        "candidate": right,
        "delta": {
            "assets": right["assets"]["total"] - left["assets"]["total"],
            "frontmatter_bytes": delta("frontmatter_surface"),
            "entry_body_bytes": delta("entry_body_surface"),
            "entry_file_bytes": delta("entry_file_surface"),
            "deferred_support_bytes": delta("deferred_support_surface"),
            "potential_full_source_bytes": delta("potential_full_source_surface"),
        },
        "limitations": [
            "byte accounting is deterministic source evidence, not native runtime loading evidence",
            "no delta is an effectiveness or quality score",
            "runtime token usage must come from runtime evidence when available",
        ],
        "lifecycle_authority": "none-evidence-only",
        "release_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure profile source context surfaces")
    parser.add_argument("--root", default=".")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--compare")
    parser.add_argument("--ratchet", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        manifest = Manifest.load(Path(args.root).resolve())
        if args.compare and args.ratchet:
            raise ManifestError("--compare and --ratchet are mutually exclusive")
        result = (
            compare_profiles(manifest, args.profile, args.compare)
            if args.compare
            else enforce_profile_ratchet(manifest, args.profile)
            if args.ratchet
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
