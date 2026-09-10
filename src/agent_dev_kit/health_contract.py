from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .domain.manifest import load_contract


REQUIRED_DIRS = ("agents", "skills", "optional-skills", "scripts", "tests", "docs", "templates")
REQUIRED_FILES = ("manifest.json", "README.md", "CONTEXT.md")
REQUIRED_TOOLS = ("bash", "git", "tar", "grep", "sed", "awk", "rg", "python3")


def _run(root: Path, argv: list[str]) -> bool:
    completed = subprocess.run(
        argv,
        cwd=root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def check_structure(root: Path) -> list[str]:
    failures: list[str] = []
    for relative in REQUIRED_DIRS:
        if not (root / relative).is_dir():
            failures.append(f"missing directory: {relative}")
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            failures.append(f"missing file: {relative}")
    if (root / "manifest.yaml").exists():
        failures.append("legacy manifest.yaml must not exist")
    return failures


def check_dependencies() -> list[str]:
    return [f"missing dependency: {tool}" for tool in REQUIRED_TOOLS if shutil.which(tool) is None]


def check_configuration(root: Path) -> list[str]:
    try:
        contract = load_contract(root)
        contract.verify()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"manifest contract failed: {exc}"]
    if not _run(root, [sys.executable, "-m", "agent_dev_kit.validation_contract", "--root", str(root), "--quick", "--summary-json"]):
        return ["asset validation contract failed"]
    return []


def check_tests(root: Path, run_tests: bool) -> list[str]:
    tests = list((root / "tests").glob("test_*.sh")) if (root / "tests").is_dir() else []
    if not tests:
        return ["no shell regression tests found"]
    if run_tests and not _run(root, ["bash", "tests/run_all.sh"]):
        return ["regression suite failed"]
    return []


def check_quality(root: Path) -> list[str]:
    checks = (
        ["bash", "scripts/quality-gate-check.sh", "check-all"],
        ["bash", "scripts/check-runtime-boundary.sh"],
        ["bash", "scripts/check-workflow-closure.sh"],
    )
    failures: list[str] = []
    for argv in checks:
        if not _run(root, list(argv)):
            failures.append("quality contract failed: " + " ".join(argv[1:]))
    return failures


def run_health(root: Path, *, run_tests: bool = False) -> dict[str, Any]:
    root = root.resolve()
    groups = {
        "structure": check_structure(root),
        "dependencies": check_dependencies(),
        "configuration": check_configuration(root),
        "tests": check_tests(root, run_tests),
        "quality": check_quality(root),
    }
    status = "pass" if all(not items for items in groups.values()) else "fail"
    return {
        "schema_version": 2,
        "status": status,
        "structure": "pass" if not groups["structure"] else "fail",
        "dependencies": "pass" if not groups["dependencies"] else "fail",
        "configuration": "pass" if not groups["configuration"] else "fail",
        "tests": "pass" if not groups["tests"] else "fail",
        "quality": "pass" if not groups["quality"] else "fail",
        "failures": [item for values in groups.values() for item in values],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run canonical ADK health checks")
    parser.add_argument("--root", default=".")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    result = run_health(Path(args.root), run_tests=args.run_tests)
    if args.summary_json:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    elif result["status"] == "pass":
        print("[PASS] canonical ADK health checks passed")
    else:
        for failure in result["failures"]:
            print(f"[FAIL] {failure}", file=sys.stderr)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
