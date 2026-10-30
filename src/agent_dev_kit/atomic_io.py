"""Bounded JSON encoding and caller-owned atomic document publication."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, List, Mapping, Optional, Sequence, Tuple

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


def validate_document_outputs(outputs: Sequence[Path], inputs: Sequence[Path] = ()) -> List[Path]:
    """Preflight a caller-owned output set without creating files or directories."""
    paths = [Path(os.path.abspath(os.fspath(path))) for path in outputs]
    sources = [path.expanduser().resolve() for path in inputs]
    for index, path in enumerate(paths):
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ManifestError("document_output_must_be_regular_file: {}".format(path))
        for parent in path.parents:
            if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
                raise ManifestError("document_output_parent_must_be_regular_directory: {}".format(parent))
        for other in paths[:index]:
            if (path == other or path in other.parents or other in path.parents
                    or (path.exists() and other.exists() and path.samefile(other))):
                raise ManifestError("document_output_alias: {} and {}".format(path, other))
        for source in sources:
            if path == source or (path.exists() and source.exists() and path.samefile(source)):
                raise ManifestError("document_input_output_alias: {} and {}".format(path, source))
    return paths


def _file_identity(path: Path) -> Optional[Tuple[int, int]]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    return info.st_dev, info.st_ino


def write_texts_atomic(documents: Sequence[Tuple[Path, str]]) -> None:
    """Stage the full set, then publish with compensating recovery on failure.

    Each rename is atomic; the set is not crash-atomic. Parents and concurrent
    writers remain caller-owned, as for write_text_atomic. Recovery failures
    retain original files and identify the reserved recovery paths. Cancellation
    during publication or recovery retains staged files and original backups.
    """
    paths = validate_document_outputs([path for path, _ in documents])
    identities = [_file_identity(path) for path in paths]
    staged: List[Path] = []
    backups: List[Optional[Path]] = []
    moved: List[int] = []
    published: List[int] = []
    staged_identities: List[Optional[Tuple[int, int]]] = []
    preserve = False
    try:
        for path, (_, text), identity in zip(paths, documents, identities):
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".stage", dir=str(path.parent))
            os.close(descriptor)
            temporary = Path(name)
            staged.append(temporary)
            write_text_atomic(text, temporary)
            staged_identities.append(_file_identity(temporary))
            backup = None
            if identity is not None:
                descriptor, name = tempfile.mkstemp(prefix="." + path.name + ".", suffix=".previous", dir=str(path.parent))
                os.close(descriptor)
                backup = Path(name)
            backups.append(backup)
        validate_document_outputs(paths)
        if [_file_identity(path) for path in paths] != identities:
            raise ManifestError("document output identity changed during staging")
        # Cancellation can occur after a rename but before its bookkeeping.
        # Cleanup is safe only after the whole set commits or recovery finishes.
        preserve = True
        try:
            for index, path in enumerate(paths):
                validate_document_outputs([path])
                if _file_identity(path) != identities[index]:
                    raise ManifestError("document output identity changed before publication: {}".format(path))
                backup = backups[index]
                if backup is not None:
                    os.replace(str(path), str(backup))
                    moved.append(index)
                os.replace(str(staged[index]), str(path))
                published.append(index)
        except Exception as publication_error:
            recovery_errors = []
            for index in reversed(sorted(set(moved + published))):
                path = paths[index]
                try:
                    current = _file_identity(path)
                    if current is not None and current != staged_identities[index]:
                        raise ManifestError("document changed before recovery: {}".format(path))
                    backup = backups[index]
                    if index in moved and backup is not None:
                        os.replace(str(backup), str(path))
                    elif current is not None:
                        path.unlink()
                except Exception as recovery_error:
                    recovery_errors.append(str(recovery_error))
            if recovery_errors:
                recovery_paths = []
                for index in moved:
                    backup = backups[index]
                    if backup is not None and backup.exists():
                        recovery_paths.append(str(backup))
                raise ManifestError(
                    "document publication and recovery failed; recover original documents from {}: {}"
                    .format(", ".join(recovery_paths), "; ".join(recovery_errors))
                ) from publication_error
            preserve = False
            raise
        preserve = False
    finally:
        if not preserve:
            for path in staged + [path for path in backups if path is not None]:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
