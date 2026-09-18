from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(root: Path) -> dict[str, Any]:
    path = root.resolve() / "manifest.json"
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("manifest.json root must be an object")
    return value


def _emit_scalar(value: Any) -> None:
    if isinstance(value, bool):
        print("true" if value else "false")
    elif isinstance(value, (str, int, float)) and not isinstance(value, bool):
        print(value)


def _emit_list(value: Any) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, bool):
            print("true" if item else "false")
        elif isinstance(item, (str, int, float)) and not isinstance(item, bool):
            print(item)


def _mapping_entry(data: dict[str, Any], section: str, name: str) -> dict[str, Any] | None:
    container = data.get(section)
    if not isinstance(container, dict):
        return None
    value = container.get(name)
    return value if isinstance(value, dict) else None


def _named_item(data: dict[str, Any], section: str, name: str) -> dict[str, Any] | None:
    container = data.get(section)
    if not isinstance(container, list):
        return None
    for raw in container:
        if isinstance(raw, dict) and raw.get("name") == name:
            return raw
    return None


def _routing_intents(data: dict[str, Any]) -> list[dict[str, Any]]:
    routing = data.get("routing")
    if not isinstance(routing, dict):
        return []
    raw_intents = routing.get("intents")
    if not isinstance(raw_intents, list):
        return []
    return [item for item in raw_intents if isinstance(item, dict)]


def _routing_intent(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in _routing_intents(data):
        if item.get("intent") == name:
            return item
    return None


def run(data: dict[str, Any], command: str, args: list[str]) -> None:
    if command == "top-value" and len(args) == 1:
        _emit_scalar(data.get(args[0]))
        return
    if command == "section-entry-names" and len(args) == 1:
        value = data.get(args[0])
        if isinstance(value, dict):
            for name in value:
                print(name)
        return
    if command == "section-entry-value" and len(args) == 3:
        entry = _mapping_entry(data, args[0], args[1])
        if entry is not None:
            _emit_scalar(entry.get(args[2]))
        return
    if command == "section-entry-list" and len(args) == 3:
        entry = _mapping_entry(data, args[0], args[1])
        if entry is not None:
            _emit_list(entry.get(args[2]))
        return
    if command == "profile-names" and not args:
        profiles = data.get("profiles")
        if isinstance(profiles, dict):
            for name in profiles:
                print(name)
        return
    if command == "profile-value" and len(args) == 2:
        entry = _mapping_entry(data, "profiles", args[0])
        if entry is not None:
            _emit_scalar(entry.get(args[1]))
        return
    if command == "profile-list" and len(args) == 2:
        entry = _mapping_entry(data, "profiles", args[0])
        if entry is not None:
            _emit_list(entry.get(args[1]))
        return
    if command == "manifest-names" and len(args) == 1:
        value = data.get(args[0])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("name"), str):
                    print(item["name"])
        return
    if command == "manifest-paths" and len(args) == 1:
        value = data.get(args[0])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("path"), str):
                    print(f"{item['name']} {item['path']}")
        return
    if command == "manifest-item-value" and len(args) == 3:
        entry = _named_item(data, args[0], args[1])
        if entry is not None:
            _emit_scalar(entry.get(args[2]))
        return
    if command == "manifest-item-list" and len(args) == 3:
        entry = _named_item(data, args[0], args[1])
        if entry is not None:
            _emit_list(entry.get(args[2]))
        return
    if command == "routing-intent-names" and not args:
        for item in _routing_intents(data):
            value = item.get("intent")
            if isinstance(value, str):
                print(value)
        return
    if command == "routing-intent-value" and len(args) == 2:
        entry = _routing_intent(data, args[0])
        if entry is not None:
            _emit_scalar(entry.get(args[1]))
        return
    if command == "routing-intent-list" and len(args) == 2:
        entry = _routing_intent(data, args[0])
        if entry is not None:
            _emit_list(entry.get(args[1]))
        return
    if command == "routing-intents" and not args:
        for item in _routing_intents(data):
            intent_zh = item.get("intent_zh")
            primary = item.get("primary_skill")
            if isinstance(intent_zh, str) and isinstance(primary, str):
                print(f"{intent_zh}\t{primary}")
        return
    if command == "routing-supporting-skills" and len(args) == 1:
        for item in _routing_intents(data):
            if item.get("primary_skill") == args[0]:
                _emit_list(item.get("supporting_skills"))
                return
        return
    raise ValueError(f"invalid manifest query: {command} {' '.join(args)}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query canonical manifest.json for repository governance launchers")
    parser.add_argument("--root", default=".")
    parser.add_argument("command")
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args(argv)
    try:
        run(_load(Path(ns.root)), ns.command, ns.args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
