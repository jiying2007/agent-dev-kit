#!/usr/bin/env python3
"""Fail-closed cleanup for stale branch heads that exactly match merged PR heads."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "adk-branch-gc-report/v1"


class BranchGCError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    branch: str
    sha: str
    pr_number: int
    merged_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "sha": self.sha,
            "basis": "exact-merged-pr",
            "merged_pr": self.pr_number,
            "merged_at": self.merged_at,
        }


class GitHubClient:
    def __init__(self, repo: str, token: str) -> None:
        if "/" not in repo:
            raise BranchGCError("repository must use owner/name")
        if not token:
            raise BranchGCError("GH_TOKEN is required")
        self.repo = repo
        self.owner = repo.split("/", 1)[0]
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo}"

    def request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
    ) -> Any:
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        req = urllib.request.Request(
            url,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "agent-dev-kit-branch-gc",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise BranchGCError(
                f"GitHub API {method} {path} failed: HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise BranchGCError(f"GitHub API {method} {path} failed: {exc}") from exc

    def list_branches(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        page = 1
        while True:
            batch = self.request(
                "GET",
                "/branches",
                {"per_page": "100", "page": str(page)},
            )
            if not isinstance(batch, list):
                raise BranchGCError("branches response is not a list")
            result.extend(item for item in batch if isinstance(item, dict))
            if len(batch) < 100:
                return result
            page += 1

    def get_branch(self, branch: str) -> dict[str, Any]:
        value = self.request(
            "GET",
            "/branches/" + urllib.parse.quote(branch, safe=""),
        )
        if not isinstance(value, dict):
            raise BranchGCError(f"invalid branch response: {branch}")
        return value

    def pulls(
        self,
        branch: str,
        state: str,
        base: str | None = None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        page = 1
        while True:
            query = {
                "state": state,
                "head": f"{self.owner}:{branch}",
                "per_page": "100",
                "page": str(page),
            }
            if base is not None:
                query["base"] = base
            batch = self.request("GET", "/pulls", query)
            if not isinstance(batch, list):
                raise BranchGCError(f"invalid pull response: {branch}")
            result.extend(item for item in batch if isinstance(item, dict))
            if len(batch) < 100:
                return result
            page += 1

    def pull(self, number: int) -> dict[str, Any]:
        value = self.request("GET", f"/pulls/{number}")
        if not isinstance(value, dict):
            raise BranchGCError(f"invalid pull response: {number}")
        return value

    def delete_branch(self, branch: str) -> None:
        self.request(
            "DELETE",
            "/git/refs/heads/" + urllib.parse.quote(branch, safe="/"),
        )


def branch_sha(branch: dict[str, Any]) -> str:
    commit = branch.get("commit")
    sha = commit.get("sha") if isinstance(commit, dict) else None
    if not isinstance(sha, str) or len(sha) != 40:
        raise BranchGCError("branch SHA is missing or invalid")
    return sha


def open_pr_numbers(client: GitHubClient, branch: str) -> list[int]:
    return sorted(
        pr["number"]
        for pr in client.pulls(branch, "open")
        if isinstance(pr.get("number"), int)
    )


def exact_merged_pr(
    client: GitHubClient,
    branch: str,
    sha: str,
    base: str,
) -> Candidate | None:
    matches: list[Candidate] = []
    for pr in client.pulls(branch, "closed", base):
        head = pr.get("head")
        base_obj = pr.get("base")
        number = pr.get("number")
        merged_at = pr.get("merged_at")
        if (
            not isinstance(head, dict)
            or not isinstance(base_obj, dict)
            or not isinstance(number, int)
            or not isinstance(merged_at, str)
        ):
            continue
        if (
            head.get("ref") == branch
            and head.get("sha") == sha
            and base_obj.get("ref") == base
        ):
            matches.append(Candidate(branch, sha, number, merged_at))
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item.merged_at, item.pr_number), reverse=True)[0]


def exact_pr_identity(
    client: GitHubClient,
    candidate: Candidate,
    base: str,
) -> bool:
    pr = client.pull(candidate.pr_number)
    head = pr.get("head")
    base_obj = pr.get("base")
    return bool(
        isinstance(head, dict)
        and isinstance(base_obj, dict)
        and pr.get("merged_at") == candidate.merged_at
        and head.get("ref") == candidate.branch
        and head.get("sha") == candidate.sha
        and base_obj.get("ref") == base
    )


def evaluate(
    client: GitHubClient,
    base: str,
) -> tuple[str, list[Candidate], list[dict[str, Any]], int]:
    base_branch = client.get_branch(base)
    base_sha = branch_sha(base_branch)
    candidates: list[Candidate] = []
    skipped: list[dict[str, Any]] = []
    scanned = 0

    for branch in sorted(client.list_branches(), key=lambda item: str(item.get("name", ""))):
        name = branch.get("name")
        if not isinstance(name, str) or not name:
            raise BranchGCError("branch name is missing or invalid")
        sha = branch_sha(branch)
        if name in {base, "main", "master"}:
            continue
        scanned += 1

        if branch.get("protected") is True:
            skipped.append({"branch": name, "sha": sha, "reason": "github-protected"})
            continue

        open_numbers = open_pr_numbers(client, name)
        if open_numbers:
            skipped.append(
                {
                    "branch": name,
                    "sha": sha,
                    "reason": "open-pr",
                    "open_prs": open_numbers,
                }
            )
            continue

        candidate = exact_merged_pr(client, name, sha, base)
        if candidate is None:
            skipped.append(
                {"branch": name, "sha": sha, "reason": "no-exact-merged-pr"}
            )
            continue
        candidates.append(candidate)

    return base_sha, candidates, skipped, scanned


def revalidate_and_delete(
    client: GitHubClient,
    candidate: Candidate,
    base: str,
) -> tuple[bool, str | None]:
    try:
        current = client.get_branch(candidate.branch)
        current_sha = branch_sha(current)
    except BranchGCError:
        return False, "branch-unavailable"

    if current.get("protected") is True:
        return False, "github-protected"
    if current_sha != candidate.sha:
        return False, "sha-changed"
    if open_pr_numbers(client, candidate.branch):
        return False, "open-pr"
    if not exact_pr_identity(client, candidate, base):
        return False, "merged-pr-identity-changed"

    client.delete_branch(candidate.branch)
    return True, None


def render_report(
    *,
    repo: str,
    base: str,
    base_sha: str | None,
    mode: str,
    status: str,
    scanned: int,
    candidates: list[Candidate],
    skipped: list[dict[str, Any]],
    deleted: list[dict[str, Any]],
    revalidation_skips: list[dict[str, Any]],
    failure: str | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "status": status,
        "mode": mode,
        "repository": repo,
        "base": base,
        "base_sha": base_sha,
        "scanned_non_base_branches": scanned,
        "candidates": [candidate.as_dict() for candidate in candidates],
        "skipped": skipped,
        "deleted": deleted,
        "revalidation_skips": revalidation_skips,
    }
    if failure is not None:
        report["failure"] = failure
    return report


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete only branch heads that still exactly match merged PR heads."
    )
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--base", default="main")
    parser.add_argument("--mode", choices=("dry-run", "apply"), required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    report_path = Path(args.report)
    candidates: list[Candidate] = []
    skipped: list[dict[str, Any]] = []
    deleted: list[dict[str, Any]] = []
    revalidation_skips: list[dict[str, Any]] = []
    base_sha: str | None = None
    scanned = 0

    try:
        client = GitHubClient(args.repo, os.environ.get("GH_TOKEN", ""))
        base_sha, candidates, skipped, scanned = evaluate(client, args.base)

        if args.mode == "apply":
            for candidate in candidates:
                ok, reason = revalidate_and_delete(client, candidate, args.base)
                if ok:
                    deleted.append(candidate.as_dict())
                else:
                    revalidation_skips.append(
                        {
                            "branch": candidate.branch,
                            "sha": candidate.sha,
                            "reason": reason,
                        }
                    )

        status = "pass" if not revalidation_skips else "fail"
        report = render_report(
            repo=args.repo,
            base=args.base,
            base_sha=base_sha,
            mode=args.mode,
            status=status,
            scanned=scanned,
            candidates=candidates,
            skipped=skipped,
            deleted=deleted,
            revalidation_skips=revalidation_skips,
        )
        write_report(report_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if status == "pass" else 2
    except BranchGCError as exc:
        report = render_report(
            repo=args.repo,
            base=args.base,
            base_sha=base_sha,
            mode=args.mode,
            status="fail",
            scanned=scanned,
            candidates=candidates,
            skipped=skipped,
            deleted=deleted,
            revalidation_skips=revalidation_skips,
            failure=str(exc),
        )
        write_report(report_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
