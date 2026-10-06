"""Bounded JSON encoding and caller-owned atomic document publication."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from .model import ManifestError
from .strict_json import StrictJSONError, loads as load_strict_json


def encode_json_document(data: Mapping[str, Any], label: str) -> str:
    """Emit only object documents the bounded strict reader can consume."""
    try:
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        value = load_strict_json(text)
        if not isinstance(value, dict):
            raise ValueError("document must be an object")
    except (StrictJSONError, ValueError, TypeError, RecursionError) as exc:
        raise ManifestError("{} exceeds the strict JSON output contract".format(label)) from exc
    return text


def write_text_atomic(text: str, output: Path, mode: Optional[int] = None) -> None:
    """Publish from a random exclusive temporary descriptor, then close/replace.

    Callers control parent directories and writers. Publication is atomic;
    this does not provide a crash journal or prevent same-user interference.
    The default POSIX mode remains private (0600); public outputs opt in.
    """
    if mode is not None and (isinstance(mode, bool) or not isinstance(mode, int)
                             or mode < 0 or mode > 0o777):
        raise ManifestError("invalid document permission mode")
    output = Path(os.path.abspath(os.fspath(output)))
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise ManifestError("document output must be a regular file")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix="." + output.name + ".",
            suffix=".tmp", dir=str(output.parent), delete=False,
        ) as stream:
            temporary = Path(stream.name)
            if mode is not None:
                if hasattr(os, "fchmod"):
                    os.fchmod(stream.fileno(), mode)
                else:
                    temporary.chmod(mode)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temporary), str(output))
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
