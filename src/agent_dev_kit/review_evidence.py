"""Validate owner-delegated AI review records; never generate semantic verdicts.

This is the shared source-review validator for the existing lifecycle, Harness,
and downstream evidence consumers. Digest validation does not authenticate a
declared reviewer identity, execute a provider, prove field observations, or
authorize a release. Historical consumers must compare source targets and patch
digests with independently verified original commits and retained Git diffs.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from . import strict_json

SCHEMA = "adk-review-evidence/v1"
POLICY_SCHEMA = "adk-review-policy/v1"
POLICY_PATH = ".adk/review-policy.json"
SCOPES = frozenset(("source-change", "harness-source", "effect-value-review", "longitudinal-review"))
MAX_RECORD_BYTES = 256 * 1024
MAX_POLICY_BYTES = 16 * 1024
MAX_REFERENCE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_REFERENCES = 64
TARGET_PATCH_PATH = "evidence/original.patch"
HARNESS_SOURCE_PATHS = frozenset((
    "src/agent_dev_kit/readiness.py",
    "src/agent_dev_kit/readiness_tools.py",
    "manifests/harness_readiness_contracts.json",
))
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_IDENTITY = re.compile(r"[a-z0-9][a-z0-9._/-]{0,127}\Z")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z\Z")


class ReviewEvidenceError(ValueError):
    """Sanitized failure of a review identity, scope, or evidence boundary."""


def _require(condition: Any, message: str) -> None:
    if not condition:
        raise ReviewEvidenceError(message)


def _identity(value: Any) -> bool:
    return isinstance(value, str) and _IDENTITY.fullmatch(value) is not None


def _digest(value: Any) -> bool:
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _timestamp(value: Any) -> datetime:
    _require(isinstance(value, str) and _TIME.fullmatch(value), "review timestamp must be canonical UTC")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewEvidenceError("review timestamp is invalid") from exc


def _no_symlinks(path: Path) -> None:
    try:
        _require(not any(part.is_symlink() for part in (path,) + tuple(path.parents)),
                 "review paths must not contain symlinks")
    except OSError as exc:
        raise ReviewEvidenceError("review path ancestry cannot be checked") from exc


def _root(path: Path) -> Path:
    value = path.expanduser().absolute()
    _require(".." not in value.parts, "review root must be canonical")
    _no_symlinks(value)
    _require(value.is_dir(), "review root must be a directory")
    return value


def _relative(root: Path, value: Any) -> Path:
    _require(isinstance(value, str) and 0 < len(value) <= 512 and "\\" not in value
             and all(ord(char) >= 32 and not (127 <= ord(char) <= 159 or 0xD800 <= ord(char) <= 0xDFFF)
                     for char in value),
             "review reference path is invalid")
    relative = PurePosixPath(value)
    _require(not relative.is_absolute() and relative.as_posix() == value
             and not any(part in (".", "..") for part in relative.parts)
             and value != ".", "review reference path must be canonical and relative")
    path = root.joinpath(*relative.parts)
    _no_symlinks(path)
    return path


def _bytes(path: Path, maximum: int) -> bytes:
    try:
        return strict_json.read_bytes(path, max_bytes=maximum, regular_only=True)
    except strict_json.StrictJSONError as exc:
        raise ReviewEvidenceError("review input is unsafe, unreadable, or exceeds its byte budget") from exc


def _object(raw: bytes, maximum: int) -> dict[str, Any]:
    try:
        value = strict_json.loads(raw, max_bytes=maximum)
    except strict_json.StrictJSONError as exc:
        raise ReviewEvidenceError("review input is not bounded unambiguous JSON") from exc
    if not isinstance(value, dict):
        raise ReviewEvidenceError("review input must be a JSON object")
    return value


def validator_fingerprints() -> dict[str, str]:
    """Fingerprint actual validator dependencies, not a caller's lookalike tree."""
    from . import readiness_evidence

    modules = (("review_evidence", Path(__file__)),
               ("strict_json", Path(strict_json.__file__)),
               ("readiness_evidence", Path(readiness_evidence.__file__)))
    values = {}
    for name, path in modules:
        _no_symlinks(path.absolute())
        values["src/agent_dev_kit/" + name + ".py"] = hashlib.sha256(
            _bytes(path, MAX_REFERENCE_BYTES)).hexdigest()
    return values


