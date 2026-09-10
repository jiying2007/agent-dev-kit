from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    canonical: dict[str, Any]

    @property
    def version(self) -> str:
        value = self.canonical.get("version")
        if not isinstance(value, str) or not value:
            raise ValueError("manifest.json version must be a non-empty string")
        return value

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_path.read_bytes()).hexdigest()

    def verify(self) -> None:
        if self.canonical_path.name != "manifest.json" or not self.canonical_path.is_file():
            raise ValueError("manifest.json must be the canonical manifest")
        if (self.root / "manifest.yaml").exists():
            raise ValueError("legacy manifest.yaml projection must not exist")
        schema_version = self.canonical.get("schema_version")
        if schema_version is None:
            raise ValueError("manifest.json schema_version is required")
        product = self.canonical.get("product")
        if not isinstance(product, dict):
            raise ValueError("manifest.json product must be an object")
        self.version


def load_contract(root: Path) -> ManifestContract:
    root = root.resolve()
    contract = ManifestContract(
        root=root,
        canonical_path=root / "manifest.json",
        canonical=load_canonical_manifest(root),
    )
    return contract


def canonical_manifest(root: Path) -> dict[str, Any]:
    """Return the only structured manifest after validating the SSOT boundary."""
    contract = load_contract(root)
    contract.verify()
    return contract.canonical
