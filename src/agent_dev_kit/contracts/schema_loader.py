from __future__ import annotations

import hashlib
from importlib import resources
from pathlib import Path
from typing import Any

_PACKAGE = "agent_dev_kit.schema_resources"


def packaged_schema_bytes(name: str) -> bytes:
    if not name.endswith(".schema.json") or "/" in name or "\\" in name:
        raise ValueError(f"invalid packaged schema name: {name}")
    return resources.files(_PACKAGE).joinpath(name).read_bytes()


def canonical_schema_bytes(root: Path, name: str) -> bytes:
    path = (root.resolve() / "schemas" / name).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"schema escapes repository root: {name}") from exc
    if not path.is_file():
        raise ValueError(f"canonical schema missing: schemas/{name}")
    return path.read_bytes()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_packaged_schema_sync(root: Path) -> dict[str, Any]:
    root = root.resolve()
    package_root = resources.files(_PACKAGE)
    names = sorted(item.name for item in package_root.iterdir() if item.name.endswith(".schema.json"))
    failures: list[str] = []
    schemas: list[dict[str, str]] = []
    for name in names:
        try:
            canonical = canonical_schema_bytes(root, name)
            packaged = packaged_schema_bytes(name)
        except (OSError, ValueError) as exc:
            failures.append(str(exc))
            continue
        canonical_sha = sha256_bytes(canonical)
        packaged_sha = sha256_bytes(packaged)
        schemas.append({"name": name, "canonical_sha256": canonical_sha, "packaged_sha256": packaged_sha})
        if canonical_sha != packaged_sha:
            failures.append(f"packaged schema drift: {name}")
    if not names:
        failures.append("no packaged schemas found")
    return {
        "schema": "adk-schema-resource-sync/v1",
        "status": "pass" if not failures else "fail",
        "count": len(names),
        "schemas": schemas,
        "failures": failures,
    }
