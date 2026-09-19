from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

class VersioningError(ValueError):
    """Version/source-identity validation failed before package dependencies are available."""


_SEMVER_PATTERN = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)


def _parse_version(value: str) -> tuple[tuple[int, int, int], tuple[str, ...] | None]:
    match = _SEMVER_PATTERN.fullmatch(value)
    if match is None:
        raise VersioningError(f"invalid semantic version: {value}")

    core_parts = (match.group(1), match.group(2), match.group(3))
    if any(len(part) > 1 and part.startswith("0") for part in core_parts):
        raise VersioningError(f"invalid semantic version: {value}")
    core = (int(match.group(1)), int(match.group(2)), int(match.group(3)))

    prerelease_raw = match.group(4)
    prerelease: tuple[str, ...] | None = None
    if prerelease_raw is not None:
        prerelease_parts = tuple(prerelease_raw.split("."))
        if any(
            not part or (part.isdigit() and len(part) > 1 and part.startswith("0"))
            for part in prerelease_parts
        ):
            raise VersioningError(f"invalid semantic version: {value}")
        prerelease = prerelease_parts

    build_raw = match.group(5)
    if build_raw is not None and any(not part for part in build_raw.split(".")):
        raise VersioningError(f"invalid semantic version: {value}")

    return core, prerelease


def validate_version(value: str) -> str:
    _parse_version(value)
    return value


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
        raise VersioningError(f"unable to read version manifest: {path}") from exc
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version:
        raise VersioningError(f"manifest version is missing or invalid: {path}")
    _parse_version(version)
    return version


def _replace_once(path: Path, pattern: str, replacement: str, label: str) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise VersioningError(f"missing version projection: {label}") from exc
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise VersioningError(f"unable to update {label}: expected exactly one version field")
    path.write_text(updated, encoding="utf-8")


def version_identity_failures(root: Path) -> list[str]:
    root = root.resolve()
    try:
        version = _manifest_version(root / "manifest.json")
    except VersioningError as exc:
        return [str(exc)]

    checks = {
        "pyproject.toml": (
            root / "pyproject.toml",
            rf'(?m)^version\s*=\s*["\x27]{re.escape(version)}["\x27]\s*$',
        ),
        "src/agent_dev_kit/__init__.py": (
            root / "src" / "agent_dev_kit" / "__init__.py",
            rf'(?m)^__version__\s*=\s*["\x27]{re.escape(version)}["\x27]\s*$',
        ),
        ".version-lock": (
            root / ".version-lock",
            rf"(?m)^version:\s*{re.escape(version)}\s*$",
        ),
        "README.md": (
            root / "README.md",
            rf"(?m)^\x60manifest\.json\x60 当前 source version 为 \x60{re.escape(version)}\x60。",
        ),
        "CONTEXT.md": (
            root / "CONTEXT.md",
            rf"(?m)^> 产品版本：{re.escape(version)}\s*$",
        ),
        "manifests/software_m5_eval_contract.json": (
            root / "manifests" / "software_m5_eval_contract.json",
            rf'(?m)^\s*"campaign_id"\s*:\s*"software-m5-{re.escape(version)}"\s*,\s*$',
        ),
    }
    failures: list[str] = []
    for label, (path, pattern) in checks.items():
        if not path.is_file():
            failures.append(f"missing {label}")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            failures.append(f"unable to read {label}: {exc}")
            continue
        if re.search(pattern, text) is None:
            failures.append(f"version mismatch in {label}")
    return failures


def sync_version_identity(
    root: Path,
    target: str,
    actor: str,
    *,
    locked_at: str | None = None,
) -> tuple[str, str]:
    root = root.resolve()
    _parse_version(target)
    actor = actor.strip()
    if not actor or "\n" in actor or "\r" in actor:
        raise VersioningError("version lock actor is invalid")

    current = _manifest_version(root / "manifest.json")
    _replace_once(
        root / "manifest.json",
        r'^(\s*"version"\s*:\s*")[^"]+("\s*,\s*)$',
        rf"\g<1>{target}\g<2>",
        "manifest.json",
    )
    _replace_once(
        root / "pyproject.toml",
        r'^(version\s*=\s*")[^"]+("\s*)$',
        rf"\g<1>{target}\g<2>",
        "pyproject.toml",
    )
    _replace_once(
        root / "src" / "agent_dev_kit" / "__init__.py",
        r'^(__version__\s*=\s*")[^"]+("\s*)$',
        rf"\g<1>{target}\g<2>",
        "src/agent_dev_kit/__init__.py",
    )
    _replace_once(
        root / "README.md",
        r"^(\x60manifest\.json\x60 当前 source version 为 \x60)[^\x60]+(\x60。.*)$",
        rf"\g<1>{target}\g<2>",
        "README.md",
    )
    _replace_once(
        root / "CONTEXT.md",
        r"^(> 产品版本：).+$",
        rf"\g<1>{target}",
        "CONTEXT.md",
    )
    _replace_once(
        root / "manifests" / "software_m5_eval_contract.json",
        r'^(\s*"campaign_id"\s*:\s*"software-m5-)[^"]+("\s*,\s*)$',
        rf"\g<1>{target}\g<2>",
        "manifests/software_m5_eval_contract.json",
    )

    lock_time = locked_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (root / ".version-lock").write_text(
        f"version: {target}\nlocked_at: {lock_time}\nlocked_by: {actor}\n",
        encoding="utf-8",
    )
    failures = version_identity_failures(root)
    if failures:
        raise VersioningError("version identity synchronization failed: " + "; ".join(failures))
    return current, target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canonical ADK semantic-version and source-identity authority")
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

    verify = subparsers.add_parser("verify-identity", help="Verify all synchronized source-version projections")
    verify.add_argument("--root", default=".")

    sync = subparsers.add_parser("sync-identity", help="Synchronize all source-version projections")
    sync.add_argument("--root", default=".")
    sync.add_argument("--target", required=True)
    sync.add_argument("--actor", required=True)

    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            relation = compare_versions(args.previous, args.candidate)
            operator = "<" if relation < 0 else ">" if relation > 0 else "=="
            print(f"{args.previous} {operator} {args.candidate}")
            return 0

        if args.command == "require-advance":
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

        if args.command == "verify-identity":
            failures = version_identity_failures(Path(args.root))
            if failures:
                for failure in failures:
                    print(f"[FAIL] {failure}", file=sys.stderr)
                return 1
            version = _manifest_version(Path(args.root) / "manifest.json")
            print(f"version identity verified: {version}")
            return 0

        current, target = sync_version_identity(Path(args.root), args.target, args.actor)
        print(f"version synchronized: {current} -> {target}")
        return 0
    except VersioningError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
