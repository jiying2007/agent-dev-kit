from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .model import ManifestError

_SEMVER_PATTERN = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


def _parse_version(value: str) -> tuple[tuple[int, int, int], tuple[str, ...] | None]:
    match = _SEMVER_PATTERN.fullmatch(value)
    if match is None:
        raise ManifestError(f"invalid semantic version: {value}")
    core = tuple(int(part) for part in match.groups()[:3])
    prerelease = match.group(4)
    return core, tuple(prerelease.split(".")) if prerelease is not None else None


def compare_versions(left: str, right: str) -> int:
    """Return -1, 0, or 1 using SemVer precedence; build metadata is ignored."""
    left_core, left_pre = _parse_version(left)
    right_core, right_pre = _parse_version(right)
    if left_core != right_core:
        return -1 if left_core < right_core else 1
    if left_pre is None or right_pre is None:
        if left_pre is None and right_pre is None:
            return 0
        return 1 if left_pre is None else -1

    for left_part, right_part in zip(left_pre, right_pre, strict=False):
        if left_part == right_part:
            continue
        left_numeric = left_part.isdigit()
        right_numeric = right_part.isdigit()
        if left_numeric and right_numeric:
            return -1 if int(left_part) < int(right_part) else 1
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return -1 if left_part < right_part else 1

    if len(left_pre) == len(right_pre):
        return 0
    return -1 if len(left_pre) < len(right_pre) else 1


def version_is_newer(previous: str, candidate: str) -> bool:
    return compare_versions(previous, candidate) < 0


def _manifest_version(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"unable to read version manifest: {path}") from exc
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version:
        raise ManifestError(f"manifest version is missing or invalid: {path}")
    _parse_version(version)
    return version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canonical ADK semantic-version ordering")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compare = subparsers.add_parser("compare", help="Compare two semantic versions")
    compare.add_argument("--previous", required=True)
    compare.add_argument("--candidate", required=True)

    require = subparsers.add_parser(
        "require-advance",
        help="Require candidate manifest version to be newer than previous manifest version",
    )
    require.add_argument("--previous-manifest", required=True)
    require.add_argument("--candidate-manifest", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            relation = compare_versions(args.previous, args.candidate)
            operator = "<" if relation < 0 else ">" if relation > 0 else "=="
            print(f"{args.previous} {operator} {args.candidate}")
            return 0

        previous = _manifest_version(Path(args.previous_manifest))
        candidate = _manifest_version(Path(args.candidate_manifest))
        if not version_is_newer(previous, candidate):
            print(
                f"[FAIL] source version must advance before merge: {previous} -> {candidate}",
                file=sys.stderr,
            )
            return 1
        print(f"version advance verified: {previous} -> {candidate}")
        return 0
    except ManifestError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