def _policy(root: Path, expected_scope: str, expected_sha256: Any, now: datetime) -> dict[str, Any]:
    path = _relative(root, POLICY_PATH)
    raw = _bytes(path, MAX_POLICY_BYTES)
    _require(_digest(expected_sha256) and hashlib.sha256(raw).hexdigest() == expected_sha256,
             "review policy digest does not match")
    policy = _object(raw, MAX_POLICY_BYTES)
    _require(set(policy) == {"schema", "mode", "owner", "allowed_scopes", "authorization"}
             and policy.get("schema") == POLICY_SCHEMA and policy.get("mode") == "owner-delegated-ai"
             and _identity(policy.get("owner")), "repository has no valid delegated review policy")
    scopes = policy.get("allowed_scopes")
    _require(isinstance(scopes, list) and scopes and all(isinstance(scope, str) for scope in scopes)
             and len(scopes) == len(set(scopes)) and set(scopes) <= SCOPES
             and expected_scope in scopes, "review scope is not delegated by this repository")
    authorization = policy.get("authorization")
    if (not isinstance(authorization, dict) or set(authorization) != {"path", "sha256", "granted_at"}
            or not _digest(authorization.get("sha256"))):
        raise ReviewEvidenceError("review authorization record is invalid")
    granted = _timestamp(authorization["granted_at"])
    _require(granted <= now, "review authorization is future-dated")
    directive = _bytes(_relative(root, authorization["path"]), MAX_POLICY_BYTES)
    _require(directive.strip() and hashlib.sha256(directive).hexdigest() == authorization["sha256"],
             "review authorization digest does not match")
    return policy


def _findings(value: Any) -> None:
    _require(isinstance(value, list) and len(value) <= 64, "review findings exceed their count budget")
    seen = set()
    for finding in value:
        _require(isinstance(finding, dict) and set(finding) == {"id", "severity", "disposition", "reason"}
                 and _identity(finding.get("id")) and finding["id"] not in seen,
                 "review finding identity is invalid or repeated")
        seen.add(finding["id"])
        _require(finding["severity"] in ("blocker", "major", "minor", "question", "cannot-verify-from-diff")
                 and finding["disposition"] in ("fixed", "accepted-risk", "not-applicable", "open")
                 and isinstance(finding["reason"], str) and 0 < len(finding["reason"].strip()) <= 2048,
                 "review finding disposition or reason is invalid")
        _require(not (finding["severity"] in ("blocker", "major") and finding["disposition"] == "open"),
                 "review has an unresolved blocker or major")


def _references(root: Path, record_path: Path, record: dict[str, Any]) -> None:
    total = 0
    seen = set()
    source_paths = set()
    original_patch_bound = False
    for group in ("sources", "evidence"):
        refs = record.get(group)
        if not isinstance(refs, list) or not refs:
            raise ReviewEvidenceError("review requires source and execution/review evidence references")
        for ref in refs:
            _require(isinstance(ref, dict) and set(ref) == {"base", "path", "sha256"}
                     and ref.get("base") in ("repository", "record") and _digest(ref.get("sha256")),
                     "review reference is invalid")
            base = root if ref["base"] == "repository" else record_path.parent
            path = _relative(base, ref["path"])
            _require(path != record_path, "review outputs cannot be their own source evidence")
            _require(path not in seen, "review references must be unique")
            seen.add(path)
            _require(len(seen) <= MAX_REFERENCES, "review reference count exceeds its budget")
            raw = _bytes(path, MAX_REFERENCE_BYTES)
            _require(group != "evidence" or raw, "review evidence references cannot be empty")
            total += len(raw)
            _require(total <= MAX_TOTAL_BYTES, "review references exceed their total byte budget")
            _require(hashlib.sha256(raw).hexdigest() == ref["sha256"], "review source or evidence digest does not match")
            if group == "sources" and ref["base"] == "repository":
                source_paths.add(ref["path"])
            if (record["scope"] == "source-change" and group == "sources" and ref["base"] == "record"
                    and ref["path"] == TARGET_PATCH_PATH):
                _require(ref["sha256"] == record["target"]["original_patch_sha256"]
                         and raw.startswith(b"diff --git "), "review original patch identity or format does not match")
                original_patch_bound = True
    if record["scope"] == "source-change":
        _require(original_patch_bound, "source review must bind its retained complete original patch")
    if record["scope"] == "harness-source":
        _require(source_paths >= HARNESS_SOURCE_PATHS, "Harness review does not bind its evaluator and contract sources")


