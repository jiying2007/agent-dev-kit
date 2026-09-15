#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from github_governance import DEFAULT_REQUIRED_CHECKS, evaluate_state

API_VERSION = "2022-11-28"
DEFAULT_RULESET_NAME = "ADK main governance"


class AdminError(RuntimeError):
    pass


class AdminClient:
    def __init__(self, repo: str, token: str | None = None) -> None:
        self.repo = repo
        self.token = token

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "agent-dev-kit-github-governance-admin",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.github.com{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read()
                return json.loads(body) if body else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AdminError(
                f"GitHub API {method} {path} failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise AdminError(f"GitHub API {method} {path} failed: {exc}") from exc


def desired_repository_settings() -> dict[str, bool]:
    return {
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "delete_branch_on_merge": True,
    }


def desired_ruleset_payload(
    branch: str,
    ruleset_name: str,
    required_checks: tuple[str, ...] = DEFAULT_REQUIRED_CHECKS,
) -> dict[str, Any]:
    return {
        "name": ruleset_name,
        "target": "branch",
        "enforcement": "active",
        "bypass_actors": [],
        "conditions": {
            "ref_name": {
                "include": [f"refs/heads/{branch}"],
                "exclude": [],
            }
        },
        "rules": [
            {
                "type": "pull_request",
                "parameters": {
                    "allowed_merge_methods": ["squash"],
                    "dismiss_stale_reviews_on_push": False,
                    "require_code_owner_review": False,
                    "require_last_push_approval": False,
                    "required_approving_review_count": 0,
                    "required_review_thread_resolution": False,
                },
            },
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": context}
                        for context in required_checks
                    ],
                    "strict_required_status_checks_policy": True,
                },
            },
            {"type": "non_fast_forward"},
            {"type": "deletion"},
        ],
    }


def _pull_request_state(rule: dict[str, Any]) -> dict[str, Any]:
    parameters = rule.get("parameters", {})
    return {
        "allowed_merge_methods": sorted(parameters.get("allowed_merge_methods", [])),
        "dismiss_stale_reviews_on_push": parameters.get("dismiss_stale_reviews_on_push"),
        "require_code_owner_review": parameters.get("require_code_owner_review"),
        "require_last_push_approval": parameters.get("require_last_push_approval"),
        "required_approving_review_count": parameters.get("required_approving_review_count"),
        "required_review_thread_resolution": parameters.get("required_review_thread_resolution"),
    }


def _status_check_state(rule: dict[str, Any]) -> dict[str, Any]:
    parameters = rule.get("parameters", {})
    checks = sorted(
        check.get("context")
        for check in parameters.get("required_status_checks", [])
        if isinstance(check, dict) and isinstance(check.get("context"), str)
    )
    return {
        "do_not_enforce_on_create": parameters.get("do_not_enforce_on_create", False),
        "required_status_checks": checks,
        "strict_required_status_checks_policy": parameters.get(
            "strict_required_status_checks_policy"
        ),
    }


def normalized_ruleset(ruleset: dict[str, Any]) -> dict[str, Any]:
    rule_map = {
        rule.get("type"): rule
        for rule in ruleset.get("rules", [])
        if isinstance(rule, dict) and isinstance(rule.get("type"), str)
    }
    return {
        "name": ruleset.get("name"),
        "target": ruleset.get("target"),
        "enforcement": ruleset.get("enforcement"),
        "bypass_actors": ruleset.get("bypass_actors", []),
        "conditions": ruleset.get("conditions", {}),
        "rule_types": sorted(rule_map),
        "pull_request": _pull_request_state(rule_map.get("pull_request", {})),
        "required_status_checks": _status_check_state(
            rule_map.get("required_status_checks", {})
        ),
    }


def _desired_normalized_ruleset(payload: dict[str, Any]) -> dict[str, Any]:
    return normalized_ruleset(payload)


