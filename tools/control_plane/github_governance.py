#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_VERSION = "2022-11-28"
DEFAULT_REQUIRED_CHECKS = (
    "contract-py3.11",
    "contract-py3.12",
    "regression-py3.11",
    "regression-py3.12",
    "deterministic-eval-package",
    "static-security",
    "codeql-python",
    "dependency-review",
    "branch-gc-dry-run",
    "platform-vnext",
)


class GovernanceError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, repo: str, token: str | None = None) -> None:
        self.repo = repo
        self.token = token

    def get(self, path: str) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "agent-dev-kit-github-governance",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GovernanceError(
                f"GitHub API GET {path} failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise GovernanceError(f"GitHub API GET {path} failed: {exc}") from exc


def _targets_branch(ruleset: dict[str, Any], branch: str, default_branch: str) -> bool:
    if ruleset.get("target") != "branch" or ruleset.get("enforcement") != "active":
        return False
    ref_name = ruleset.get("conditions", {}).get("ref_name", {})
    includes = set(ref_name.get("include", []))
    excludes = set(ref_name.get("exclude", []))
    ref = f"refs/heads/{branch}"
    branch_matches = (
        ref in includes
        or branch in includes
        or "~ALL" in includes
        or (branch == default_branch and "~DEFAULT_BRANCH" in includes)
    )
    branch_excluded = (
        ref in excludes
        or branch in excludes
        or "~ALL" in excludes
        or (branch == default_branch and "~DEFAULT_BRANCH" in excludes)
    )
    return branch_matches and not branch_excluded


def _ruleset_evidence(
    rulesets: list[dict[str, Any]],
    branch: str,
    default_branch: str,
) -> tuple[list[dict[str, Any]], set[str], set[str]]:
    applicable = [
        ruleset
        for ruleset in rulesets
        if _targets_branch(ruleset, branch, default_branch)
    ]
    rule_types: set[str] = set()
    required_contexts: set[str] = set()
    for ruleset in applicable:
        for rule in ruleset.get("rules", []):
            rule_type = rule.get("type")
            if isinstance(rule_type, str):
                rule_types.add(rule_type)
            if rule_type == "required_status_checks":
                for check in rule.get("parameters", {}).get(
                    "required_status_checks", []
                ):
                    context = check.get("context")
                    if isinstance(context, str):
                        required_contexts.add(context)
    return applicable, rule_types, required_contexts


def evaluate_state(
    repository: dict[str, Any],
    branch: dict[str, Any],
    rulesets: list[dict[str, Any]],
    *,
    branch_name: str,
    required_checks: tuple[str, ...] = DEFAULT_REQUIRED_CHECKS,
) -> dict[str, Any]:
    default_branch = str(repository.get("default_branch") or "main")
    applicable, rule_types, required_contexts = _ruleset_evidence(
        rulesets,
        branch_name,
        default_branch,
    )
    missing_contexts = sorted(set(required_checks) - required_contexts)

    checks = {
        "main_protected": bool(branch.get("protected")),
        "active_branch_ruleset": bool(applicable),
        "pull_request_required": "pull_request" in rule_types,
        "required_status_checks_present": "required_status_checks" in rule_types,
        "all_required_checks_enforced": not missing_contexts,
        "force_push_blocked": "non_fast_forward" in rule_types,
        "branch_deletion_blocked": "deletion" in rule_types,
        "squash_only_merge_policy": bool(repository.get("allow_squash_merge"))
        and not bool(repository.get("allow_merge_commit"))
        and not bool(repository.get("allow_rebase_merge")),
        "delete_branch_on_merge": bool(repository.get("delete_branch_on_merge")),
    }

    violations: list[str] = []
    remediation: list[str] = []
    if not checks["main_protected"]:
        violations.append(f"branch {branch_name!r} is not protected")
        remediation.append("enable native protection/ruleset enforcement for main")
    if not checks["active_branch_ruleset"]:
        violations.append(f"no active branch ruleset targets {branch_name!r}")
        remediation.append("create an active ruleset targeting refs/heads/main")
    if not checks["pull_request_required"]:
        violations.append("active ruleset does not require pull requests")
        remediation.append("add a pull_request rule")
    if not checks["required_status_checks_present"]:
        violations.append("active ruleset does not require status checks")
        remediation.append("add a required_status_checks rule")
    if missing_contexts:
        violations.append(
            "required status checks missing: " + ", ".join(missing_contexts)
        )
        remediation.append("require every canonical ADK qualification check")
    if not checks["force_push_blocked"]:
        violations.append("active ruleset does not block non-fast-forward updates")
        remediation.append("add a non_fast_forward rule")
    if not checks["branch_deletion_blocked"]:
        violations.append("active ruleset does not block branch deletion")
        remediation.append("add a deletion rule")
    if not checks["squash_only_merge_policy"]:
        violations.append("repository merge methods are not squash-only")
        remediation.append("enable squash merge; disable merge-commit and rebase merge")
    if not checks["delete_branch_on_merge"]:
        violations.append("delete_branch_on_merge is disabled")
        remediation.append("enable native branch deletion after merge")

    return {
        "schema_version": 1,
        "repository": repository.get("full_name"),
        "branch": branch_name,
        "default_branch": default_branch,
        "compliant": all(checks.values()),
        "checks": checks,
        "required_status_checks": list(required_checks),
        "observed_status_checks": sorted(required_contexts),
        "missing_status_checks": missing_contexts,
        "active_rulesets": [
            {
                "id": ruleset.get("id"),
                "name": ruleset.get("name"),
                "bypass_actors": ruleset.get("bypass_actors", []),
            }
            for ruleset in applicable
        ],
        "observed_rule_types": sorted(rule_types),
        "merge_settings": {
            "allow_squash_merge": repository.get("allow_squash_merge"),
            "allow_merge_commit": repository.get("allow_merge_commit"),
            "allow_rebase_merge": repository.get("allow_rebase_merge"),
            "delete_branch_on_merge": repository.get("delete_branch_on_merge"),
        },
        "violations": violations,
        "remediation": remediation,
    }


def fetch_live_state(
    repo: str,
    branch_name: str,
    token: str | None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    client = GitHubClient(repo, token)
    repository = client.get(f"/repos/{repo}")
    branch = client.get(f"/repos/{repo}/branches/{branch_name}")
    summaries = client.get(f"/repos/{repo}/rulesets")
    if not isinstance(summaries, list):
        raise GovernanceError("repository rulesets response is not a list")
    details = [
        client.get(f"/repos/{repo}/rulesets/{ruleset['id']}")
        for ruleset in summaries
        if isinstance(ruleset, dict) and ruleset.get("id") is not None
    ]
    return repository, branch, details


def load_fixture(path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["repository"], payload["branch"], payload["rulesets"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify native GitHub governance required for ADK terminal closure."
    )
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--required-check", action="append", dest="required_checks")
    args = parser.parse_args(argv)

    required_checks = tuple(args.required_checks or DEFAULT_REQUIRED_CHECKS)
    if args.fixture:
        repository, branch, rulesets = load_fixture(args.fixture)
    else:
        if not args.repo:
            parser.error("--repo or GITHUB_REPOSITORY is required")
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        repository, branch, rulesets = fetch_live_state(args.repo, args.branch, token)

    report = evaluate_state(
        repository,
        branch,
        rulesets,
        branch_name=args.branch,
        required_checks=required_checks,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["compliant"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GovernanceError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
