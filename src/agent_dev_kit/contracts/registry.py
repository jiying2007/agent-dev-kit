from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REGISTRY_SCHEMA = "adk-contract-registry/v1"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract_registry(root: Path) -> dict[str, Any]:
    root = root.resolve()
    registry_path = root / "manifests" / "contract_registry.json"
    schema_path = root / "schemas" / "contract-registry-v1.schema.json"
    failures: list[str] = []
    try:
        registry = _load_json(registry_path)
        schema = _load_json(schema_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": REGISTRY_SCHEMA, "status": "fail", "failures": [str(exc)]}

    for error in sorted(Draft202012Validator(schema).iter_errors(registry), key=lambda item: list(item.path)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        failures.append(f"schema {location}: {error.message}")

    seen: set[tuple[str, str]] = set()
    entries = registry.get("contracts", []) if isinstance(registry, dict) else []
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            continue
        identity = (str(entry.get("id") or ""), str(entry.get("version") or ""))
        if identity in seen:
            failures.append(f"duplicate contract identity: {identity[0]}@{identity[1]}")
        seen.add(identity)
        for field in ("surface_path", "schema_path"):
            value = entry.get(field)
            if value is None:
                continue
            if not isinstance(value, str) or not value:
                failures.append(f"{identity[0]}@{identity[1]} invalid {field}")
                continue
            path = (root / value).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                failures.append(f"{identity[0]}@{identity[1]} {field} escapes repository: {value}")
                continue
            if not path.is_file():
                failures.append(f"{identity[0]}@{identity[1]} missing {field}: {value}")
        if entry.get("schema_path") is None and entry.get("surface_path") is None:
            failures.append(f"{identity[0]}@{identity[1]} requires schema_path or surface_path")

    return {
        "schema": REGISTRY_SCHEMA,
        "status": "pass" if not failures else "fail",
        "contract_count": len(entries) if isinstance(entries, list) else 0,
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the ADK versioned contract registry")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_contract_registry(Path(args.root))
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif result["status"] == "pass":
        print(f"[PASS] contract registry entries={result['contract_count']}")
    else:
        for failure in result["failures"]:
            print(f"[FAIL] {failure}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