def _find_managed_ruleset(
    rulesets: list[dict[str, Any]],
    ruleset_name: str,
) -> dict[str, Any] | None:
    matches = [ruleset for ruleset in rulesets if ruleset.get("name") == ruleset_name]
    if len(matches) > 1:
        ids = [ruleset.get("id") for ruleset in matches]
        raise AdminError(f"multiple managed rulesets named {ruleset_name!r}: {ids}")
    return matches[0] if matches else None


def _require_observable_repository_settings(repository: dict[str, Any]) -> None:
    missing = [
        key
        for key in desired_repository_settings()
        if not isinstance(repository.get(key), bool)
    ]
    if missing:
        raise AdminError(
            "repository administration settings are not observable: "
            + ", ".join(sorted(missing))
            + "; set ADK_GITHUB_ADMIN_TOKEN with repository Administration read/write "
            "before planning or applying governance"
        )


def build_plan(
    repository: dict[str, Any],
    branch_state: dict[str, Any],
    rulesets: list[dict[str, Any]],
    *,
    branch: str,
    ruleset_name: str,
    required_checks: tuple[str, ...] = DEFAULT_REQUIRED_CHECKS,
) -> dict[str, Any]:
    _require_observable_repository_settings(repository)
    desired_settings = desired_repository_settings()
    repository_changes = {
        key: {"current": repository.get(key), "desired": value}
        for key, value in desired_settings.items()
        if repository.get(key) != value
    }
    desired_ruleset = desired_ruleset_payload(branch, ruleset_name, required_checks)
    managed = _find_managed_ruleset(rulesets, ruleset_name)
    if managed is None:
        ruleset_action = "create"
        managed_id = None
    elif normalized_ruleset(managed) == _desired_normalized_ruleset(desired_ruleset):
        ruleset_action = "none"
        managed_id = managed.get("id")
    else:
        ruleset_action = "update"
        managed_id = managed.get("id")

    return {
        "schema_version": 1,
        "mode": "plan",
        "repository": repository.get("full_name"),
        "branch": branch,
        "current_governance": evaluate_state(
            repository,
            branch_state,
            rulesets,
            branch_name=branch,
            required_checks=required_checks,
        ),
        "repository_changes": repository_changes,
        "ruleset": {
            "name": ruleset_name,
            "action": ruleset_action,
            "id": managed_id,
            "desired": desired_ruleset,
        },
    }


