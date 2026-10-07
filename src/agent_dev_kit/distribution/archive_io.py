"""Bounded, immutable archive snapshots and forward-only gzip inspection."""
from __future__ import annotations

import gzip
import io
import os
import tarfile
import zlib
from pathlib import Path
from typing import Protocol

from ..strict_json import StrictJSONError
from ..strict_json import read_bytes as read_bounded_bytes

MAX_COMPRESSED_BYTES = 64 * 1024 * 1024
MAX_DECODED_BYTES = 128 * 1024 * 1024
MAX_MEMBERS = 8192
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_NAME_BYTES = 4096
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_HEADER_READ_BYTES = 64 * 1024
MAX_METADATA_BYTES = 8 * 1024 * 1024
MAX_HEADERS_PER_MEMBER = 32
MAX_PAX_KEYS = 256
_CHUNK_BYTES = 64 * 1024
_JSON_NAMES = frozenset(("manifest.json", "release-manifest.json", "sbom.spdx.json"))


class ArchiveInputError(ValueError):
    """Sanitized malformed-input or resource-budget failure."""


class _Readable(Protocol):
    def read(self, size: int = -1) -> bytes: ...


class _ForwardTarReader(io.RawIOBase):
    """Count actual decoded bytes, including skipped payload and hidden headers."""

    def __init__(self, stream: _Readable) -> None:
        super().__init__()
        self.stream = stream
        self.position = 0
        self.metadata_bytes = 0
        self.header_reads = 0
        self.payload_mode = False
        self.skipping = False

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def read(self, size: int = -1) -> bytes:
        limit = MAX_JSON_BYTES + 512 if self.payload_mode else MAX_HEADER_READ_BYTES
        if size < 0 or size > limit:
            raise ArchiveInputError("release archive exceeds header read budget")
        metadata = not self.payload_mode and not self.skipping
        if metadata and size == 512:
            self.header_reads += 1
            if self.header_reads > MAX_HEADERS_PER_MEMBER:
                raise ArchiveInputError("release archive exceeds hidden header chain budget")
        data = self.stream.read(min(size, MAX_DECODED_BYTES - self.position + 1))
        self.position += len(data)
        if self.position > MAX_DECODED_BYTES:
            raise ArchiveInputError("release archive exceeds decoded byte budget")
        if metadata:
            self.metadata_bytes += len(data)
            if self.metadata_bytes > MAX_METADATA_BYTES:
                raise ArchiveInputError("release archive exceeds metadata byte budget")
        return data

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        target = self.position + offset if whence == os.SEEK_CUR else offset
        if whence not in (os.SEEK_SET, os.SEEK_CUR) or target < self.position:
            raise ArchiveInputError("release archive requires unsupported backward seek")
        if target > MAX_DECODED_BYTES:
            raise ArchiveInputError("release archive exceeds decoded byte budget")
        self.skipping = True
        try:
            while self.position < target:
                if not self.read(min(_CHUNK_BYTES, target - self.position)):
                    raise ArchiveInputError("release archive payload is truncated")
        finally:
            self.skipping = False
        return self.position


def load_archive_snapshot(artifact: Path, *, require_json: bool = True) -> tuple[bytes, dict[str, bytes]]:
    """Inspect one bounded regular-file snapshot; never extract to the filesystem.

    These byte/record limits do not replace OS CPU/memory limits. Callers own
    parent directories and writers. All later hashing/extraction must use raw.
    """
    artifact = Path(os.path.abspath(os.fspath(artifact)))
    try:
        raw = read_bounded_bytes(artifact, max_bytes=MAX_COMPRESSED_BYTES, regular_only=True)
    except (StrictJSONError, OSError, ValueError) as exc:
        raise ArchiveInputError("release artifact must be a bounded regular file") from exc
    return raw, inspect_archive_snapshot(raw, require_json=require_json)


def inspect_archive_snapshot(raw: bytes, *, require_json: bool = True) -> dict[str, bytes]:
    """Preflight already-captured bytes without reopening a path."""
    if not isinstance(raw, bytes) or len(raw) > MAX_COMPRESSED_BYTES:
        raise ArchiveInputError("release artifact exceeds compressed byte budget")
    payloads: dict[str, bytes] = {}
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as compressed, _ForwardTarReader(compressed) as reader:
            with tarfile.TarFile(fileobj=reader, mode="r") as archive:
                count = 0
                while True:
                    reader.header_reads = 0
                    member = archive.next()
                    if member is None:
                        break
                    # Retaining TarInfo also retains copied global PAX maps.
                    cached = getattr(archive, "members", None)
                    if not isinstance(cached, list):
                        raise ArchiveInputError("unsupported tar member cache contract")
                    cached.clear()
                    count += 1
                    if count > MAX_MEMBERS:
                        raise ArchiveInputError("release archive exceeds member budget")
                    if len(archive.pax_headers or {}) > MAX_PAX_KEYS or len(member.pax_headers) > MAX_PAX_KEYS:
                        raise ArchiveInputError("release archive exceeds PAX key budget")
                    if len(member.name.encode("utf-8", errors="surrogatepass")) > MAX_NAME_BYTES:
                        raise ArchiveInputError("release archive exceeds member name budget")
                    if member.size < 0 or member.size > MAX_MEMBER_BYTES:
                        raise ArchiveInputError("release archive exceeds member byte budget")
                    if member.name not in _JSON_NAMES:
                        continue
                    if member.name in payloads or not member.isreg() or member.issparse():
                        raise ArchiveInputError("release JSON member must be one regular file")
                    if member.size > MAX_JSON_BYTES:
                        raise ArchiveInputError("release JSON member exceeds byte budget")
                    source = archive.extractfile(member)
                    if source is None:
                        raise ArchiveInputError("release JSON member cannot be read")
                    reader.payload_mode = True
                    try:
                        with source:
                            data = source.read(MAX_JSON_BYTES + 1)
                    finally:
                        reader.payload_mode = False
                    if len(data) != member.size:
                        raise ArchiveInputError("release JSON member is truncated")
                    payloads[member.name] = data
            # Tar EOF may precede gzip EOF. Account for padding/concatenated
            # streams and validate gzip CRC rather than trusting a prefix.
            reader.skipping = True
            while reader.read(_CHUNK_BYTES):
                pass
    except ArchiveInputError:
        raise
    except (OSError, EOFError, tarfile.TarError, ValueError, OverflowError, RecursionError, zlib.error) as exc:
        raise ArchiveInputError("invalid release archive stream") from exc
    if require_json and set(payloads) != _JSON_NAMES:
        raise ArchiveInputError("release archive is missing required JSON members")
    return payloads
