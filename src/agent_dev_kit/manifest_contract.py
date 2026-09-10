from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from agent_dev_kit.domain.manifest import (
    ManifestContract,
    canonical_manifest,
    load_canonical_manifest,
    load_contract,
)

__all__ = [
    "ManifestContract",
    "canonical_manifest",
    "load_canonical_manifest",
    "load_contract",
    "main",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify manifest.json is the single structured Manifest SSOT")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        contract = load_contract(Path(args.root))
        contract.verify()
        if not re.fullmatch(r"[0-9a-f]{64}", contract.sha256):
            raise ValueError("manifest.json SHA256 identity is invalid")
        result = {
            "schema": "adk-manifest-contract/v3",
            "status": "pass",
            "version": contract.version,
            "canonical": "manifest.json",
            "canonical_sha256": contract.sha256,
            "legacy_projection_absent": True,
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"schema": "adk-manifest-contract/v3", "status": "fail", "error": str(exc)}
        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"[PASS] manifest.json is the sole Manifest SSOT ({contract.version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