def fetch_state(
    client: AdminClient,
    repo: str,
    branch: str,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    repository = client.request("GET", f"/repos/{repo}")
    branch_state = client.request("GET", f"/repos/{repo}/branches/{branch}")
    summaries = client.request("GET", f"/repos/{repo}/rulesets")
    if not isinstance(summaries, list):
        raise AdminError("repository rulesets response is not a list")
    details = [
        client.request("GET", f"/repos/{repo}/rulesets/{ruleset['id']}")
        for ruleset in summaries
        if isinstance(ruleset, dict) and ruleset.get("id") is not None
    ]
    return repository, branch_state, details


def _run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AdminError("git is required for --apply checkout verification") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise AdminError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def inspect_local_checkout() -> dict[str, Any]:
    return {
        "toplevel": _run_git("rev-parse", "--show-toplevel"),
        "branch": _run_git("branch", "--show-current"),
        "head_sha": _run_git("rev-parse", "HEAD"),
        "status": _run_git("status", "--porcelain"),
        "origin": _run_git("remote", "get-url", "origin"),
    }


def _repo_from_github_remote(remote: str) -> str | None:
    value = remote.strip()
    ssh_prefix = "git@github.com:"
    if value.startswith(ssh_prefix):
        path = value[len(ssh_prefix) :]
    else:
        parsed = urllib.parse.urlparse(value)
        if parsed.hostname != "github.com":
            return None
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    return path or None


def validate_local_checkout(
    repo: str,
    branch: str,
    branch_state: dict[str, Any],
    local: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observed = dict(local or inspect_local_checkout())
    remote_sha = branch_state.get("commit", {}).get("sha")
    if not isinstance(remote_sha, str) or not remote_sha:
        raise AdminError("live GitHub branch state has no commit SHA")

    problems: list[str] = []
    local_branch = str(observed.get("branch") or "")
    local_head = str(observed.get("head_sha") or "")
    status = str(observed.get("status") or "")
    origin = str(observed.get("origin") or "")
    origin_repo = _repo_from_github_remote(origin)

    if local_branch != branch:
        problems.append(f"local branch is {local_branch!r}, expected {branch!r}")
    if local_head != remote_sha:
        problems.append(f"local HEAD {local_head!r} does not match live {branch} {remote_sha!r}")
    if status:
        problems.append("local working tree is not clean")
    if origin_repo is None or origin_repo.lower() != repo.lower():
        problems.append(f"origin {origin!r} does not identify repository {repo!r}")
    if problems:
        raise AdminError("unsafe local checkout for --apply: " + "; ".join(problems))

    return {
        "toplevel": observed.get("toplevel"),
        "branch": local_branch,
        "head_sha": local_head,
        "remote_branch_sha": remote_sha,
        "origin": origin,
        "repository": origin_repo,
        "worktree_clean": True,
    }


def apply_plan(
    client: AdminClient,
    repo: str,
    plan: dict[str, Any],
) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    if plan["repository_changes"]:
        payload = {
            key: change["desired"]
            for key, change in plan["repository_changes"].items()
        }
        client.request("PATCH", f"/repos/{repo}", payload)
        operations.append({"operation": "update_repository", "payload": payload})

    ruleset_plan = plan["ruleset"]
    action = ruleset_plan["action"]
    if action == "create":
        created = client.request(
            "POST",
            f"/repos/{repo}/rulesets",
            ruleset_plan["desired"],
        )
        operations.append(
            {"operation": "create_ruleset", "id": created.get("id")}
        )
    elif action == "update":
        ruleset_id = ruleset_plan["id"]
        if ruleset_id is None:
            raise AdminError("managed ruleset update has no ruleset id")
        client.request(
            "PUT",
            f"/repos/{repo}/rulesets/{ruleset_id}",
            ruleset_plan["desired"],
        )
        operations.append({"operation": "update_ruleset", "id": ruleset_id})
    elif action != "none":
        raise AdminError(f"unsupported ruleset plan action: {action!r}")
    return operations


def _render(payload: dict[str, Any], out: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan or apply ADK native GitHub governance with an admin token."
    )
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--branch", default="main")
    parser.add_argument("--ruleset-name", default=DEFAULT_RULESET_NAME)
    parser.add_argument("--required-check", action="append", dest="required_checks")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if not args.repo:
        parser.error("--repo or GITHUB_REPOSITORY is required")

    required_checks = tuple(args.required_checks or DEFAULT_REQUIRED_CHECKS)
    token = os.environ.get("ADK_GITHUB_ADMIN_TOKEN")
    if args.apply:
        if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
            raise AdminError("--apply refuses to run inside GitHub Actions")
        if not token:
            raise AdminError(
                "--apply requires ADK_GITHUB_ADMIN_TOKEN with repository Administration write"
            )

    client = AdminClient(args.repo, token)
    repository, branch_state, rulesets = fetch_state(client, args.repo, args.branch)
    plan = build_plan(
        repository,
        branch_state,
        rulesets,
        branch=args.branch,
        ruleset_name=args.ruleset_name,
        required_checks=required_checks,
    )
    if not args.apply:
        _render(plan, args.out)
        return 0 if not plan["repository_changes"] and plan["ruleset"]["action"] == "none" else 1

    checkout = validate_local_checkout(args.repo, args.branch, branch_state)
    operations = apply_plan(client, args.repo, plan)
    repository, branch_state, rulesets = fetch_state(client, args.repo, args.branch)
    verification = evaluate_state(
        repository,
        branch_state,
        rulesets,
        branch_name=args.branch,
        required_checks=required_checks,
    )
    result = {
        "schema_version": 1,
        "mode": "apply",
        "repository": args.repo,
        "local_checkout": checkout,
        "operations": operations,
        "verification": verification,
    }
    _render(result, args.out)
    return 0 if verification["compliant"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AdminError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
