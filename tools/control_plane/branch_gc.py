#!/usr/bin/env python3
"""Fail-closed cleanup for merged branch heads and explicitly retired ancestor heads."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "adk-branch-gc-report/v1"
RETIRED_SCHEMA = "adk-branch-gc-retired/v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RETIRED_REGISTRY = ROOT / "manifests/branch_gc_retired.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class BranchGCError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetiredEntry:
    branch: str
    sha: str
    proof: str
    reviewed_against_main: str
    reason: str

    def as_candidate(self) -> "Candidate":
        return Candidate(
            branch=self.branch,
            sha=self.sha,
            basis="explicit-retired-ancestor",
            proof=self.proof,
            reviewed_against_main=self.reviewed_against_main,
            reason=self.reason,
        )


@dataclass(frozen=True)
class Candidate:
    branch: str
    sha: str
    basis: str
    pr_number: int | None = None
    merged_at: str | None = None
    proof: str | None = None
    reviewed_against_main: str | None = None
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "branch": self.branch,
            "sha": self.sha,
            "basis": self.basis,
        }
        if self.basis == "exact-merged-pr":
            result["merged_pr"] = self.pr_number
            result["merged_at"] = self.merged_at
        elif self.basis == "explicit-retired-ancestor":
            result["proof"] = self.proof
            result["reviewed_against_main"] = self.reviewed_against_main
            result["reason"] = self.reason
        return result


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

    def compare(self, base_sha: str, head_sha: str) -> dict[str, Any]:
        value = self.request(
            "GET",
            "/compare/"
            + urllib.parse.quote(base_sha, safe="")
            + "..."
            + urllib.parse.quote(head_sha, safe=""),
        )
        if not isinstance(value, dict):
            raise BranchGCError(f"invalid compare response: {base_sha}...{head_sha}")
        return value

    def delete_branch(self, branch: str) -> None:
        self.request(
            "DELETE",
            "/git/refs/heads/" + urllib.parse.quote(branch, safe="/"),
        )


def valid_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def branch_sha(branch: dict[str, Any]) -> str:
    commit = branch.get("commit")
    sha = commit.get("sha") if isinstance(commit, dict) else None
    if not valid_sha(sha):
        raise BranchGCError("branch SHA is missing or invalid")
    return sha


def load_retired_registry(path: Path) -> dict[str, RetiredEntry]:
    if not path.is_file():
        raise BranchGCError(f"retired registry is missing: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BranchGCError(f"retired registry is unreadable: {path}: {exc}") from exc

    if not isinstance(raw, dict) or raw.get("schema") != RETIRED_SCHEMA:
        raise BranchGCError("retired registry schema is invalid")
    items = raw.get("entries")
    if not isinstance(items, list):
        raise BranchGCError("retired registry entries must be a list")

    result: dict[str, RetiredEntry] = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise BranchGCError(f"retired registry entry {index} is not an object")
        branch = item.get("branch")
        sha = item.get("sha")
        proof = item.get("proof")
        reviewed = item.get("reviewed_against_main")
        reason = item.get("reason")
        disposition = item.get("disposition")
        if not isinstance(branch, str) or not branch or branch in {"main", "master"}:
            raise BranchGCError(f"retired registry entry {index} has invalid branch")
        if not valid_sha(sha):
            raise BranchGCError(f"retired registry entry {index} has invalid sha")
        if proof != "ancestor-of-main":
            raise BranchGCError(f"retired registry entry {index} has unsupported proof")
        if not valid_sha(reviewed):
            raise BranchGCError(
                f"retired registry entry {index} has invalid reviewed_against_main"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise BranchGCError(f"retired registry entry {index} has invalid reason")
        if disposition != "delete":
            raise BranchGCError(f"retired registry entry {index} must use disposition=delete")
        if branch in result:
            raise BranchGCError(f"retired registry has duplicate branch: {branch}")
        result[branch] = RetiredEntry(
            branch=branch,
            sha=sha,
            proof=proof,
            reviewed_against_main=reviewed,
            reason=reason.strip(),
        )
    return result


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
            matches.append(
                Candidate(
                    branch=branch,
                    sha=sha,
                    basis="exact-merged-pr",
                    pr_number=number,
                    merged_at=merged_at,
                )
            )
    if not matches:
        return None
    return sorted(
        matches,
        key=lambda item: (item.merged_at or "", item.pr_number or 0),
        reverse=True,
    )[0]


def exact_pr_identity(
    client: GitHubClient,
    candidate: Candidate,
    base: str,
) -> bool:
    if candidate.pr_number is None or candidate.merged_at is None:
        return False
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


def commit_is_ancestor(client: GitHubClient, ancestor: str, descendant: str) -> bool:
    if ancestor == descendant:
        return True
    comparison = client.compare(ancestor, descendant)
    merge_base = comparison.get("merge_base_commit")
    status = comparison.get("status")
    return bool(
        isinstance(merge_base, dict)
        and merge_base.get("sha") == ancestor
        and status in {"ahead", "identical"}
    )


def ancestor_retirement_valid(
    client: GitHubClient,
    entry: RetiredEntry,
    base_sha: str,
) -> bool:
    return bool(
        commit_is_ancestor(client, entry.sha, entry.reviewed_against_main)
        and commit_is_ancestor(client, entry.reviewed_against_main, base_sha)
    )


def evaluate(
    client: GitHubClient,
    base: str,
    retired: dict[str, RetiredEntry],
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
        if candidate is not None:
            candidates.append(candidate)
            continue

        retired_entry = retired.get(name)
        if retired_entry is None:
            skipped.append(
                {"branch": name, "sha": sha, "reason": "no-exact-merged-pr"}
            )
            continue
        if sha != retired_entry.sha:
            skipped.append(
                {
                    "branch": name,
                    "sha": sha,
                    "reason": "retired-sha-mismatch",
                    "expected_sha": retired_entry.sha,
                }
            )
            continue
        if not ancestor_retirement_valid(client, retired_entry, base_sha):
            skipped.append(
                {
                    "branch": name,
                    "sha": sha,
                    "reason": "retired-proof-invalid",
                    "proof": retired_entry.proof,
                    "reviewed_against_main": retired_entry.reviewed_against_main,
                }
            )
            continue
        candidates.append(retired_entry.as_candidate())

    return base_sha, candidates, skipped, scanned


def revalidate_and_delete(
    client: GitHubClient,
    candidate: Candidate,
    base: str,
    retired: dict[str, RetiredEntry],
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

    if candidate.basis == "exact-merged-pr":
        if not exact_pr_identity(client, candidate, base):
            return False, "merged-pr-identity-changed"
    elif candidate.basis == "explicit-retired-ancestor":
        entry = retired.get(candidate.branch)
        if entry is None or entry.as_candidate() != candidate:
            return False, "retired-registry-changed"
        try:
            current_base_sha = branch_sha(client.get_branch(base))
            if not ancestor_retirement_valid(client, entry, current_base_sha):
                return False, "ancestor-proof-changed"
        except BranchGCError:
            return False, "base-unavailable"
    else:
        return False, "unsupported-candidate-basis"

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
        description=(
            "Delete only exact merged-PR branch heads or explicitly retired "
            "exact-SHA ancestor heads."
        )
    )
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--base", default="main")
    parser.add_argument("--mode", choices=("dry-run", "apply"), required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--retired-registry",
        default=str(DEFAULT_RETIRED_REGISTRY),
        help="Path to the exact-SHA retired branch registry.",
    )
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
        retired = load_retired_registry(Path(args.retired_registry))
        base_sha, candidates, skipped, scanned = evaluate(client, args.base, retired)

        if args.mode == "apply":
            for candidate in candidates:
                ok, reason = revalidate_and_delete(client, candidate, args.base, retired)
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
