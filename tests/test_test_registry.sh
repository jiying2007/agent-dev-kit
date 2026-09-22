#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
tests_dir = root / "tests"
runner_path = tests_dir / "run_all.sh"
workflow_dir = root / ".github" / "workflows"

runner = runner_path.read_text(encoding="utf-8")


def extract_array(name: str) -> set[str]:
    match = re.search(rf"(?ms)^{name}=\(\n(.*?)^\)", runner)
    if match is None:
        raise AssertionError(f"missing {name} array in {runner_path.relative_to(root)}")
    return set(
        re.findall(
            r"(?m)^\s*(test_[A-Za-z0-9_.-]+\.sh)\s*$",
            match.group(1),
        )
    )


full_tests = extract_array("TESTS")
quick_tests = extract_array("QUICK_TESTS")
assert quick_tests <= full_tests, sorted(quick_tests - full_tests)

workflow_text = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted(workflow_dir.glob("*.y*ml"))
)
workflow_tests = set(
    re.findall(r"\btests/(test_[A-Za-z0-9_.-]+\.sh)\b", workflow_text)
)
filesystem_tests = {path.name for path in tests_dir.glob("test_*.sh")}

owned_tests = full_tests | workflow_tests
unowned = sorted(filesystem_tests - owned_tests)
missing = sorted((full_tests | quick_tests | workflow_tests) - filesystem_tests)

assert not unowned, f"unowned shell tests: {unowned}"
assert not missing, f"registered shell tests missing from filesystem: {missing}"
assert "test_test_registry.sh" in full_tests
assert "test_test_registry.sh" in quick_tests

print(
    "[PASS] shell test registry closed: "
    f"files={len(filesystem_tests)} full={len(full_tests)} "
    f"quick={len(quick_tests)} workflow_only={len(workflow_tests - full_tests)}"
)
PY
