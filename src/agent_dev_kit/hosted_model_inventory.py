"""Bounded, read-only identity checks for the pilot's Ollama v0.40.16 store.

This does not relax work/Skill inventories or publication rules. The supported
Linux writer uses relative v2 name links to directly addressed manifest blobs.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
from typing import Any

from .strict_json import StrictJSONError, loads

MAX_ENTRIES = 4096
MAX_DEPTH = 8
MAX_JSON_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_LINK_BYTES = 4096
MAX_CHILDREN = 64
MANIFEST_TYPE = "application/vnd.docker.distribution.manifest.v2+json"
LIST_TYPE = "application/vnd.ollama.manifest.list.v2+json"
_DIGEST = re.compile(r"(?:sha256:)?([0-9a-f]{64})")
_BLOB = re.compile(r"sha256-([0-9a-f]{64})")
_COMPONENT = re.compile(r"[a-z0-9][a-z0-9._-]*")
_DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
Signature = tuple[int, int, int, int, int, int]


class ModelInventoryError(RuntimeError):
    """The collection or identity cannot be admitted before inference."""


def _signature(info: os.stat_result) -> Signature:
    return info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns


@contextmanager
def _directory(start: int, parts: tuple[str, ...]) -> Iterator[int]:
    descriptor = os.dup(start)
    try:
        for part in parts:
            next_descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        yield descriptor
    except OSError as error:
        raise ModelInventoryError("Missing, linked, or unsafe model directory") from error
    finally:
        os.close(descriptor)


@contextmanager
def _root_directory(root: Path) -> Iterator[int]:
    if not root.is_absolute() or root == Path("/") or ".." in root.parts or len(root.parts) > 64:
        raise ModelInventoryError("Model root must be a bounded absolute directory path")
    anchor = os.open("/", _DIRECTORY_FLAGS)
    try:
        with _directory(anchor, root.parts[1:]) as descriptor:
            yield descriptor
    finally:
        os.close(anchor)


@contextmanager
def _plain_file(parent: int, name: str, expected: Signature) -> Iterator[int]:
    descriptor = os.open(name, _FILE_FLAGS, dir_fd=parent)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or _signature(info) != expected:
            raise ModelInventoryError("Model file identity changed before reading")
        yield descriptor
        if _signature(os.fstat(descriptor)) != expected:
            raise ModelInventoryError("Model file identity changed while reading")
    finally:
        os.close(descriptor)


def _stream_digest(parent: int, name: str, expected: Signature) -> str:
    digest = hashlib.sha256()
    total = 0
    with _plain_file(parent, name, expected) as descriptor:
        while chunk := os.read(descriptor, 1024 * 1024):
            total += len(chunk)
            if total > expected[3]:
                raise ModelInventoryError("Model file grew while hashing")
            digest.update(chunk)
    if total != expected[3]:
        raise ModelInventoryError("Model file size changed while hashing")
    return digest.hexdigest()


def _json_object(data: bytes) -> dict[str, Any]:
    try:
        value = loads(data, max_bytes=MAX_JSON_BYTES, max_depth=MAX_JSON_DEPTH)
    except StrictJSONError as error:
        raise ModelInventoryError(f"Invalid model identity JSON: {error}") from error
    if not isinstance(value, dict):
        raise ModelInventoryError("Model identity must be a JSON object")
    return value


def _small_bytes(parent: int, name: str, expected: Signature) -> bytes:
    if expected[3] > MAX_JSON_BYTES:
        raise ModelInventoryError("Model identity JSON exceeds byte limit")
    with _plain_file(parent, name, expected) as descriptor:
        chunks = []
        remaining = MAX_JSON_BYTES + 1
        while remaining and (chunk := os.read(descriptor, min(65536, remaining))):
            chunks.append(chunk)
            remaining -= len(chunk)
    data = b"".join(chunks)
    if len(data) > MAX_JSON_BYTES or len(data) != expected[3]:
        raise ModelInventoryError("Model identity size changed or exceeded byte limit")
    return data


def read_model_record(path: Path) -> dict[str, Any]:
    """Read the native API record without following links or unbounded JSON."""
    try:
        with _root_directory(path.parent) as parent:
            info = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise ModelInventoryError("Model API record must be a plain file")
            return _json_object(_small_bytes(parent, path.name, _signature(info)))
    except OSError as error:
        raise ModelInventoryError("Cannot safely read model API record") from error


def _allowed_link(parts: tuple[str, ...]) -> bool:
    return (
        len(parts) == 5
        and parts[:3] == ("manifests-v2", "ollama.com", "library")
        and all(_COMPONENT.fullmatch(part) for part in parts[3:])
        and all(part not in (".", "..") for part in parts)
    )


def _link_destination(parts: tuple[str, ...], raw: str) -> str:
    if not raw or raw.startswith("/") or len(raw.encode("utf-8")) > MAX_LINK_BYTES:
        raise ModelInventoryError("Absolute or oversized model link target")
    result = list(parts[:-1])
    for component in PurePosixPath(raw).parts:
        if component == "..":
            if not result:
                raise ModelInventoryError("Model link target escapes root")
            result.pop()
        elif component != ".":
            result.append(component)
    if len(result) != 2 or result[0] != "blobs" or not _BLOB.fullmatch(result[1]):
        raise ModelInventoryError("Model link must directly name a content-addressed blob")
    destination = "/".join(result)
    if raw != posixpath.relpath(destination, "/".join(parts[:-1])):
        raise ModelInventoryError("Model link target is not the official canonical relative path")
    return destination


def _scan(root: int) -> tuple[dict[str, dict[str, Any]], dict[str, Signature]]:
    files: dict[str, dict[str, Any]] = {}
    identities: dict[str, Signature] = {}

    def visit(directory: int, prefix: tuple[str, ...]) -> None:
        before = _signature(os.fstat(directory))
        with os.scandir(directory) as entries:
            for entry in entries:
                parts = (*prefix, entry.name)
                relative = "/".join(parts)
                if len(parts) > MAX_DEPTH or len(identities) >= MAX_ENTRIES:
                    raise ModelInventoryError("Model tree exceeds depth or entry limit")
                relative.encode("utf-8")
                info = os.stat(entry.name, dir_fd=directory, follow_symlinks=False)
                identity = _signature(info)
                identities[relative] = identity
                if stat.S_ISDIR(info.st_mode):
                    with _directory(directory, (entry.name,)) as child:
                        if _signature(os.fstat(child)) != identity:
                            raise ModelInventoryError("Model directory identity changed")
                        visit(child, parts)
                elif stat.S_ISREG(info.st_mode):
                    if (
                        parts[0] in ("manifests", "manifests-v2") or entry.name.endswith(".json")
                    ) and info.st_size > MAX_JSON_BYTES:
                        raise ModelInventoryError("Model identity JSON exceeds byte limit")
                    digest = _stream_digest(directory, entry.name, identity)
                    if parts[0] == "blobs":
                        match = _BLOB.fullmatch(entry.name) if len(parts) == 2 else None
                        if match is None or match[1] != digest:
                            raise ModelInventoryError("Blob filename does not match complete content digest")
                    files[relative] = {"kind": "file", "sha256": digest, "bytes": info.st_size}
                elif stat.S_ISLNK(info.st_mode):
                    if not _allowed_link(parts):
                        raise ModelInventoryError("Link outside supported official v2 manifest location")
                    raw = os.readlink(entry.name, dir_fd=directory)
                    destination = _link_destination(parts, raw)
                    if _signature(os.stat(entry.name, dir_fd=directory, follow_symlinks=False)) != identity:
                        raise ModelInventoryError("Model link identity changed")
                    files[relative] = {
                        "kind": "symlink",
                        "target": raw,
                        "normalized_target": destination,
                        "link_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    }
                else:
                    raise ModelInventoryError("Special model filesystem object is unsupported")
        if _signature(os.fstat(directory)) != before:
            raise ModelInventoryError("Model directory changed during enumeration")

    visit(root, ())
    for item in files.values():
        if item["kind"] == "symlink":
            target = files.get(item["normalized_target"])
            if target is None or target["kind"] != "file":
                raise ModelInventoryError("Dangling, chained, or directory model link")
            item.update(target_sha256=target["sha256"], target_bytes=target["bytes"])
    return dict(sorted(files.items())), identities


def _digest(value: object) -> str:
    match = _DIGEST.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise ModelInventoryError("Full canonical SHA256 model digest is required")
    return match[1]


def _read_manifest(
    root: int, path: str, files: dict[str, dict[str, Any]], identities: dict[str, Signature]
) -> tuple[dict[str, Any], dict[str, Any]]:
    item = files.get(path)
    if item is None or item["kind"] != "file":
        raise ModelInventoryError("Manifest must resolve to an inventoried plain file")
    parts = PurePosixPath(path).parts
    with _directory(root, parts[:-1]) as parent:
        data = _small_bytes(parent, parts[-1], identities[path])
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ModelInventoryError("Manifest identity changed after enumeration")
    parsed = _json_object(data)
    if type(parsed.get("schemaVersion")) is not int or parsed["schemaVersion"] != 2:
        raise ModelInventoryError("Unsupported manifest schema version")
    return parsed, {"path": path, "sha256": item["sha256"], "bytes": len(data), "raw_utf8": data.decode("utf-8")}


def _verify_leaf(leaf: dict[str, Any], files: dict[str, dict[str, Any]], runner: str) -> None:
    if leaf.get("mediaType") != MANIFEST_TYPE or "manifests" in leaf:
        raise ModelInventoryError("Nested or unsupported leaf manifest")
    if leaf.get("runner", runner) != runner:
        raise ModelInventoryError("Leaf runner does not match native API record")
    config, layers = leaf.get("config"), leaf.get("layers")
    if not isinstance(config, dict) or not isinstance(layers, list) or len(layers) > MAX_ENTRIES:
        raise ModelInventoryError("Incomplete leaf manifest")
    for layer in [config, *layers]:
        if not isinstance(layer, dict):
            raise ModelInventoryError("Invalid manifest layer descriptor")
        digest = _digest(layer.get("digest"))
        item = files.get("blobs/sha256-" + digest)
        if item is None or item["kind"] != "file" or item["sha256"] != digest:
            raise ModelInventoryError("Manifest references a missing or unverified blob")
        size = layer.get("size")
        if type(size) is not int or size < 0 or size != item["bytes"]:
            raise ModelInventoryError("Manifest layer size does not match blob")


def _bind(
    root: int,
    files: dict[str, dict[str, Any]],
    identities: dict[str, Signature],
    model: Mapping[str, Any],
    expected_name: str,
) -> dict[str, Any]:
    parts = expected_name.split(":")
    if len(parts) != 2 or not all(_COMPONENT.fullmatch(part) and part not in (".", "..") for part in parts):
        raise ModelInventoryError("Only an explicit canonical public model and tag are supported")
    if model.get("name") != expected_name or model.get("model") != expected_name:
        raise ModelInventoryError("API record does not identify the selected model name")
    digest = _digest(model.get("digest"))
    details = model.get("details")
    runner = details.get("runner") if isinstance(details, dict) else None
    if runner not in ("ggml", "llamacpp", "mlx"):
        raise ModelInventoryError("API record lacks a supported explicit runner")
    suffix = "/".join(parts)
    choices = [
        "manifests-v2/ollama.com/library/" + suffix,
        "manifests/registry.ollama.ai/library/" + suffix,
        "manifests/ollama.com/library/" + suffix,
    ]
    named = next((path for path in choices if path in identities), None)
    if named is None or named not in files:
        raise ModelInventoryError("Selected canonical named manifest is missing or not a file")
    item = files[named]
    path = item["normalized_target"] if item["kind"] == "symlink" else named
    parent, parent_record = _read_manifest(root, path, files, identities)
    leaf, leaf_record = parent, parent_record
    binding = "direct-manifest"
    if parent.get("mediaType") == LIST_TYPE:
        children = parent.get("manifests")
        if not isinstance(children, list) or not 1 <= len(children) <= MAX_CHILDREN:
            raise ModelInventoryError("Manifest list exceeds supported bounds")
        matches = []
        seen: set[tuple[str, str]] = set()
        for child in children:
            if (
                not isinstance(child, dict)
                or child.get("mediaType") != MANIFEST_TYPE
                or any(key in child for key in ("config", "layers", "manifests"))
            ):
                raise ModelInventoryError("Inline or nested manifest list entry is unsupported")
            child_digest = _digest(child.get("digest"))
            child_runner = child.get("runner")
            if child_runner not in ("ggml", "llamacpp", "mlx") or (child_digest, child_runner) in seen:
                raise ModelInventoryError("Ambiguous or unsupported child descriptor")
            seen.add((child_digest, child_runner))
            if child_digest == digest:
                matches.append(child)
        if len(matches) != 1 or matches[0]["runner"] != runner:
            raise ModelInventoryError("API digest and runner do not select one child descriptor")
        leaf, leaf_record = _read_manifest(root, "blobs/sha256-" + digest, files, identities)
        binding = "manifest-list-child"
    if leaf_record["sha256"] != digest:
        raise ModelInventoryError("Selected manifest bytes do not match complete API digest")
    _verify_leaf(leaf, files, runner)
    return {
        "model_name": expected_name,
        "named_entry": named,
        "binding": binding,
        "api_digest": digest,
        "api_runner": runner,
        "named_manifest": parent_record,
        "selected_manifest": leaf_record,
    }


def inventory_model_store(root: Path, model: Mapping[str, Any], expected_name: str) -> dict[str, Any]:
    """Freeze files, allowed links, and canonical-name/API manifest identity."""
    try:
        with _root_directory(root) as descriptor:
            initial = _signature(os.fstat(descriptor))
            files, identities = _scan(descriptor)
            binding = _bind(descriptor, files, identities, model, expected_name)
            for relative, expected in identities.items():
                parts = PurePosixPath(relative).parts
                with _directory(descriptor, parts[:-1]) as parent:
                    if _signature(os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)) != expected:
                        raise ModelInventoryError("Model tree identity changed before freezing")
            with _root_directory(root) as current:
                if _signature(os.fstat(current)) != initial:
                    raise ModelInventoryError("Model root identity changed before freezing")
            return {
                "files": files,
                "identity": binding,
                "limits": {
                    "entries": MAX_ENTRIES,
                    "depth": MAX_DEPTH,
                    "json_bytes": MAX_JSON_BYTES,
                    "json_depth": MAX_JSON_DEPTH,
                    "manifest_children": MAX_CHILDREN,
                },
            }
    except (OSError, UnicodeError) as error:
        raise ModelInventoryError("Unsafe, missing, or changed model-store object") from error
