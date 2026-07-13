"""Deterministic target export for ADK assets."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

from .model import Asset, Manifest, ManifestError, ProfileResolution, ensure_within, sha256_file
from .locking import TargetLock


@dataclass(frozen=True)
class ExportedFile:
    kind: str
    name: str
    source: str
    destination: str
    sha256: str


def _content_file(asset: Asset) -> Path:
    filename = "AGENTS.md" if asset.kind == "agent" else "SKILL.md"
    path = asset.path / filename
    if not path.is_file():
        raise ManifestError("asset content missing: {}".format(path))
    return path


def _strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return text.rstrip() + "\n"
    try:
        end = lines.index("---", 1)
    except ValueError:
        return text.rstrip() + "\n"
    return "\n".join(lines[end + 1 :]).lstrip("\n").rstrip() + "\n"


def _destination(target: str, target_root: Path, asset: Asset) -> Path:
    if target == "claude-code":
        return target_root / ("agents" if asset.kind == "agent" else "skills") / (asset.name + ".md")
    if target == "hermes-agent":
        if asset.kind == "agent":
            return target_root / "agents" / asset.name / "instructions.md"
        return target_root / "skills" / asset.name / "SKILL.md"
    if target == "opencode":
        return target_root / "prompts" / asset.kind / (asset.name + ".md")
    raise ManifestError("no compiler adapter for target: {}".format(target))


def _render(manifest: Manifest, target: str, asset: Asset) -> str:
    source = _content_file(asset)
    metadata = [
        "---",
        "name: {}".format(asset.name),
        "kind: {}".format(asset.kind),
        "target: {}".format(target),
        "manifest_version: {}".format(manifest.version),
        "source: {}".format(source.relative_to(manifest.root).as_posix()),
        "---",
        "",
    ]
    return "\n".join(metadata) + _strip_frontmatter(source.read_text(encoding="utf-8"))


def export_assets(
    manifest: Manifest,
    target: str,
    output_root: Path,
    profiles: Sequence[str],
    optional_skills: Sequence[str] = (),
    clean: bool = False,
    dry_run: bool = False,
    lock_timeout_seconds: float = 0.0,
) -> Dict[str, object]:
    manifest.target(target)
    resolution = manifest.resolve_profiles(profiles, optional_skills)
    output_root = output_root.resolve()
    target_root = ensure_within(output_root / target, output_root, "export target")

    assets: List[Asset] = list(resolution.agents) + list(resolution.skills)
    planned = []
    for asset in assets:
        destination = _destination(target, target_root, asset)
        ensure_within(destination, target_root, "export destination")
        planned.append((asset, destination, _render(manifest, target, asset)))

    lock = nullcontext() if dry_run else TargetLock(target_root, "export", lock_timeout_seconds)
    with lock:
        if not dry_run:
            output_root.mkdir(parents=True, exist_ok=True)
            staging_parent = Path(tempfile.mkdtemp(prefix=".adk-export-", dir=str(output_root)))
            staging_target = staging_parent / target
            preserve_staging = False
            try:
                for asset, destination, content in planned:
                    relative = destination.relative_to(target_root)
                    staged = staging_target / relative
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    staged.write_text(content, encoding="utf-8")
                inventory = {
                    "schema_version": 1,
                    "manifest_version": manifest.version,
                    "manifest_sha256": manifest.digest,
                    "target": target,
                    "profiles": list(resolution.profiles),
                    "optional_skills": list(optional_skills),
                    "files": [
                        {
                            "kind": asset.kind,
                            "name": asset.name,
                            "path": destination.relative_to(target_root).as_posix(),
                        }
                        for asset, destination, _ in planned
                    ],
                }
                (staging_target / "adk-export-manifest.json").write_text(
                    json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                backup_target: Optional[Path] = None
                if target_root.exists() or target_root.is_symlink():
                    if not clean:
                        raise ManifestError("export target exists; use --clean: {}".format(target_root))
                    backup_target = staging_parent / (target + ".previous")
                    os.replace(str(target_root), str(backup_target))
                try:
                    os.replace(str(staging_target), str(target_root))
                except Exception as replacement_error:
                    if backup_target is not None and (backup_target.exists() or backup_target.is_symlink()):
                        try:
                            os.replace(str(backup_target), str(target_root))
                        except Exception as recovery_error:
                            preserve_staging = True
                            raise ManifestError(
                                "export replacement and recovery failed; recover previous target from {}"
                                .format(backup_target)
                            ) from recovery_error
                    raise
            finally:
                if not preserve_staging:
                    shutil.rmtree(str(staging_parent), ignore_errors=True)

        files = [
            {
                "kind": asset.kind,
                "name": asset.name,
                "source": _content_file(asset).relative_to(manifest.root).as_posix(),
                "destination": destination.relative_to(output_root).as_posix(),
                "sha256": "dry-run" if dry_run else sha256_file(destination),
            }
            for asset, destination, _ in planned
        ]
    return {
        "schema_version": 1,
        "status": "planned" if dry_run else "pass",
        "target": target,
        "output": str(target_root),
        "profiles": list(resolution.profiles),
        "agents": len(resolution.agents),
        "skills": len(resolution.skills),
        "optional_skills": len(optional_skills),
        "files": files,
    }
