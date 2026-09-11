from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path
from typing import Any

_PACKAGE = "agent_dev_kit.schema_resources"
_PACKAGE_RELATIVE = Path("src") / "agent_dev_kit" / "schema_resources"


def packaged_schema_bytes(name: str) -> bytes:
    if not name.endswith(".schema.json") or "/" in name or "\\" in name:
        raise ValueError(f"invalid packaged schema name: {name}")
    return resources.files(_PACKAGE).joinpath(name).read_bytes()


def canonical_schema_bytes(root: Path, name: str) -> bytes:
    root = root.resolve()
    path = (root / "schemas" / name).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"schema escapes repository root: {name}") from exc
    if not path.is_file():
        raise ValueError(f"canonical schema missing: schemas/{name}")
    return path.read_bytes()


def source_schema_resource_dir(root: Path) -> Path:
    root = root.resolve()
    package_root = (root / _PACKAGE_RELATIVE).resolve()
    try:
        package_root.relative_to(root)
    except ValueError as exc:
        raise ValueError("schema resource directory escapes repository root") from exc
    if not package_root.is_dir():
        raise ValueError(f"schema resource directory missing: {_PACKAGE_RELATIVE.as_posix()}")
    return package_root


def packaged_schema_names(root: Path) -> list[str]:
    package_root = source_schema_resource_dir(root)
    return sorted(path.name for path in package_root.glob("*.schema.json") if path.is_file())


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sync_packaged_schemas(root: Path, *, write: bool = False) -> dict[str, Any]:
    """Check or regenerate the explicit packaged-schema mirror set.

    The files already present under ``schema_resources`` are the explicit wheel
    surface allowlist. Their bytes are always sourced from canonical ``schemas/``
    files; this function never auto-adds every repository schema to the wheel.
    """

    root = root.resolve()
    package_root = source_schema_resource_dir(root)
    names = packaged_schema_names(root)
    failures: list[str] = []
    schemas: list[dict[str, str]] = []
    changed: list[str] = []

    for name in names:
        try:
            canonical = canonical_schema_bytes(root, name)
        except (OSError, ValueError) as exc:
            failures.append(str(exc))
            continue
        target = package_root / name
        packaged = target.read_bytes()
        canonical_sha = sha256_bytes(canonical)
        packaged_sha = sha256_bytes(packaged)
        if canonical_sha != packaged_sha and write:
            target.write_bytes(canonical)
            packaged = canonical
            packaged_sha = canonical_sha
            changed.append(name)
        schemas.append({"name": name, "canonical_sha256": canonical_sha, "packaged_sha256": packaged_sha})
        if canonical_sha != packaged_sha:
            failures.append(f"packaged schema drift: {name}")

    if not names:
        failures.append("no packaged schemas found")
    return {
        "schema": "adk-schema-resource-sync/v2",
        "status": "pass" if not failures else "fail",
        "mode": "write" if write else "check",
        "count": len(names),
        "changed": changed,
        "schemas": schemas,
        "failures": failures,
    }


def validate_packaged_schema_sync(root: Path) -> dict[str, Any]:
    return sync_packaged_schemas(root, write=False)
