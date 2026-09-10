from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CANONICAL_ONLY_KEYS = frozenset({"schema_version", "product"})


def _first_difference(left: Any, right: Any, path: str = "$") -> str | None:
    if type(left) is not type(right):
        return f"{path}: type {type(left).__name__} != {type(right).__name__}"
    if isinstance(left, dict):
        left_keys = set(left)
        right_keys = set(right)
        if left_keys != right_keys:
            missing = sorted(left_keys - right_keys)
            extra = sorted(right_keys - left_keys)
            return f"{path}: key drift missing_in_yaml={missing} extra_in_yaml={extra}"
        for key in left:
            diff = _first_difference(left[key], right[key], f"{path}.{key}")
            if diff:
                return diff
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: length {len(left)} != {len(right)}"
        for index, (left_item, right_item) in enumerate(zip(left, right, strict=True)):
            diff = _first_difference(left_item, right_item, f"{path}[{index}]")
            if diff:
                return diff
        return None
    if left != right:
        return f"{path}: {left!r} != {right!r}"
    return None


def _compatibility_projection(canonical: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in canonical.items() if key not in CANONICAL_ONLY_KEYS}


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

    @property
    def compatibility_omissions(self) -> tuple[str, ...]:
        return tuple(sorted(CANONICAL_ONLY_KEYS))

    def verify(self) -> None:
        expected = _compatibility_projection(self.canonical)
        difference = _first_difference(expected, self.compatibility)
        if difference:
            raise ValueError(f"manifest.yaml compatibility projection differs semantically: {difference}")
        forbidden = sorted(set(self.compatibility) & CANONICAL_ONLY_KEYS)
        if forbidden:
            raise ValueError(
                "manifest.yaml unexpectedly owns canonical-only metadata: " + ", ".join(forbidden)
            )


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