def validate_review(
    root: Path,
    record_path: Path,
    *,
    expected_subject: str,
    expected_scope: str,
    now: datetime | None = None,
    policy_root: Path | None = None,
) -> dict[str, Any]:
    """Validate a scoped record and return its verified fields and byte identity.

    ``root`` owns the record and its references. An explicitly supplied
    ``policy_root`` permits downstream consumers to reuse one pinned ADK policy.
    ``now`` exists for deterministic tests; production callers use the real clock.
    """
    root = _root(root)
    authority_root = _root(policy_root) if policy_root is not None else root
    _require(isinstance(expected_scope, str) and expected_scope in SCOPES and _identity(expected_subject),
             "expected review subject or scope is invalid")
    if record_path.is_absolute():
        try:
            relative = record_path.relative_to(root).as_posix()
        except ValueError as exc:
            raise ReviewEvidenceError("review record must be inside its repository") from exc
    else:
        relative = record_path.as_posix()
    record_path = _relative(root, relative)
    raw = _bytes(record_path, MAX_RECORD_BYTES)
    record = _object(raw, MAX_RECORD_BYTES)
    required = {"schema", "subject_id", "scope", "author_id", "reviewer", "reviewed_at",
                "evidence_completed_at", "verdicts", "findings", "limitations", "policy_sha256",
                "validator_sha256", "sources", "evidence"}
    _require(required <= set(record) and set(record) <= required | {"owner", "target", "dimension_ids"},
             "review record fields are incomplete or unsupported")
    _require(record["schema"] == SCHEMA and record["subject_id"] == expected_subject
             and record["scope"] == expected_scope, "review record subject or scope does not match")
    current = now if now is not None else datetime.now(timezone.utc)
    _require(isinstance(current, datetime) and current.tzinfo is not None and current.utcoffset() is not None,
             "review evaluation time must have a timezone")
    policy = _policy(authority_root, expected_scope, record["policy_sha256"], current)
    _require(record.get("owner", policy["owner"]) == policy["owner"], "review owner differs from delegated responsibility")
    reviewer = record["reviewer"]
    _require(isinstance(reviewer, dict) and set(reviewer) == {"id", "kind", "independence"}
             and _identity(reviewer.get("id")) and reviewer.get("kind") == "ai"
             and reviewer.get("independence") == "independent" and _identity(record["author_id"])
             and reviewer["id"] != record["author_id"], "review requires an independent, identified AI reviewer")
    reviewed = _timestamp(record["reviewed_at"])
    completed = _timestamp(record["evidence_completed_at"])
    _require(_timestamp(policy["authorization"]["granted_at"]) <= reviewed <= current
             and completed <= reviewed, "review must follow authorization and evidence, without future dating")
    _require(record["verdicts"] == {"spec": "pass", "quality": "pass"}, "review requires separate Spec and Quality pass verdicts")
    _findings(record["findings"])
    limitations = record["limitations"]
    _require(isinstance(limitations, list) and 1 <= len(limitations) <= 16
             and all(isinstance(item, str) and 0 < len(item.strip()) <= 2048 for item in limitations),
             "review must retain its bounded limitations")
    _require(record["validator_sha256"] == validator_fingerprints(), "review validator source identity changed")
    if expected_scope == "source-change":
        target = record.get("target")
        _require(isinstance(target, dict) and set(target) == {"base_commit", "head_commit", "original_patch_sha256"}
                 and all(isinstance(target[field], str) and _COMMIT.fullmatch(target[field])
                         for field in ("base_commit", "head_commit"))
                 and _digest(target["original_patch_sha256"]),
                 "source review requires exact original commits and retained patch identity")
    elif expected_scope == "harness-source":
        from .readiness_evidence import EXPECTED_DIMENSIONS

        _require(expected_subject == "harness-readiness" and record.get("owner") == policy["owner"]
                 and isinstance(record.get("dimension_ids"), list)
                 and len(record["dimension_ids"]) == len(EXPECTED_DIMENSIONS)
                 and all(isinstance(item, str) for item in record["dimension_ids"])
                 and set(record["dimension_ids"]) == set(EXPECTED_DIMENSIONS),
                 "Harness review must cover exactly all seven dimensions for its owner")
    _references(root, record_path, record)
    return dict(record, status="pass", record_sha256=hashlib.sha256(raw).hexdigest(),
                review_policy_sha256=record["policy_sha256"], review_scope=expected_scope,
                human_review_performed=False, field_evidence_verified=False,
                provider_execution_performed=False, product_release_authorized=False)
