"""Deterministic target export for ADK assets."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import Dict, Optional, Sequence

from .locking import TargetLock
from .model import Manifest, ManifestError, ensure_within
from .targets import render_selection


def export_assets(
    manifest: Manifest,
    target: str,
    output_root: Path,
    profiles: Sequence[str],
    optional_skills: Sequence[str] = (),
    asset_kind: Optional[str] = None,
    clean: bool = False,
    dry_run: bool = False,
    lock_timeout_seconds: float = 0.0,
) -> Dict[str, object]:
    bundle = render_selection(manifest, target, profiles, optional_skills, asset_kind)
    output_root = output_root.resolve()
    target_root = ensure_within(output_root / target, output_root, "export target")

    lock = nullcontext() if dry_run else TargetLock(target_root, "export", lock_timeout_seconds)
    with lock:
        if not dry_run:
            output_root.mkdir(parents=True, exist_ok=True)
            staging_parent = Path(tempfile.mkdtemp(prefix=".adk-export-", dir=str(output_root)))
            staging_target = staging_parent / target
            preserve_staging = False
            try:
                for rendered in bundle.files:
                    staged = ensure_within(
                        staging_target / rendered.destination,
                        staging_target,
                        "staged export destination",
                    )
                    staged.parent.mkdir(parents=True, exist_ok=True)
                    staged.write_bytes(rendered.content)
                    staged.chmod(rendered.mode)
                inventory = {
                    "schema": "adk-export-manifest/v2",
                    "schema_version": 2,
                    "manifest_version": manifest.version,
                    "manifest_sha256": manifest.digest,
                    "target": target,
                    "contract_sha256": bundle.contract.digest,
                    "contract_status": bundle.contract.status,
                    "profiles": list(bundle.resolution.profiles),
                    "optional_skills": list(optional_skills),
                    "asset_kind": asset_kind,
                    "files": [
                        {
                            "kind": rendered.kind,
                            "name": rendered.name,
                            "source": rendered.source,
                            "path": rendered.destination,
                            "sha256": rendered.sha256,
                            "mode": format(rendered.mode, "04o"),
                        }
                        for rendered in bundle.files
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
                except Exception:
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
                "kind": rendered.kind,
                "name": rendered.name,
                "source": rendered.source,
                "destination": (Path(target) / rendered.destination).as_posix(),
                "sha256": rendered.sha256,
                "mode": format(rendered.mode, "04o"),
                "written": not dry_run,
            }
            for rendered in bundle.files
        ]
    return {
        "schema": "adk-export-result/v2",
        "schema_version": 2,
        "status": "planned" if dry_run else "pass",
        "target": target,
        "contract_sha256": bundle.contract.digest,
        "contract_status": bundle.contract.status,
        "output": str(target_root),
        "profiles": list(bundle.resolution.profiles),
        "asset_kind": asset_kind,
        "agents": bundle.agent_count,
        "skills": bundle.skill_count,
        "optional_skills": len(optional_skills),
        "files": files,
    }
