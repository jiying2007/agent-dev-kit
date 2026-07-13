#!/usr/bin/env python3
"""Check the v2 YAML compatibility mirror against the v3 JSON SSOT."""

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="manifest.json")
    parser.add_argument("--yaml", default="manifest.yaml")
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("[FAIL] PyYAML is required while manifest.yaml compatibility exists", file=sys.stderr)
        return 1

    json_path = Path(args.json)
    yaml_path = Path(args.yaml)
    canonical = json.loads(json_path.read_text(encoding="utf-8"))
    mirror = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(canonical, dict) or not isinstance(mirror, dict):
        print("[FAIL] manifest roots must be objects", file=sys.stderr)
        return 1

    mirror["schema_version"] = canonical.get("schema_version")
    mirror["product"] = canonical.get("product")
    if mirror != canonical:
        canonical_keys = set(canonical)
        mirror_keys = set(mirror)
        differing = sorted(
            key for key in canonical_keys.intersection(mirror_keys) if canonical.get(key) != mirror.get(key)
        )
        print(
            "[FAIL] manifest.yaml compatibility mirror drifted: missing={} extra={} differing={}".format(
                sorted(canonical_keys.difference(mirror_keys)),
                sorted(mirror_keys.difference(canonical_keys)),
                differing,
            ),
            file=sys.stderr,
        )
        return 1

    print("[PASS] manifest.json and manifest.yaml are semantically aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
