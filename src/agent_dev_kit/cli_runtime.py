"""CLI runtime substrate: environment selection and stable output I/O."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .model import Manifest, ManifestError


def _discover_root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = [Path.cwd()] + list(Path(__file__).resolve().parents)
    for candidate in candidates:
        if (candidate / "manifest.json").is_file() and (candidate / "scripts" / "devkit.sh").is_file():
            return candidate.resolve()
    return Path.cwd().resolve()


ROOT = _discover_root()
DEFAULT_TASKS = ROOT / "tests" / "fixtures" / "product_eval_tasks.jsonl"


def _manifest() -> Manifest:
    if not (ROOT / "manifest.json").is_file():
        raise ManifestError("ADK asset root not found; run inside a checkout or set ADK_ROOT")
    return Manifest.load(ROOT)


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def _write_json(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _write_text(path: Path, value: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(value)
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _help() -> None:
    print("Usage:")
    print("  ./scripts/devkit.sh <command> [options]")
    print("")
    print("Commands:")
    for name, description in PUBLIC_COMMANDS:
        print("  {:24s} {}".format(name, description))
