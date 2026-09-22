"""Deterministic, read-only Harness readiness evidence projection."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .readiness_evidence import (
    EXPECTED_DIMENSIONS as EXPECTED_DIMENSIONS,
)
from .readiness_evidence import (
    NON_MATERIAL_PARTS as NON_MATERIAL_PARTS,
)
from .readiness_evidence import (
    REPOSITORY_OWNER_PATHS as REPOSITORY_OWNER_PATHS,
)
from .readiness_evidence import (
    STATUS_PRIORITY as STATUS_PRIORITY,
)
from .readiness_evidence import (
    VALID_STATUSES as VALID_STATUSES,
)
from .readiness_evidence import (
    ReadinessContractError as ReadinessContractError,
)
from .readiness_evidence import (
    RepositoryIndex as RepositoryIndex,
)
from .readiness_evidence import (
    _blocker as _blocker,
)
from .readiness_evidence import (
    _deduplicate as _deduplicate,
)
from .readiness_evidence import (
    _dimension_contracts as _dimension_contracts,
)
from .readiness_evidence import (
    _load_metadata as _load_metadata,
)
from .readiness_evidence import (
    _material_evidence as _material_evidence,
)
from .readiness_evidence import (
    _metadata_for_dimension as _metadata_for_dimension,
)
from .readiness_evidence import (
    _valid_verified_at as _valid_verified_at,
)
from .readiness_evidence import (
    _verified_at_issue as _verified_at_issue,
)
from .readiness_evidence import (
    load_readiness_contract as load_readiness_contract,
)


from .readiness_tools import _evaluate_tools


def _finish_dimension(
    contract_item: Mapping[str, Any],
    raw_status: str,
    evidence: Iterable[str],
    blockers: Sequence[Dict[str, str]],
    metadata: Mapping[str, Any],
    metadata_errors: Sequence[Dict[str, str]],
    metadata_path: str,
    evidence_limit: int,
    blocker_limit: int,
    verification_policy: Optional[Mapping[str, Any]] = None,
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    if raw_status not in VALID_STATUSES:
        raise ReadinessContractError("invalid readiness status: {}".format(raw_status))
    owner, verified_at, metadata_blockers = _metadata_for_dimension(
        metadata,
        str(contract_item["dimension_id"]),
        metadata_path,
        verification_policy=verification_policy,
        as_of=as_of,
    )
    all_blockers = list(blockers)
    status = raw_status
    if raw_status != "not-applicable":
        all_blockers.extend(metadata_errors)
        all_blockers.extend(metadata_blockers)
        if metadata_errors and STATUS_PRIORITY[status] < STATUS_PRIORITY["needs-review"]:
            status = "needs-review"
        elif metadata_blockers and status == "pass":
            status = "partial"
    if len(all_blockers) > blocker_limit:
        omitted = len(all_blockers) - blocker_limit + 1
        all_blockers = all_blockers[: blocker_limit - 1] + [
            _blocker("blockers_truncated", "另有 {} 个 blocker 未展开".format(omitted))
        ]
    metadata_evidence = [metadata_path] if metadata_path in evidence or metadata else []
    return {
        "dimension_id": contract_item["dimension_id"],
        "title": contract_item["title"],
        "status": status,
        "evidence_refs": _deduplicate(list(evidence) + metadata_evidence, evidence_limit),
        "last_verified_at": verified_at,
        "owner": owner,
        "blockers": all_blockers,
        "next_action": contract_item["next_action"],
    }


def _evaluate_context(index: RepositoryIndex, contract: Mapping[str, Any]) -> Tuple[str, List[str], List[Dict[str, str]]]:
    evidence: List[str] = []
    blockers: List[Dict[str, str]] = []
    agents = index.read_text("AGENTS.md")
    readme_ref = next((name for name in ("README.md", "README.rst", "README") if name in index.files), None)
    if agents is not None:
        evidence.append("AGENTS.md")
    if readme_ref:
        evidence.append(readme_ref)
    if agents is not None:
        line_count = len(agents.splitlines())
        max_lines = int(contract["scan"]["instruction_max_lines"])
        if line_count > max_lines:
            blockers.append(
                _blocker(
                    "oversized_agent_index",
                    "根 AGENTS.md 为 {} 行，超过 {} 行的索引预算".format(line_count, max_lines),
                    "AGENTS.md",
                )
            )
    if agents is not None and readme_ref and not blockers:
        return "pass", evidence, blockers
    if agents is not None and readme_ref:
        return "partial", evidence, blockers
    if agents is not None or readme_ref:
        blockers.append(_blocker("incomplete_context_entrypoint", "根 AI 入口或 README 缺失"))
        return "needs-review", evidence, blockers
    blockers.append(_blocker("missing_context_entrypoint", "未发现根 AGENTS.md 与 README"))
    return "needs-review", evidence, blockers


def _evaluate_spec(index: RepositoryIndex) -> Tuple[str, List[str], List[Dict[str, str]]]:
    spec_names = {"requirements.md", "requirement.md", "proposal.md", "design.md", "spec.md"}
    task_names = {"tasks.md", "task.md", "plan.md"}
    acceptance_names = {
        "verify-report.md",
        "review-report.md",
        "acceptance.md",
        "test-report.md",
        "checklist.md",
        "negative-results.md",
    }
    specs = [relative for relative in index.by_basename(spec_names) if _material_evidence(relative)]
    tasks = [relative for relative in index.by_basename(task_names) if _material_evidence(relative)]
    acceptance = [relative for relative in index.by_basename(acceptance_names) if _material_evidence(relative)]
    evidence = specs[:4] + tasks[:4] + acceptance[:4]
    present = sum(bool(group) for group in (specs, tasks, acceptance))
    blockers: List[Dict[str, str]] = []
    if not specs:
        blockers.append(_blocker("missing_spec", "未发现 requirements/spec/proposal/design 工件"))
    if not tasks:
        blockers.append(_blocker("missing_task_contract", "未发现 task/plan 工件"))
    if not acceptance:
        blockers.append(_blocker("missing_acceptance_evidence", "未发现验收、验证或评审工件"))
    if present == 3:
        return "pass", evidence, blockers
    if present == 2:
        return "partial", evidence, blockers
    return "needs-review", evidence, blockers


def _evaluate_state(index: RepositoryIndex) -> Tuple[str, List[str], List[Dict[str, str]]]:
    state_names = {"state.yaml", "state.yml", "state.json", "progress.md", "history.log"}
    states = [
        relative
        for relative in index.by_basename(state_names)
        if _material_evidence(relative)
        and any(part.lower() in {".adk", "changes", "plans", "openspec", ".codebuddy"} for part in Path(relative).parts)
    ]
    knowledge = [
        relative
        for relative in sorted(index.files)
        if _material_evidence(relative)
        and any(part.lower() in {"decisions", "adr", "runbooks", "knowledge"} for part in Path(relative).parts)
    ]
    evidence = states[:6] + knowledge[:6]
    blockers: List[Dict[str, str]] = []
    if not states:
        blockers.append(_blocker("missing_persistent_state", "未发现 change/plan 的持久状态工件"))
    if not knowledge:
        blockers.append(_blocker("missing_governed_knowledge", "未发现 decision/ADR/runbook/knowledge 工件"))
    if states and knowledge:
        return "pass", evidence, blockers
    if states or knowledge:
        return "partial", evidence, blockers
    return "needs-review", evidence, blockers


def _has_validation_command(index: RepositoryIndex) -> List[str]:
    evidence: List[str] = []
    pattern = re.compile(r"`[^`\n]*(?:test|check|verify|lint|validate)[^`\n]*`", re.IGNORECASE)
    for relative in ("AGENTS.md", "README.md", "README.rst", "README"):
        content = index.read_text(relative)
        if content is not None and pattern.search(content):
            evidence.append(relative)
    return evidence


def _evaluate_verification(index: RepositoryIndex) -> Tuple[str, List[str], List[Dict[str, str]]]:
    test_suffixes = (".py", ".sh", ".go", ".rs", ".java", ".kt", ".c", ".cc", ".cpp", ".js", ".ts")
    tests = [
        relative
        for relative in sorted(index.files)
        if _material_evidence(relative)
        and (
            (relative.startswith("tests/") and Path(relative).suffix.lower() in test_suffixes)
            or Path(relative).name.startswith("test_")
            or Path(relative).name.endswith(("_test.go", ".spec.ts", ".test.ts", ".test.js"))
        )
    ]
    ci_candidates = [
        relative
        for relative in sorted(index.files)
        if relative.startswith(".github/workflows/")
        or relative in {".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml"}
    ]
    ci = []
    validation_term = re.compile(r"(?:test|check|verify|lint|validate)", re.IGNORECASE)
    for relative in ci_candidates:
        content = index.read_text(relative)
        if content is not None and validation_term.search(content):
            ci.append(relative)
    commands = _has_validation_command(index)
    evidence = tests[:5] + ci[:5] + commands
    present = sum(bool(group) for group in (tests, ci, commands))
    blockers: List[Dict[str, str]] = []
    if not tests:
        blockers.append(_blocker("missing_tests", "未发现测试工件"))
    if not ci:
        blockers.append(_blocker("missing_ci", "未发现 CI workflow"))
    if not commands:
        blockers.append(_blocker("missing_validation_command", "根说明未提供可执行 test/check/verify/lint/validate 命令"))
    if present == 3:
        return "pass", evidence, blockers
    if present == 2:
        return "partial", evidence, blockers
    return "needs-review", evidence, blockers


def _evaluate_recovery(index: RepositoryIndex) -> Tuple[str, List[str], List[Dict[str, str]]]:
    tokens = ("rollback", "recovery", "recover", "restore", "backup", "回滚", "恢复", "备份")
    evidence = [
        relative
        for relative in sorted(index.files)
        if _material_evidence(relative)
        and relative.startswith(("docs/runbooks/", "scripts/", ".github/workflows/"))
        and any(token in relative.lower() for token in tokens)
    ]
    if evidence:
        return "pass", evidence[:10], []
    return "needs-review", [], [_blocker("missing_recovery_evidence", "未发现 rollback/recovery/backup 工件")]


def _evaluate_freshness(index: RepositoryIndex) -> Tuple[str, List[str], List[Dict[str, str]]]:
    check_tokens = ("check-doc", "docs-lint", "lint-doc", "check-format", "check-agents", "catalog", "freshness", "entropy")
    checks: List[str] = []
    for relative in sorted(index.files):
        if not _material_evidence(relative):
            continue
        lowered = relative.lower()
        if relative.startswith(("scripts/", "tests/", ".github/workflows/")) and any(
            token in lowered for token in check_tokens
        ):
            checks.append(relative)
            continue
        if relative in {".pre-commit-config.yaml", ".pre-commit-config.yml"}:
            if index.read_text(relative):
                checks.append(relative)
            continue
        if relative == "Makefile":
            content = index.read_text(relative)
            if content is not None and re.search(r"(?:doc|format|catalog|freshness|entropy)", content, re.IGNORECASE):
                checks.append(relative)
    owners = sorted(relative for relative in REPOSITORY_OWNER_PATHS if relative in index.files)
    evidence = checks[:8] + owners[:4]
    blockers: List[Dict[str, str]] = []
    if not checks:
        blockers.append(_blocker("missing_freshness_check", "未发现文档、格式、目录或新鲜度机械检查"))
    if not owners:
        blockers.append(_blocker("missing_ownership_evidence", "未发现 CODEOWNERS/OWNERS"))
    if index.truncated or index.errors:
        blockers.append(_blocker("scan_incomplete", "仓库扫描被预算截断或包含不可读路径"))
        return "needs-review", evidence, blockers
    if checks and owners:
        return "pass", evidence, blockers
    if checks or owners:
        return "partial", evidence, blockers
    return "needs-review", evidence, blockers


def _overall_status(dimensions: Sequence[Mapping[str, Any]]) -> str:
    statuses = [str(item["status"]) for item in dimensions if item["status"] != "not-applicable"]
    if not statuses:
        return "pass"
    return max(statuses, key=lambda status: STATUS_PRIORITY[status])


def run_harness_readiness(
    root: Path,
    contract_path: Path,
    mode: str = "report-only",
    as_of: Optional[date] = None,
) -> Dict[str, Any]:
    """Inspect a repository and return a stable Harness readiness report."""

    if mode not in {"report-only", "gate"}:
        raise ReadinessContractError("Harness readiness mode must be report-only or gate")
    if mode == "gate" and as_of is not None:
        raise ReadinessContractError(
            "Harness readiness gate does not accept an explicit as_of; gate evaluation must use the current date"
        )
    contract = load_readiness_contract(contract_path)
    index = RepositoryIndex(root, contract)
    contracts = _dimension_contracts(contract)
    metadata_path = str(contract["metadata_path"])
    metadata, metadata_errors = _load_metadata(index, contract)
    effective_as_of = as_of or date.today()
    evidence_limit = int(contract["scan"]["max_evidence_per_dimension"])
    blocker_limit = int(contract["scan"]["max_blockers_per_dimension"])
    raw = {
        "context_legibility": _evaluate_context(index, contract),
        "spec_and_execution_contract": _evaluate_spec(index),
        "tool_and_permission_boundary": _evaluate_tools(index, contract, metadata),
        "state_and_knowledge_continuity": _evaluate_state(index),
        "verification_review_and_eval": _evaluate_verification(index),
        "recovery_and_rollback": _evaluate_recovery(index),
        "freshness_and_entropy_control": _evaluate_freshness(index),
    }
    dimensions = []
    for dimension_id in EXPECTED_DIMENSIONS:
        status, evidence, blockers = raw[dimension_id]
        dimensions.append(
            _finish_dimension(
                contracts[dimension_id],
                status,
                evidence,
                blockers,
                metadata,
                metadata_errors,
                metadata_path,
                evidence_limit,
                blocker_limit,
                verification_policy=contract["verification"],
                as_of=effective_as_of,
            )
        )
    overall = _overall_status(dimensions)
    counts = {status: 0 for status in VALID_STATUSES}
    for item in dimensions:
        counts[item["status"]] += 1
    return {
        "schema_version": "adk-harness-readiness-report/v1",
        "contract_version": contract["contract_version"],
        "mode": mode,
        "as_of": effective_as_of.isoformat(),
        "target_root": str(index.root),
        "overall_status": overall,
        "counts": counts,
        "scan": {
            "files_seen": len(index.files),
            "text_files_read": sum(value is not None for value in index.text_cache.values()),
            "truncated": index.truncated,
            "errors": sorted(set(index.errors)),
        },
        "dimensions": dimensions,
        "score": None,
        "field_evidence_status": "not-verified",
    }


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def readiness_markdown(report: Mapping[str, Any]) -> str:
    """Render a readiness report without adding volatile timestamps."""

    lines = [
        "# Harness Readiness Report",
        "",
        "- target: `{}`".format(report["target_root"]),
        "- mode: `{}`".format(report["mode"]),
        "- as_of: `{}`".format(report["as_of"]),
        "- overall_status: `{}`".format(report["overall_status"]),
        "- score: `not-used`",
        "- field_evidence_status: `{}`".format(report["field_evidence_status"]),
        "",
        "| Dimension | Status | Owner | Last verified | Evidence |",
        "|---|---|---|---|---:|",
    ]
    for item in report["dimensions"]:
        lines.append(
            "| {} | {} | {} | {} | {} |".format(
                _markdown_cell(item["dimension_id"]),
                _markdown_cell(item["status"]),
                _markdown_cell(item["owner"]),
                _markdown_cell(item["last_verified_at"]),
                len(item["evidence_refs"]),
            )
        )
    for item in report["dimensions"]:
        lines.extend(
            [
                "",
                "## {}".format(item["title"]),
                "",
                "- id: `{}`".format(item["dimension_id"]),
                "- status: `{}`".format(item["status"]),
                "- owner: `{}`".format(item["owner"]),
                "- last_verified_at: `{}`".format(item["last_verified_at"]),
                "- next_action: {}".format(item["next_action"]),
                "",
                "### Evidence",
                "",
            ]
        )
        if item["evidence_refs"]:
            lines.extend("- `{}`".format(ref) for ref in item["evidence_refs"])
        else:
            lines.append("- none")
        lines.extend(["", "### Blockers", ""])
        if item["blockers"]:
            for blocker in item["blockers"]:
                location = " (`{}`)".format(blocker["evidence_ref"]) if blocker["evidence_ref"] else ""
                lines.append("- `{}`: {}{}".format(blocker["code"], blocker["message"], location))
        else:
            lines.append("- none")
    scan = report["scan"]
    lines.extend(
        [
            "",
            "## Scan boundary",
            "",
            "- files_seen: {}".format(scan["files_seen"]),
            "- text_files_read: {}".format(scan["text_files_read"]),
            "- truncated: {}".format(str(scan["truncated"]).lower()),
            "- errors: {}".format(len(scan["errors"])),
            "",
        ]
    )
    return "\n".join(lines)
