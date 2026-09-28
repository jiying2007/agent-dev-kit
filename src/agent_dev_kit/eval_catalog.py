"""Read-only integrity audit for declared evaluation suites.

This module does not execute a grader, model, tool, or runtime adapter.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, Mapping

CATALOG_PATH = "manifests/eval_suites.json"
GUARDRAIL_SUITE = "governance-eval-guardrail-regression-dataset"
GUARDRAIL_COLUMNS = ("case_id", "category", "expected", "input")
GUARDRAIL_OUTCOMES = {
    "positive": "trigger",
    "negative": "do-not-trigger",
    "adversarial": "trigger",
    "borderline": "analyze-with-boundary",
}


ID_PATTERN = re.compile(r"[a-z][a-z0-9-]*\Z")
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\Z")
MAX_CATALOG_BYTES = 1024 * 1024
MAX_GUARDRAIL_BYTES = 256 * 1024
MAX_DATASET_BYTES = 1024 * 1024


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _read_bounded(path: Path, limit: int) -> str:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("source exceeded byte budget")
    return raw.decode("utf-8")


def _safe_dataset(root: Path, value: Any, issues: list[str], label: str) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value:
        issues.append(f"{label}: invalid dataset_path")
        return None
    parts = value.split("/")
    if value.startswith("/") or any(part in ("", ".", "..") for part in parts):
        issues.append(f"{label}: dataset_path must stay within the repository")
        return None
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink():
            issues.append(f"{label}: symlink dataset_path is forbidden")
            return None
    if not path.is_file():
        issues.append(f"{label}: dataset_path is missing")
        return None
    if root not in path.resolve().parents:
        issues.append(f"{label}: dataset_path escapes the repository")
        return None
    return path


def _fixture_map(value: Any, issues: list[str], label: str) -> dict[str, tuple[str, str]]:
    if not isinstance(value, list) or not value:
        issues.append(f"{label}: fixtures must be a non-empty list")
        return {}
    fixtures: dict[str, tuple[str, str]] = {}
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            issues.append(f"{label}: fixture[{index}] must be an object")
            continue
        if set(item) != {"id", "input", "expected"}:
            issues.append(f"{label}: fixture[{index}] has unsupported fields")
            continue
        case_id = item.get("id")
        expected = item.get("expected")
        prompt = item.get("input")
        if not isinstance(case_id, str) or not ID_PATTERN.fullmatch(case_id):
            issues.append(f"{label}: fixture[{index}] has invalid id")
            continue
        if case_id in fixtures:
            issues.append(f"{label}: duplicate fixture id {case_id}")
            continue
        if not isinstance(prompt, str) or not prompt.strip():
            issues.append(f"{label}: fixture {case_id} has empty input")
            continue
        if not isinstance(expected, str) or not expected:
            issues.append(f"{label}: fixture {case_id} has invalid expected result")
            continue
        fixtures[case_id] = (expected, prompt)
    return fixtures


def _validate_graders(value: Any, issues: list[str], label: str) -> None:
    if not isinstance(value, list) or not value:
        issues.append(f"{label}: graders must be a non-empty list")
        return
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            issues.append(f"{label}: grader[{index}] must be an object")
            continue
        if set(item) != {"name", "type", "threshold"}:
            issues.append(f"{label}: grader[{index}] has unsupported fields")
            continue
        name = item.get("name")
        threshold = item.get("threshold")
        if not isinstance(name, str) or not ID_PATTERN.fullmatch(name.replace("_", "-")):
            issues.append(f"{label}: grader[{index}] has invalid name")
        elif name in names:
            issues.append(f"{label}: duplicate grader name {name}")
        else:
            names.add(name)
        if item.get("type") != "deterministic":
            issues.append(f"{label}: grader[{index}] must declare deterministic type")
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            issues.append(f"{label}: grader[{index}] has invalid threshold")


def _validate_guardrail_dataset(
    content: str, fixtures: Mapping[str, tuple[str, str]], issues: list[str]
) -> int:
    label = GUARDRAIL_SUITE
    try:
        with io.StringIO(content, newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t", strict=True)
            if tuple(reader.fieldnames or ()) != GUARDRAIL_COLUMNS:
                issues.append(f"{label}: TSV header must be {GUARDRAIL_COLUMNS}")
                return 0
            rows = list(reader)
    except csv.Error:
        issues.append(f"{label}: TSV cannot be parsed")
        return 0

    cases: dict[str, tuple[str, str]] = {}
    categories: set[str] = set()
    for index, row in enumerate(rows):
        case_id = row.get("case_id")
        category = row.get("category")
        expected = row.get("expected")
        if None in row or not isinstance(case_id, str) or not ID_PATTERN.fullmatch(case_id):
            issues.append(f"{label}: TSV row {index + 2} has invalid columns or case_id")
            continue
        if case_id in cases:
            issues.append(f"{label}: duplicate TSV case_id {case_id}")
            continue
        if category not in GUARDRAIL_OUTCOMES or expected != GUARDRAIL_OUTCOMES[category]:
            issues.append(f"{label}: TSV case {case_id} has invalid category/expected pair")
        prompt = row.get("input")
        if not isinstance(prompt, str) or not prompt.strip():
            issues.append(f"{label}: TSV case {case_id} has empty input")
        cases[case_id] = (str(expected), str(prompt))
        categories.add(str(category))
    if categories != set(GUARDRAIL_OUTCOMES):
        issues.append(f"{label}: positive, negative, adversarial and borderline cases are required")
    if cases != fixtures:
        issues.append(f"{label}: TSV cases and manifest fixtures disagree")
    return len(rows)


def audit_eval_catalog(root: Path) -> dict[str, Any]:
    """Validate static suite declarations without claiming an evaluation run."""
    root = root.resolve()
    issues: list[str] = []
    catalog_path = root / CATALOG_PATH
    catalog_text: str | None = None
    try:
        if (root / "manifests").is_symlink() or catalog_path.is_symlink():
            raise ValueError("linked catalog is forbidden")
        catalog_text = _read_bounded(catalog_path, MAX_CATALOG_BYTES)
        catalog = json.loads(catalog_text, object_pairs_hook=_unique_json_object)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        catalog = None
        issues.append("eval catalog is missing, linked, oversized or invalid JSON")
    if isinstance(catalog, Mapping) and (
        not isinstance(catalog.get("schema_version"), str)
        or not VERSION_PATTERN.fullmatch(catalog["schema_version"])
    ):
        issues.append("eval catalog schema_version is missing or invalid")
    suites = catalog.get("suites") if isinstance(catalog, Mapping) else None
    if not isinstance(suites, list) or not suites:
        issues.append("eval catalog suites must be a non-empty list")
        suites = []

    seen: set[str] = set()
    guardrail_count = 0
    guardrail_rows = 0
    alignment_checked: list[str] = []
    suite_reports: list[dict[str, Any]] = []
    for index, suite in enumerate(suites):
        if not isinstance(suite, Mapping):
            issues.append(f"suite[{index}] must be an object")
            continue
        suite_id = suite.get("id")
        if not isinstance(suite_id, str) or not ID_PATTERN.fullmatch(suite_id):
            issues.append(f"suite[{index}] has invalid id")
            continue
        if suite_id in seen:
            issues.append(f"duplicate suite id {suite_id}")
            continue
        seen.add(suite_id)
        for field in ("category", "owner", "goal", "minimum_gate"):
            if not isinstance(suite.get(field), str) or not suite[field].strip():
                issues.append(f"{suite_id}: {field} must be non-empty")
        dataset = _safe_dataset(root, suite.get("dataset_path"), issues, suite_id)
        dataset_text: str | None = None
        dataset_sha256: str | None = None
        if dataset is not None:
            try:
                limit = MAX_GUARDRAIL_BYTES if suite_id == GUARDRAIL_SUITE else MAX_DATASET_BYTES
                dataset_text = _read_bounded(dataset, limit)
                dataset_sha256 = hashlib.sha256(dataset_text.encode("utf-8")).hexdigest()
            except (OSError, UnicodeError, ValueError):
                issues.append(f"{suite_id}: dataset cannot be read within byte budget")
        before_fixtures = len(issues)
        fixtures = _fixture_map(suite.get("fixtures"), issues, suite_id)
        fixture_structure_valid = len(issues) == before_fixtures
        _validate_graders(suite.get("graders"), issues, suite_id)
        alignment_status = "not-checked"
        if suite_id == GUARDRAIL_SUITE:
            guardrail_count += 1
            if dataset_text is not None:
                before_alignment = len(issues)
                guardrail_rows = _validate_guardrail_dataset(dataset_text, fixtures, issues)
                alignment_checked.append(suite_id)
                alignment_status = "pass" if fixture_structure_valid and len(issues) == before_alignment else "fail"
        suite_reports.append({
            "id": suite_id,
            "dataset_path": suite.get("dataset_path") if isinstance(suite.get("dataset_path"), str) else None,
            "dataset_present": dataset is not None,
            "dataset_readable": dataset_text is not None,
            "dataset_sha256": dataset_sha256,
            "fixture_count": len(fixtures),
            "fixture_dataset_alignment": alignment_status,
            "grader_executed": False,
            "runtime_eval_executed": False,
        })
    if guardrail_count != 1:
        issues.append("exactly one guardrail regression suite is required")

    return {
        "schema": "adk-eval-catalog-audit/v1",
        "status": "fail" if issues else "pass",
        "catalog_valid": not issues,
        "catalog_sha256": hashlib.sha256(catalog_text.encode("utf-8")).hexdigest()
        if catalog_text is not None else None,
        "snapshot_atomic": False,
        "runtime_eval_executed": False,
        "release_authorized": False,
        "suite_count": len(suites),
        "guardrail_case_count": guardrail_rows,
        "dataset_fixture_alignment_scope": alignment_checked,
        "contract_only_suite_count": len(suite_reports) - len(alignment_checked),
        "suite_reports": suite_reports,
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit ADK evaluation catalog integrity")
    parser.add_argument("--root", default=".")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    result = audit_eval_catalog(Path(args.root))
    print(json.dumps(result, ensure_ascii=False, sort_keys=args.summary_json, indent=None if args.summary_json else 2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
