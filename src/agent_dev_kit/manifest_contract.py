from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


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
        difference = _first_difference(self.canonical, self.compatibility)
        if difference:
            raise ValueError(f"manifest.yaml compatibility mirror differs semantically: {difference}")


def load_contract(root: Path) -> ManifestContract:
    root = root.resolve()
    canonical_path = root / "manifest.json"
    compatibility_path = root / "manifest.yaml"
    with canonical_path.open(encoding="utf-8") as handle:
        canonical = json.load(handle)
    with compatibility_path.open(encoding="utf-8") as handle:
        compatibility = yaml.safe_load(handle)
    if not isinstance(canonical, dict):
        raise ValueError("manifest.json root must be an object")
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
    contract = load_contract(root)
    contract.verify()
    return contract.canonical


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify manifest.json SSOT and manifest.yaml compatibility mirror")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = load_contract(Path(args.root))
        contract.verify()
        result = {
            "schema": "adk-manifest-contract/v1",
            "status": "pass",
            "version": contract.version,
            "canonical": "manifest.json",
            "compatibility_mirror": "manifest.yaml",
        }
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        result = {"schema": "adk-manifest-contract/v1", "status": "fail", "error": str(exc)}
        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"[PASS] manifest.json SSOT matches manifest.yaml compatibility mirror ({contract.version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
