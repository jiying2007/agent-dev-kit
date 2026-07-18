"""Deterministic, read-only Harness readiness evidence projection."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


EXPECTED_DIMENSIONS = (
    "context_legibility",
    "spec_and_execution_contract",
    "tool_and_permission_boundary",
    "state_and_knowledge_continuity",
    "verification_review_and_eval",
    "recovery_and_rollback",
    "freshness_and_entropy_control",
)
VALID_STATUSES = ("pass", "partial", "needs-review", "blocked", "not-applicable")
STATUS_PRIORITY = {"pass": 0, "not-applicable": 0, "partial": 1, "needs-review": 2, "blocked": 3}
VERIFIED_AT = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?$")
SECRET_REFERENCE = re.compile(
    r"^(?:Bearer\s+)?(?:"
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|"
    r"\$[A-Za-z_][A-Za-z0-9_]*|"
    r"process\.env\.[A-Za-z_][A-Za-z0-9_]*|"
    r"(?:env|secret):[A-Za-z_][A-Za-z0-9_.-]*|"
    r"(?:YOUR|EXAMPLE)_[A-Z0-9_-]+|"
    r"REDACTED|CHANGEME|<[A-Za-z0-9_.-]+>"
    r")$",
    re.IGNORECASE,
)
NON_MATERIAL_PARTS = {"archive", "archives", "examples", "samples", "template", "templates"}
DEFAULT_VERIFICATION_MAX_AGE_DAYS = 90
DEFAULT_FUTURE_TOLERANCE_DAYS = 0
REPOSITORY_OWNER_PATHS = {"OWNERS", "CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"}


class ReadinessContractError(ValueError):
    """Raised when the readiness contract or target metadata is unusable."""


def load_readiness_contract(path: Path) -> Dict[str, Any]:
    """Load and minimally validate the readiness contract."""

    try:
        value = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, RecursionError) as exc:
        raise ReadinessContractError("cannot load Harness readiness contract: {}".format(exc)) from exc
    if not isinstance(value, dict):
        raise ReadinessContractError("Harness readiness contract must be a JSON object")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list):
        raise ReadinessContractError("Harness readiness contract dimensions must be a list")
    if not all(
        isinstance(item, dict)
        and isinstance(item.get("dimension_id"), str)
        and isinstance(item.get("title"), str)
        and bool(item["title"].strip())
        and isinstance(item.get("next_action"), str)
        and bool(item["next_action"].strip())
        for item in dimensions
    ):
        raise ReadinessContractError("Harness readiness dimension fields are invalid")
    dimension_ids = tuple(item["dimension_id"] for item in dimensions)
    if dimension_ids != EXPECTED_DIMENSIONS:
        raise ReadinessContractError("Harness readiness contract dimension order or IDs are invalid")
    statuses = value.get("statuses")
    if statuses != list(VALID_STATUSES):
        raise ReadinessContractError("Harness readiness contract statuses are invalid")
    scan = value.get("scan")
    if not isinstance(scan, dict):
        raise ReadinessContractError("Harness readiness contract scan policy is missing")
    for key in (
        "max_files",
        "max_file_bytes",
        "instruction_max_lines",
        "max_evidence_per_dimension",
        "max_blockers_per_dimension",
    ):
        if not isinstance(scan.get(key), int) or scan[key] < 1:
            raise ReadinessContractError("Harness readiness contract scan.{} must be a positive integer".format(key))
    if scan["max_blockers_per_dimension"] < 2:
        raise ReadinessContractError("Harness readiness max_blockers_per_dimension must be at least 2")
    excluded = scan.get("excluded_directories")
    if not isinstance(excluded, list) or not all(isinstance(item, str) and item for item in excluded):
        raise ReadinessContractError("Harness readiness contract excluded_directories are invalid")
    if not isinstance(value.get("contract_version"), str) or not value["contract_version"].strip():
        raise ReadinessContractError("Harness readiness contract_version is missing")
    if not isinstance(value.get("metadata_path"), str) or not value["metadata_path"]:
        raise ReadinessContractError("Harness readiness contract metadata_path is missing")
    metadata_path = Path(value["metadata_path"])
    if metadata_path.is_absolute() or ".." in metadata_path.parts:
        raise ReadinessContractError("Harness readiness metadata_path must stay inside the target repository")
    verification = value.get("verification")
    if not isinstance(verification, dict):
        raise ReadinessContractError("Harness readiness verification policy is missing")
    if not isinstance(verification.get("max_age_days"), int) or verification["max_age_days"] < 1:
        raise ReadinessContractError("Harness readiness verification.max_age_days must be a positive integer")
    if (
        not isinstance(verification.get("future_tolerance_days"), int)
        or verification["future_tolerance_days"] < 0
    ):
        raise ReadinessContractError(
            "Harness readiness verification.future_tolerance_days must be a non-negative integer"
        )
    mcp = value.get("mcp")
    if not isinstance(mcp, dict):
        raise ReadinessContractError("Harness readiness MCP policy is missing")
    for key in ("max_configs", "max_permission_docs"):
        if not isinstance(mcp.get(key), int) or mcp[key] < 1:
            raise ReadinessContractError("Harness readiness mcp.{} must be a positive integer".format(key))
    for key in ("config_names", "sensitive_key_fragments"):
        items = mcp.get(key)
        if not isinstance(items, list) or not items or not all(isinstance(item, str) and item for item in items):
            raise ReadinessContractError("Harness readiness mcp.{} is invalid".format(key))
    permission_terms = mcp.get("permission_evidence_terms")
    required_groups = {"read_only", "approval", "credential_boundary"}
    if not isinstance(permission_terms, dict) or set(permission_terms) != required_groups:
        raise ReadinessContractError("Harness readiness MCP permission evidence groups are invalid")
    if not all(
        isinstance(items, list) and items and all(isinstance(item, str) and item for item in items)
        for items in permission_terms.values()
    ):
        raise ReadinessContractError("Harness readiness MCP permission evidence terms are invalid")
    structured = mcp.get("structured_permission_boundary")
    if not isinstance(structured, dict):
        raise ReadinessContractError("Harness readiness structured permission boundary policy is missing")
    if not isinstance(structured.get("metadata_key"), str) or not structured["metadata_key"]:
        raise ReadinessContractError("Harness readiness structured permission metadata_key is invalid")
    required_true = structured.get("required_true_fields")
    if not isinstance(required_true, list) or not required_true or not all(
        isinstance(item, str) and item for item in required_true
    ):
        raise ReadinessContractError("Harness readiness structured permission true fields are invalid")
    if (
        not isinstance(structured.get("credential_source_field"), str)
        or not structured["credential_source_field"]
    ):
        raise ReadinessContractError("Harness readiness structured permission source field is invalid")
    allowed_sources = structured.get("allowed_credential_sources")
    if not isinstance(allowed_sources, list) or not allowed_sources or not all(
        isinstance(item, str) and item for item in allowed_sources
    ):
        raise ReadinessContractError("Harness readiness structured permission sources are invalid")
    return value


class RepositoryIndex:
    """Bounded, symlink-safe repository file index with lazy text reads."""

    def __init__(self, root: Path, contract: Mapping[str, Any]) -> None:
        resolved = root.expanduser().resolve()
        if not resolved.is_dir():
            raise ReadinessContractError("Harness readiness root is not a directory: {}".format(resolved))
        self.root = resolved
        scan = contract["scan"]
        self.max_files = int(scan["max_files"])
        self.max_file_bytes = int(scan["max_file_bytes"])
        self.excluded = set(str(item) for item in scan["excluded_directories"])
        self.files: Dict[str, Path] = {}
        self.text_cache: Dict[str, Optional[str]] = {}
        self.errors: List[str] = []
        self.truncated = False
        self._scan()

    def _scan(self) -> None:
        def on_error(exc: OSError) -> None:
            name = getattr(exc, "filename", None)
            if name:
                try:
                    label = Path(name).resolve().relative_to(self.root).as_posix()
                except (OSError, ValueError):
                    label = "unreadable-path"
            else:
                label = "unreadable-path"
            self.errors.append(label)

        for current, directories, filenames in os.walk(
            str(self.root), topdown=True, onerror=on_error, followlinks=False
        ):
            current_path = Path(current)
            directories[:] = sorted(
                name
                for name in directories
                if name not in self.excluded and not (current_path / name).is_symlink()
            )
            for name in sorted(filenames):
                path = current_path / name
                if path.is_symlink() or not path.is_file():
                    continue
                if len(self.files) >= self.max_files:
                    self.truncated = True
                    directories[:] = []
                    break
                try:
                    relative = path.relative_to(self.root).as_posix()
                except ValueError:
                    continue
                self.files[relative] = path
            if self.truncated:
                break

    def read_text(self, relative: str) -> Optional[str]:
        if relative in self.text_cache:
            return self.text_cache[relative]
        path = self.files.get(relative)
        if path is None:
            self.text_cache[relative] = None
            return None
        try:
            if path.stat().st_size > self.max_file_bytes:
                self.text_cache[relative] = None
                return None
            value = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            value = None
        self.text_cache[relative] = value
        return value

    def by_basename(self, names: Iterable[str]) -> List[str]:
        expected = {name.lower() for name in names}
        return sorted(relative for relative in self.files if Path(relative).name.lower() in expected)


def _blocker(code: str, message: str, evidence_ref: str = "") -> Dict[str, str]:
    return {"code": code, "message": message, "evidence_ref": evidence_ref}


def _deduplicate(values: Iterable[str], limit: int) -> List[str]:
    return sorted(set(value for value in values if value))[:limit]


def _material_evidence(relative: str) -> bool:
    parts = {part.lower() for part in Path(relative).parts[:-1]}
    return not bool(parts & NON_MATERIAL_PARTS)


def _dimension_contracts(contract: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    return {item["dimension_id"]: item for item in contract["dimensions"]}


def _load_metadata(index: RepositoryIndex, contract: Mapping[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    relative = str(contract["metadata_path"])
    content = index.read_text(relative)
    if content is None:
        if relative in index.files:
            return {}, [
                _blocker(
                    "unreadable_readiness_metadata",
                    "readiness metadata 超过扫描预算、不是 UTF-8 或不可读",
                    relative,
                )
            ]
        return {}, []
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return {}, [_blocker("invalid_readiness_metadata", "readiness metadata 不是有效 JSON", relative)]
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or not isinstance(value.get("dimensions", {}), dict)
    ):
        return {}, [
            _blocker(
                "invalid_readiness_metadata",
                "readiness metadata 必须使用 schema_version=1 且 dimensions 为对象",
                relative,
            )
        ]
    return value, []


def _metadata_for_dimension(
    metadata: Mapping[str, Any],
    dimension_id: str,
    metadata_path: str,
    verification_policy: Optional[Mapping[str, Any]] = None,
    as_of: Optional[date] = None,
) -> Tuple[str, str, List[Dict[str, str]]]:
    dimensions = metadata.get("dimensions", {})
    raw = dimensions.get(dimension_id, {}) if isinstance(dimensions, dict) else {}
    if not isinstance(raw, dict):
        return "unassigned", "not-recorded", [
            _blocker("invalid_dimension_metadata", "维度 metadata 必须是对象", metadata_path)
        ]
    blockers: List[Dict[str, str]] = []
    owner = raw.get("owner")
    if not isinstance(owner, str) or not owner.strip() or len(owner.strip()) > 100 or "\n" in owner:
        owner_value = "unassigned"
        blockers.append(_blocker("missing_owner", "未记录该维度 owner", metadata_path))
    else:
        owner_value = owner.strip()
    verified = raw.get("last_verified_at")
    verified_issue = None
    if isinstance(verified, str):
        verified_issue = _verified_at_issue(
            verified.strip(), verification_policy=verification_policy, as_of=as_of
        )
    if not isinstance(verified, str) or verified_issue == "invalid":
        verified_value = "not-recorded"
        blockers.append(_blocker("missing_last_verified_at", "未记录有效的 last_verified_at", metadata_path))
    else:
        verified_value = verified.strip()
        if verified_issue == "future":
            blockers.append(
                _blocker(
                    "future_last_verified_at",
                    "last_verified_at 晚于 readiness 评估日期",
                    metadata_path,
                )
            )
        elif verified_issue == "stale":
            blockers.append(
                _blocker(
                    "stale_last_verified_at",
                    "last_verified_at 超过 readiness freshness 窗口",
                    metadata_path,
                )
            )
    return owner_value, verified_value, blockers


def _parsed_verified_date(value: str) -> Optional[date]:
    if not VERIFIED_AT.fullmatch(value):
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        return date.fromisoformat(value)
    except ValueError:
        return None


def _verified_at_issue(
    value: str,
    verification_policy: Optional[Mapping[str, Any]] = None,
    as_of: Optional[date] = None,
) -> Optional[str]:
    verified_date = _parsed_verified_date(value)
    if verified_date is None:
        return "invalid"
    policy = verification_policy or {}
    max_age_days = int(policy.get("max_age_days", DEFAULT_VERIFICATION_MAX_AGE_DAYS))
    future_tolerance_days = int(
        policy.get("future_tolerance_days", DEFAULT_FUTURE_TOLERANCE_DAYS)
    )
    reference_date = as_of or date.today()
    if verified_date > reference_date + timedelta(days=future_tolerance_days):
        return "future"
    if (reference_date - verified_date).days > max_age_days:
        return "stale"
    return None


def _valid_verified_at(value: str) -> bool:
    return _verified_at_issue(value) is None


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


def _walk_json(value: Any, parts: Tuple[str, ...] = ()) -> Iterable[Tuple[Tuple[str, ...], str, Any]]:
    if isinstance(value, dict):
        for key in sorted(value):
            item = value[key]
            current = parts + (str(key),)
            yield current, str(key), item
            yield from _walk_json(item, current)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_json(item, parts + (str(index),))


def _safe_secret_reference(value: str) -> bool:
    stripped = value.strip()
    return not stripped or bool(SECRET_REFERENCE.fullmatch(stripped))


def _sensitive_key(key: str, fragments: Sequence[str]) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "_", key.lower()).strip("_")
    compact = normalized.replace("_", "")
    return any(
        normalized == fragment
        or normalized.endswith("_" + fragment)
        or compact == fragment.replace("_", "")
        or compact.endswith(fragment.replace("_", ""))
        for fragment in fragments
    )


def _unpinned_npx_dependency(server: Mapping[str, Any]) -> Optional[str]:
    command = server.get("command")
    args = server.get("args")
    if not isinstance(command, str) or Path(command).name not in {"npx", "pnpx", "bunx"}:
        return None
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        return "args"
    candidates = [item for item in args if item and not item.startswith("-")]
    if not candidates:
        return "args"
    package = candidates[0]
    if (
        package.startswith(("/", "./", "../"))
        or re.match(r"^[A-Za-z]:[\\/]", package)
        or package.endswith((".js", ".mjs", ".cjs"))
    ):
        return None
    if package.startswith("@"):
        separator = package.rfind("@")
        if separator <= 0:
            return package
        version = package[separator + 1 :]
    elif "@" in package:
        version = package.rsplit("@", 1)[1]
    else:
        return package
    return None if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version) else package


def _positive_permission_term(content: str, term: str) -> bool:
    lowered = content.lower()
    expected = term.lower()
    for match in re.finditer(re.escape(expected), lowered):
        prefix = lowered[max(0, match.start() - 48) : match.start()]
        window = lowered[max(0, match.start() - 48) : min(len(lowered), match.end() + 32)]
        if re.search(r"(?:\bnot\b|\bno\b|\bwithout\b|\bnever\b).{0,32}$", prefix):
            continue
        if re.search(r"(?:不|无|未|禁止|不得).{0,16}$", prefix):
            continue
        if re.search(r"hardcod(?:e|es|ed|ing).{0,24}(?:credential|secret|token|password)", window):
            continue
        return True
    return False


def _permission_document_evidence(index: RepositoryIndex, contract: Mapping[str, Any]) -> List[str]:
    candidates: List[str] = []
    for relative in sorted(index.files):
        lowered = relative.lower()
        if not _material_evidence(relative):
            continue
        if relative == "AGENTS.md" or (
            relative.startswith("docs/") and any(token in lowered for token in ("mcp", "permission", "security", "tool"))
        ):
            candidates.append(relative)
    groups = contract["mcp"]["permission_evidence_terms"]
    matched: List[str] = []
    found_groups = set()
    for relative in candidates[: int(contract["mcp"]["max_permission_docs"])]:
        content = index.read_text(relative)
        if content is None:
            continue
        lowered = content.lower()
        for name, terms in groups.items():
            if any(_positive_permission_term(lowered, str(term)) for term in terms):
                found_groups.add(name)
                matched.append(relative)
    return _deduplicate(matched, 12) if len(found_groups) == len(groups) else []


def _structured_permission_evidence(
    metadata: Mapping[str, Any], contract: Mapping[str, Any]
) -> Tuple[str, List[str], List[Dict[str, str]]]:
    metadata_path = str(contract["metadata_path"])
    dimensions = metadata.get("dimensions", {})
    raw = dimensions.get("tool_and_permission_boundary", {}) if isinstance(dimensions, dict) else {}
    policy = contract["mcp"]["structured_permission_boundary"]
    boundary = raw.get(policy["metadata_key"]) if isinstance(raw, dict) else None
    if boundary is None:
        return "missing", [], [
            _blocker(
                "missing_structured_permission_boundary",
                "MCP 存在但 readiness metadata 未声明结构化权限边界",
                metadata_path,
            )
        ]
    if not isinstance(boundary, dict):
        return "invalid", [metadata_path], [
            _blocker(
                "invalid_structured_permission_boundary",
                "结构化权限边界必须是对象",
                metadata_path,
            )
        ]
    required_true = policy["required_true_fields"]
    source_field = policy["credential_source_field"]
    allowed_sources = set(policy["allowed_credential_sources"])
    if any(boundary.get(field) is not True for field in required_true) or boundary.get(
        source_field
    ) not in allowed_sources:
        return "invalid", [metadata_path], [
            _blocker(
                "invalid_structured_permission_boundary",
                "结构化权限边界必须明确只读、审批和受支持的凭证来源",
                metadata_path,
            )
        ]
    return "pass", [metadata_path], []


def _evaluate_tools(
    index: RepositoryIndex,
    contract: Mapping[str, Any],
    metadata: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, List[str], List[Dict[str, str]]]:
    names = set(str(item).lower() for item in contract["mcp"]["config_names"])
    all_configs = sorted(
        relative
        for relative in index.files
        if _material_evidence(relative) and Path(relative).name.lower() in names
    )
    if not all_configs:
        return "not-applicable", [], []
    blockers: List[Dict[str, str]] = []
    blocker_limit = int(contract["scan"]["max_blockers_per_dimension"])
    omitted_blockers = 0

    def record_blocker(item: Dict[str, str]) -> None:
        nonlocal omitted_blockers
        if len(blockers) < blocker_limit - 1:
            blockers.append(item)
        else:
            omitted_blockers += 1

    def bounded_blockers() -> List[Dict[str, str]]:
        if omitted_blockers:
            return blockers + [
                _blocker("blockers_truncated", "另有 {} 个 MCP blocker 未展开".format(omitted_blockers))
            ]
        return list(blockers)

    parse_failed = False
    hardcoded_secret = False
    unpinned = False
    max_configs = int(contract["mcp"]["max_configs"])
    configs = all_configs[:max_configs]
    if len(all_configs) > max_configs:
        parse_failed = True
        record_blocker(
            _blocker(
                "mcp_config_limit_exceeded",
                "MCP 配置数量 {} 超过扫描上限 {}".format(len(all_configs), max_configs),
            )
        )
    fragments = [str(item) for item in contract["mcp"]["sensitive_key_fragments"]]
    for relative in configs:
        content = index.read_text(relative)
        if content is None:
            parse_failed = True
            record_blocker(_blocker("unreadable_mcp_config", "MCP 配置无法在扫描预算内读取", relative))
            continue
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, RecursionError):
            parse_failed = True
            record_blocker(_blocker("invalid_mcp_json", "MCP 配置不是有效 JSON", relative))
            continue
        if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
            parse_failed = True
            record_blocker(_blocker("invalid_mcp_schema", "MCP 配置必须包含 mcpServers 对象", relative))
            continue
        for parts, key, value in _walk_json(data):
            if not _sensitive_key(key, fragments) or value is None:
                continue
            if not isinstance(value, str) or not _safe_secret_reference(value):
                hardcoded_secret = True
                record_blocker(
                    _blocker(
                        "hardcoded_mcp_secret",
                        "MCP 敏感字段使用了非环境引用；值已脱敏",
                        "{}#{}".format(relative, ".".join(parts)),
                    )
                )
        servers = data["mcpServers"]
        for server_name in sorted(servers):
            server = servers[server_name]
            if not isinstance(server, dict):
                parse_failed = True
                record_blocker(
                    _blocker(
                        "invalid_mcp_server",
                        "MCP server 定义必须是对象",
                        "{}#mcpServers.{}".format(relative, server_name),
                    )
                )
                continue
            dependency = _unpinned_npx_dependency(server)
            if dependency is not None:
                unpinned = True
                record_blocker(
                    _blocker(
                        "unpinned_mcp_dependency",
                        "npx 类 MCP dependency 未固定版本",
                        "{}#mcpServers.{}.args".format(relative, server_name),
                    )
                )
    permission_refs = _permission_document_evidence(index, contract)
    structured_status, structured_refs, structured_blockers = _structured_permission_evidence(
        metadata or {}, contract
    )
    evidence = configs + structured_refs + permission_refs
    if hardcoded_secret:
        return "blocked", evidence, bounded_blockers()
    if parse_failed or unpinned:
        return "needs-review", evidence, bounded_blockers()
    for blocker in structured_blockers:
        record_blocker(blocker)
    if structured_status == "invalid":
        return "needs-review", evidence, bounded_blockers()
    if structured_status == "missing":
        return "partial", evidence, bounded_blockers()
    if not permission_refs:
        record_blocker(_blocker("missing_permission_boundary", "MCP 存在但未发现只读、审批和凭证边界证据"))
        return "partial", evidence, bounded_blockers()
    return "pass", evidence, bounded_blockers()


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
