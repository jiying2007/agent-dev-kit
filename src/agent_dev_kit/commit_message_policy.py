"""Read-only, deterministic Conventional Commit syntax checker; never mutates Git."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

TYPES = frozenset({"feat", "fix", "docs", "style", "refactor", "perf", "test", "chore", "ci", "revert", "build"})
SUBJECT = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[a-z0-9][a-z0-9.,/_-]*)\))?(?P<breaking>!)?: (?P<summary>\S.*)$")
ISSUE = re.compile(r"(?im)^(?:closes?|fixes?|resolves?)\s+#\d+\s*$")
BREAKING = re.compile(r"(?m)^BREAKING[ -]CHANGE:\s+\S")


def validate_message(message: str, *, max_summary_length: int = 50, require_issue: bool = False) -> dict:
    """Validate machine syntax; language selection belongs to the calling repository."""
    subject = message.splitlines()[0].strip() if message.splitlines() else ""
    match = SUBJECT.fullmatch(subject)
    errors: list[str] = []
    kind = match.group("type") if match else None
    scope = match.group("scope") if match else None
    summary = match.group("summary") if match else None
    if not match:
        errors.append("subject-format")
    else:
        if kind not in TYPES:
            errors.append("type")
        if len(summary) > max_summary_length:
            errors.append("summary-length")
        if summary.endswith(("。", ".")):
            errors.append("summary-punctuation")
    if require_issue and kind == "fix" and not ISSUE.search(message):
        errors.append("issue-required-by-repository-policy")
    return {
        "status": "pass" if not errors else "needs-fix",
        "type": kind,
        "scope": scope,
        "summary": summary,
        "breaking": bool((match and match.group("breaking")) or BREAKING.search(message)),
        "issues": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a commit message without SCM writes")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--message")
    source.add_argument("--file", type=Path)
    parser.add_argument("--require-issue", action="store_true")
    parser.add_argument("--max-summary-length", type=int, default=50)
    args = parser.parse_args(argv)
    if not 1 <= args.max_summary_length <= 500:
        parser.error("max-summary-length must be between 1 and 500")
    if args.file:
        if not args.file.is_file() or args.file.stat().st_size > 65536:
            parser.error("message file must exist and be at most 64 KiB")
        try:
            message = args.file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            parser.error("unable to read message: " + str(exc))
    else:
        message = args.message
    result = validate_message(
        message, max_summary_length=args.max_summary_length, require_issue=args.require_issue
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
