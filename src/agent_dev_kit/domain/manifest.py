from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CANONICAL_ONLY_KEYS = frozenset({"schema_version", "product"})


def _projection_diff(canonical: Any, projection: Any, path: str = "$") -> str | None:
    if isinstance(projection, dict):
        if not isinstance(canonical, dict):
            return f"{path}: projection mapping does not match canonical {type(canonical).__name__}"
        extra = sorted(set(projection) - set(canonical))
        if extra:
            return f"{path}: projection contains unknown keys {extra}"
        for key, value in projection.items():
            diff = _projection_diff(canonical[key], value, f"{path}.{key}")
            if diff:
                return diff
        missing = sorted(set(canonical) - set(projection))
        allowed = CANONICAL_ONLY_KEYS if path == "$" else frozenset()
        unexpected = [key for key in missing if key not in allowed]
        if unexpected:
            return f"{path}: projection missing canonical keys {unexpected}"
        return None

    if isinstance(projection, list):
        if not isinstance(canonical, list):
            return f"{path}: projection list does not match canonical {type(canonical).__name__}"
        if len(canonical) != len(projection):
            return f"{path}: list length drift canonical={len(canonical)} projection={len(projection)}"
        for index, value in enumerate(projection):
            diff = _projection_diff(canonical[index], value, f"{path}[{index}]")
            if diff:
                return diff
        return None

    if canonical != projection:
        return f"{path}: value drift canonical={canonical!r} projection={projection!r}"
    return None


def load_canonical_manifest(root: Path) -> dict[str, Any]:
    path = root.resolve() / "manifest.json"
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("manifest.json root must be an object")
    return value


@dataclass(frozen=True)
class ManifestContract:
    root: Path
    canonical_path: Path
    compatibility_path: Path
    canonical: dict[str, Any]
    compatibility: dict[str, Any]

    @property
    def version(self) -> str:
        value = self.canonical.get("version")
        if not isinstance(value, str) or not value:
            raise ValueError("manifest.json version must be a non-empty string")
        return value

    def verify(self) -> None:
        diff = _projection_diff(self.canonical, self.compatibility)
        if diff:
            raise ValueError(f"manifest.yaml compatibility projection differs semantically: {diff}")


def load_contract(root: Path) -> ManifestContract:
    root = root.resolve()
    canonical_path = root / "manifest.json"
    compatibility_path = root / "manifest.yaml"
    canonical = load_canonical_manifest(root)
    with compatibility_path.open(encoding="utf-8") as handle:
        compatibility = yaml.safe_load(handle)
    if not isinstance(compatibility, dict):
        raise ValueError("manifest.yaml root must be a mapping")
    return ManifestContract(
        root=root,
        canonical_path=canonical_path,
        compatibility_path=compatibility_path,
        canonical=canonical,
        compatibility=compatibility,
    )


def canonical_manifest(root: Path) -> dict[str, Any]:
    """Return canonical JSON after proving the legacy projection has not drifted."""
    contract = load_contract(root)
    contract.verify()
    return contract.canonical
