"""Read-only upstream Git source drift detector for reviewed official examples.

A fresh HEAD is observational data, never permission to change a Skill, source
allowlist, installed asset, native runtime, or product release qualification.
Network calls run only from the explicitly invoked separate scheduled workflow.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

SCHEMA = "adk-official-upstream-git-pins/v1"
REPORT_SCHEMA = "adk-official-upstream-drift-report/v1"
TRUSTED = {
    "openai-plugins-examples": "openai/plugins",
    "openai-skills-legacy": "openai/skills",
}
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
MAX_CONFIG_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 128 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow changing API redirects to an unreviewed host."""

    def redirect_request(self, request: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        raise ValueError("upstream API redirected: explicit source review required")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key in upstream evidence")
        result[key] = value
    return result


def _strict_json(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8", errors="strict"), object_pairs_hook=_no_duplicates,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def load_config(path: Path) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_CONFIG_BYTES:
        raise ValueError("upstream pins must be a bounded regular file")
    config = _strict_json(path.read_bytes())
    if not isinstance(config, dict) or config.get("schema") != SCHEMA or config.get("status") != "watch":
        raise ValueError("upstream pin schema/status mismatch")
    sources = config.get("sources")
    if not isinstance(sources, list) or len(sources) != len(TRUSTED):
        raise ValueError("upstream pins must enumerate exactly the reviewed sources")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("upstream source must be an object")
        source_id, repository = source.get("id"), source.get("repository")
        if not isinstance(source_id, str) or source_id in seen or TRUSTED.get(source_id) != repository:
            raise ValueError("unregistered or duplicate upstream source")
        seen.add(source_id)
        if source.get("branch") != "main" or not isinstance(source.get("reviewed_sha"), str):
            raise ValueError("upstream ref or reviewed SHA is invalid")
        if COMMIT_RE.fullmatch(source["reviewed_sha"]) is None:
            raise ValueError("upstream reviewed SHA must be an exact 40-hex Git commit")
    if seen != set(TRUSTED):
        raise ValueError("upstream source ownership incomplete")
    try:
        reviewed = dt.date.fromisoformat(config["last_reviewed_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("upstream review date is invalid") from exc
    if reviewed > dt.datetime.now(dt.UTC).date():
        raise ValueError("upstream review date must not be in the future")
    return config


def fetch_head(repository: str) -> str:
    """Use only the hardcoded public GitHub API origin, without redirects/auth."""
    if repository not in TRUSTED.values():
        raise ValueError("unreviewed upstream repository")
    url = f"https://api.github.com/repos/{repository}/commits/main"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "agent-dev-kit-official-drift/1", "Accept": "application/vnd.github+json"},
        method="GET",
    )
    opener = urllib.request.build_opener(_NoRedirect())
    with opener.open(request, timeout=10) as response:
        if response.status != 200:
            raise ValueError("upstream API did not return HTTP 200")
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("upstream API response exceeds byte budget")
    value = _strict_json(raw)
    sha = value.get("sha") if isinstance(value, dict) else None
    if not isinstance(sha, str) or COMMIT_RE.fullmatch(sha) is None:
        raise ValueError("upstream API returned an invalid commit identity")
    return sha


def check_sources(
    config: Mapping[str, Any], fetch: Callable[[str], str] = fetch_head,
) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    for source in sorted(config["sources"], key=lambda row: row["id"]):
        repository = source["repository"]
        expected = source["reviewed_sha"]
        row = {"id": source["id"], "repository": repository, "reviewed_sha": expected}
        try:
            observed = fetch(repository)
            if not isinstance(observed, str) or COMMIT_RE.fullmatch(observed) is None:
                raise ValueError("upstream returned a noncanonical SHA")
            row["observed_sha"] = observed
            row["state"] = "unchanged" if observed == expected else "drift"
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
            row["state"] = "unavailable"
            row["reason"] = type(exc).__name__
        rows.append(row)
    status = "fail" if any(row["state"] == "unavailable" for row in rows) else (
        "drift" if any(row["state"] == "drift" for row in rows) else "pass"
    )
    return {
        "schema": REPORT_SCHEMA,
        "status": status,
        "authority": "read-only-public-github-api",
        "claims": "HEAD-drift-only-not-doc-content-or-native-certification",
        "sources": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observe reviewed official upstream Git HEAD drift")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    try:
        config = load_config(Path(args.root) / "manifests/official_upstream_git_pins.json")
        report = check_sources(config)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        report = {"schema": REPORT_SCHEMA, "status": "fail", "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":") if args.summary_json else None,
                     indent=None if args.summary_json else 2))
    return {"pass": 0, "drift": 2}.get(report["status"], 1)


if __name__ == "__main__":
    raise SystemExit(main())
