"""Bounded repository evidence collection for Harness readiness."""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


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
