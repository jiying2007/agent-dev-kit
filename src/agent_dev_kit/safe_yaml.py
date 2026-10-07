"""Safe YAML parsing with the optional LibYAML implementation."""

from __future__ import annotations

from typing import Any

import yaml


def safe_load(text: str) -> Any:
    """Preserve SafeLoader constructors with or without the C extension."""
    if hasattr(yaml, "CSafeLoader"):
        return yaml.load(text, Loader=yaml.CSafeLoader)
    return yaml.safe_load(text)
