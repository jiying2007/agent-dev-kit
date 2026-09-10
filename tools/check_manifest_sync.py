#!/usr/bin/env python3
"""Legacy entrypoint that now enforces the single-manifest boundary.

The historical filename is retained temporarily because release.py still invokes
it.  It no longer synchronizes or parses a YAML mirror; it fails if that mirror
reappears.
"""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="manifest.json")
    parser.add_argument("--yaml", default="manifest.yaml")
    args = parser.parse_args()

    json_path = Path(args.json)
    legacy_path = Path(args.yaml)
    if legacy_path.exists():
        print(f"[FAIL] legacy Manifest projection must be removed: {legacy_path}", file=sys.stderr)
        return 1
    try:
        canonical = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] cannot read canonical manifest.json: {exc}", file=sys.stderr)
        return 1
    if not isinstance(canonical, dict):
        print("[FAIL] manifest.json root must be an object", file=sys.stderr)
        return 1
    if not isinstance(canonical.get("version"), str) or not canonical["version"]:
        print("[FAIL] manifest.json version must be a non-empty string", file=sys.stderr)
        return 1
    if "schema_version" not in canonical or not isinstance(canonical.get("product"), dict):
        print("[FAIL] manifest.json canonical metadata is incomplete", file=sys.stderr)
        return 1

    print("[PASS] manifest.json is the sole structured Manifest SSOT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
