"""Read actual top-level timing values for the existing budget reporter."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .strict_json import read

_MODES = ("quick", "full", "benchmark")
_MAX_INTEGER = (1 << 63) - 1


def timing_values(manifest_path: Path, timing_path: Path) -> tuple[str, int, int]:
    """Reject ambiguous input rather than truncating or selecting nested values."""
    timing = read(timing_path, regular_only=True)
    manifest = read(manifest_path, regular_only=True)
    if not isinstance(timing, dict) or not isinstance(manifest, dict):
        raise ValueError("timing and budget inputs must be objects")
    if type(timing.get("schema_version")) is not int or timing["schema_version"] != 1:
        raise ValueError("unsupported timing schema")
    mode = timing.get("mode")
    elapsed = timing.get("elapsed_ms")
    if not isinstance(mode, str) or mode not in _MODES:
        raise ValueError("unknown timing mode")
    if type(elapsed) is not int or not 0 <= elapsed <= _MAX_INTEGER:
        raise ValueError("elapsed_ms must be a bounded nonnegative integer")
    budgets = manifest.get("budgets")
    if not isinstance(budgets, list) or not budgets:
        raise ValueError("configured budgets are missing")
    version = ".".join(map(str, sys.version_info[:2]))
    choices: dict[str, int] = {}
    for budget in budgets:
        if not isinstance(budget, dict):
            raise ValueError("configured budget must be an object")
        if budget.get("mode") != mode:
            continue
        scope = budget.get("python", "default")
        maximum = budget.get("max_elapsed_ms")
        if (not isinstance(scope, str) or not scope or scope in choices
                or type(maximum) is not int or not 0 < maximum <= _MAX_INTEGER):
            raise ValueError("configured mode budget is invalid or ambiguous")
        choices[scope] = maximum
    maximum = choices.get(version, choices.get("default"))
    if maximum is None:
        raise ValueError("no budget configured for timing mode and interpreter")
    return mode, elapsed, maximum


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("timing", type=Path)
    args = parser.parse_args(argv)
    try:
        values = timing_values(args.manifest, args.timing)
    except (OSError, ValueError):
        print("[FAIL] invalid timing JSON or configured mode budget", file=sys.stderr)
        return 1
    # Only allowlisted mode and bounded integers reach the shell's read/compare.
    print(*values)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
