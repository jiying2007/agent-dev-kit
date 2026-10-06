"""Bounded report-only maintenance inventory; never deletes or changes modes."""
from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, List

from .model import ManifestError

MAX_ENTRIES = 2000
GENERATED_AREAS = (".cache", "dist")
PRESERVED_DIRS = {".git", ".backups", ".adk-backups", "backups", "credentials",
                  "auth", "sessions", "memories", "local-ci"}


def create_plan(root: Path, level: str = "basic") -> Dict[str, Any]:
    if level not in ("basic", "medium", "advanced"):
        raise ManifestError("unknown maintenance level")
    root = root.resolve()
    if not (root / "manifest.json").is_file():
        raise ManifestError("maintenance root must contain an ADK manifest")
    candidates: List[Dict[str, Any]] = []
    seen = 0
    if (not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY")
            or os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd
            or os.scandir not in os.supports_fd):
        raise ManifestError("safe directory inventory is unavailable on this platform")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    def visit(parent: int, name: str, relative: str, depth: int) -> None:
        nonlocal seen
        seen += 1
        if seen > MAX_ENTRIES:
            raise ManifestError("maintenance inventory exceeds entry budget")
        if depth > 64:
            raise ManifestError("maintenance inventory exceeds nesting budget")
        info = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode):
            candidates.append({"path": relative, "kind": "symlink", "disposition": "preserve"})
        elif stat.S_ISDIR(info.st_mode):
            if name in PRESERVED_DIRS:
                candidates.append({"path": relative, "kind": "protected-directory",
                                   "disposition": "preserve"})
                return
            descriptor = os.open(name, flags, dir_fd=parent)
            try:
                opened = os.fstat(descriptor)
                if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                    raise ManifestError("maintenance directory changed during inventory")
                # Descriptor-relative traversal never follows a replaced path.
                # Consume entries incrementally; no unbounded sort or queue.
                with os.scandir(descriptor) as stream:
                    for entry in stream:
                        visit(descriptor, entry.name, relative + "/" + entry.name, depth + 1)
            finally:
                os.close(descriptor)
        elif stat.S_ISREG(info.st_mode):
            candidates.append({"path": relative, "kind": "file", "bytes": info.st_size,
                               "sha256": None, "digest_capture": "not-performed-report-only",
                               "mode": format(stat.S_IMODE(info.st_mode), "04o"),
                               "disposition": "review-only", "execution_eligible": False})
        else:
            candidates.append({"path": relative, "kind": "special", "disposition": "preserve"})
    descriptor = os.open(root, flags)
    try:
        for name in GENERATED_AREAS:
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            visit(descriptor, name, name, 1)
    finally:
        os.close(descriptor)
    return {"schema": "adk-maintenance-plan/v1", "status": "planned", "level": level,
            "read_only": True, "apply": 0, "applied": False, "execution_supported": False,
            "inventory_scope": list(GENERATED_AREAS), "entries_scanned": seen,
            "candidates": sorted(candidates, key=lambda item: item["path"]),
            "preserved": ["source", "user-logs", "credentials", "sessions", "backups", "git",
                          "verification-receipts"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--level", default="basic", choices=("basic", "medium", "advanced"))
    parser.add_argument("--summary-json", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.apply:
            raise ManifestError("maintenance execution requires a reviewed bounded action contract; report-only supported")
        result = create_plan(args.root, args.level)
    except (ManifestError, OSError) as exc:
        print(json.dumps({"schema": "adk-maintenance-plan/v1", "status": "blocked",
                          "reason": str(exc) if isinstance(exc, ManifestError) else "inventory cannot be read safely",
                          "read_only": True, "applied": False,
                          "execution_supported": False}))
        return 2
    if args.summary_json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("[PLAN] report-only maintenance; no files modified")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
