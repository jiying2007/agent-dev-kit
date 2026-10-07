"""Bounded, unambiguous JSON decoding for caller-supplied evidence."""
from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path
from typing import Any, Sequence

DEFAULT_MAX_BYTES = 4 * 1024 * 1024
DEFAULT_MAX_DEPTH = 64


class StrictJSONError(ValueError):
    """Sanitized syntax, ambiguity or resource-boundary failure."""


def unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StrictJSONError("JSON contains duplicate object keys")
        value[key] = item
    return value


def _finite_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise StrictJSONError("JSON contains a non-finite number")
    return value


def _reject_constant(_text: str) -> Any:
    raise StrictJSONError("JSON contains a non-finite number")


def _depth_guard(text: str, maximum: int) -> None:
    depth = 0
    quoted = escaped = False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > maximum:
                raise StrictJSONError("JSON exceeds nesting budget")
        elif character in "]}":
            depth -= 1


def loads(data: str | bytes, *, max_bytes: int = DEFAULT_MAX_BYTES,
          max_depth: int = DEFAULT_MAX_DEPTH) -> Any:
    for limit in (max_bytes, max_depth):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise StrictJSONError("JSON budgets must be positive integers")
    if not isinstance(data, (str, bytes)):
        raise StrictJSONError("JSON input must be text or bytes")
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if len(raw) > max_bytes:
            raise StrictJSONError("JSON exceeds byte budget")
        text = raw.decode("utf-8")
        _depth_guard(text, max_depth)
        return json.loads(text, object_pairs_hook=unique_object,
                          parse_float=_finite_float, parse_constant=_reject_constant)
    except StrictJSONError:
        raise
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise StrictJSONError("invalid JSON input") from exc


def read_bytes(path: Path, *, max_bytes: int = DEFAULT_MAX_BYTES,
               regular_only: bool = False) -> bytes:
    """Read bounded bytes once so callers can hash the exact parsed payload."""
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        raise StrictJSONError("JSON byte budget must be a positive integer")
    try:
        if regular_only:
            # Bind the leaf check to the opened descriptor. NONBLOCK avoids a
            # replaced FIFO hanging before fstat; NOFOLLOW rejects leaf links.
            if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
                raise StrictJSONError("safe regular-file JSON reading is unavailable")
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    raise StrictJSONError("JSON input must be a regular file")
                with os.fdopen(descriptor, "rb", closefd=False) as stream:
                    data = stream.read(max_bytes + 1)
            finally:
                os.close(descriptor)
        else:
            with path.open("rb") as stream:
                data = stream.read(max_bytes + 1)
    except OSError as exc:
        raise StrictJSONError("JSON input cannot be read") from exc
    if len(data) > max_bytes:
        raise StrictJSONError("JSON exceeds byte budget")
    return data


def read(path: Path, *, max_bytes: int = DEFAULT_MAX_BYTES,
         max_depth: int = DEFAULT_MAX_DEPTH, regular_only: bool = False) -> Any:
    data = read_bytes(path, max_bytes=max_bytes, regular_only=regular_only)
    return loads(data, max_bytes=max_bytes, max_depth=max_depth)
