"""Small standard-library compatibility helpers for supported Python versions."""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, Type, TypeVar, cast

T = TypeVar("T")


def frozen_slots_dataclass(cls: Type[T]) -> Type[T]:
    """Keep frozen dataclasses on 3.8 and retain slots where supported."""

    options: Dict[str, Any] = {"frozen": True}
    if sys.version_info >= (3, 10):
        options["slots"] = True
    return cast(Type[T], dataclass(**options)(cls))


def sha256_stream(stream: BinaryIO) -> str:
    """Hash a binary stream without relying on Python 3.11's file_digest."""

    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()
