from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from agent_dev_kit.domain.manifest import (
    CANONICAL_ONLY_KEYS,
    ManifestContract,
    canonical_manifest,
    load_canonical_manifest,
    load_contract,
)

__all__ = [
    "CANONICAL_ONLY_KEYS",
    "ManifestContract",
    "canonical_manifest",
    "load_canonical_manifest",
    "load_contract",
    "main",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify manifest.json SSOT and manifest.yaml compatibility projection"
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = load_contract(Path(args.root))
        contract.verify()
        result = {
            "schema": "adk-manifest-contract/v2",
            "status": "pass",
            "version": contract.version,
            "canonical": "manifest.json",
            "compatibility_projection": "manifest.yaml",
            "canonical_only_fields": list(contract.compatibility_omissions),
        }
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        result = {"schema": "adk-manifest-contract/v2", "status": "fail", "error": str(exc)}
        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"[PASS] manifest.json SSOT matches manifest.yaml compatibility projection ({contract.version})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
