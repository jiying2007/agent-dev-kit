#!/usr/bin/env python3
"""One-time v2 YAML to v3 JSON migration utility."""

import argparse
import json
import os
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        import yaml
    except ImportError as exc:
        raise SystemExit("PyYAML is required only for v2 migration") from exc

    source = Path(args.source)
    output = Path(args.output)
    if not source.is_file():
        raise SystemExit("source manifest does not exist: {}".format(source))
    if source.resolve() == output.resolve():
        raise SystemExit("source and output must be different files")
    if output.exists() and not args.force:
        raise SystemExit("output already exists; use --force to replace it")
    data = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("manifest root must be a mapping")
    data["schema_version"] = "3.0.0"
    data["version"] = "3.0.0"
    data["product"] = {
        "kind": "agent-asset-platform",
        "runtime_boundary": "no-llm-runner",
        "evidence_model": "source-test-runtime-field",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, str(output))
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
