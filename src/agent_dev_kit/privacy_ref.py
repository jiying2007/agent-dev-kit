"""Shared privacy, identifier, opaque-reference and evidence-file validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Tuple

from .model import ManifestError, ensure_within, sha256_file


IDENTIFIER_PATTERN = r"^[a-z0-9][a-z0-9._:/-]{0,127}$"
OPAQUE_REF_PATTERN = r"^ref:[0-9a-f]{64}$"
SHA256_PATTERN = r"^[0-9a-f]{64}$"
EVIDENCE_PATH_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,511}$"

_IDENTIFIER_RE = re.compile(IDENTIFIER_PATTERN)
_OPAQUE_REF_RE = re.compile(OPAQUE_REF_PATTERN)
_SHA256_RE = re.compile(SHA256_PATTERN)
_EVIDENCE_PATH_RE = re.compile(EVIDENCE_PATH_PATTERN)

_FORBIDDEN_KEYS = frozenset({
    "prompt",
    "prompts",
    "raw_prompt",
    "system_prompt",
    "message",
    "messages",
    "raw_message",
    "input_message",
    "input_messages",
    "output_message",
    "output_messages",
    "password",
    "passwords",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "api_key",
    "access_token",
    "private_key",
    "raw_log",
    "tool_payload",
    "tool_arguments",
    "tool_result",
    "tool_results",
})

_SECRET_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\bghp_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}=*\b", re.IGNORECASE),
    re.compile(r"\b(?:password|secret|credential|api[_ -]?key)\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"\b(?:raw[ _.-]?prompt|raw[ _.-]?message|tool[ _.-]?payload)\b", re.IGNORECASE),
)


def _walk(value: Any, path: Tuple[str, ...] = ()) -> Iterator[Tuple[Tuple[str, ...], Optional[str], Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = path + (str(key),)
            yield child_path, str(key), child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = path + (str(index),)
            yield child_path, None, child
            yield from _walk(child, child_path)


def validate_no_secrets(value: Any, label: str) -> None:
    for path, key, child in _walk(value):
        normalized = str(key).casefold().replace(".", "_").replace("-", "_") if key is not None else ""
        if normalized in _FORBIDDEN_KEYS:
            raise ManifestError("{} contains forbidden sensitive field at {}".format(label, "/".join(path)))
        if isinstance(child, str) and any(pattern.search(child) for pattern in _SECRET_VALUE_PATTERNS):
            raise ManifestError("{} contains secret-like content at {}".format(label, "/".join(path)))
    if isinstance(value, str) and any(pattern.search(value) for pattern in _SECRET_VALUE_PATTERNS):
        raise ManifestError("{} contains secret-like content".format(label))


def validate_identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER_RE.fullmatch(value) is None:
        raise ManifestError("{} must be a lowercase opaque identifier".format(label))
    validate_no_secrets(value, label)
    return value


def validate_opaque_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or _OPAQUE_REF_RE.fullmatch(value) is None:
        raise ManifestError("{} must use ref:<sha256> opaque-reference form".format(label))
    return value


def validate_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ManifestError("{} must be a lowercase SHA-256 digest".format(label))
    return value


def validate_evidence_ref(
    value: Any,
    evidence_root: Path,
    label: str,
    *,
    expected_sha256: Optional[str] = None,
) -> Path:
    required = {"ref", "path", "sha256"}
    if not isinstance(value, Mapping) or set(value) != required:
        raise ManifestError("{} must be a typed evidence reference".format(label))
    opaque_ref = validate_opaque_ref(value.get("ref"), "{}.ref".format(label))
    digest = validate_sha256(value.get("sha256"), "{}.sha256".format(label))
    if opaque_ref != "ref:{}".format(digest):
        raise ManifestError("{} opaque ref must bind its SHA-256 digest".format(label))
    if expected_sha256 is not None and digest != expected_sha256:
        raise ManifestError("{} digest differs from content_sha256".format(label))
    raw_path = value.get("path")
    if not isinstance(raw_path, str) or _EVIDENCE_PATH_RE.fullmatch(raw_path) is None:
        raise ManifestError("{}.path must be a bounded relative evidence path".format(label))
    validate_no_secrets(raw_path, "{}.path".format(label))
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ManifestError("{}.path must not escape evidence root".format(label))
    candidate = evidence_root / relative
    current = evidence_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ManifestError("{} path must not traverse a symlink".format(label))
    path = ensure_within(candidate, evidence_root, label)
    if not path.is_file():
        raise ManifestError("{} path is missing or unsafe".format(label))
    if sha256_file(path) != digest:
        raise ManifestError("{} file digest mismatch".format(label))
    return path


def opaque_ref_for_sha256(digest: str) -> str:
    return "ref:{}".format(validate_sha256(digest, "opaque ref digest"))
