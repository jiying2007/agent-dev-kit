"""Per-audit state and bounded file ports; no process-global mutable state."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .strict_json import StrictJSONError, read as read_json


class AuditContext:
    def __init__(self, root: Path, summary_json: bool) -> None:
        self.root = root
        self.failures: list[str] = []
        self.bindings: dict[str, Any] = {
            "root": root, "summary_json": summary_json, "failures": self.failures,
            "fail": self.fail, "load_json": self.load_json,
            "require_keys": self.require_keys, "require_file_contains": self.require_file_contains,
        }

    def fail(self, message: str) -> None:
        self.failures.append(message)

    def load_json(self, relative: str) -> Any:
        path = self.root / relative
        if not path.is_file():
            self.fail("missing file: " + relative)
            return {}
        try:
            return read_json(path)
        except StrictJSONError as exc:
            self.fail("invalid json: {}: {}".format(relative, exc))
            return {}

    def require_keys(self, obj: Any, keys: list[str], label: str) -> None:
        for key in keys:
            if key not in obj or obj[key] in ("", None, []):
                self.fail("{} missing key: {}".format(label, key))

    def require_file_contains(self, relative: str, markers: list[str], label: str) -> None:
        path = self.root / relative
        if not path.is_file():
            self.fail("missing file: " + relative)
            return
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                self.fail("{} missing marker: {}".format(label, marker))
