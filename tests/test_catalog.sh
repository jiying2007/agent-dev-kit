#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CATALOG_OUT="$TMP_DIR/catalog.md"
bash "$ROOT_DIR/scripts/devkit.sh" catalog build --out "$CATALOG_OUT"

[[ -f "$CATALOG_OUT" ]] || {
  echo "[FAIL] catalog file not generated" >&2
  exit 1
}

grep -q '^# Agent and Skill Catalog$' "$CATALOG_OUT" || {
  echo "[FAIL] catalog header missing" >&2
  exit 1
}

grep -q '`requirements-analyst`' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing known agent" >&2
  exit 1
}

grep -q '| `hardware-debugger` | 硬件故障定位、oops 分析和板级调试证据整理 | `agents/hardware-debugger/AGENTS.md` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing agent description" >&2
  exit 1
}

grep -q '`adk-incident-rca-report`' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing optional skill" >&2
  exit 1
}

grep -q '^## Agent Contract Matrix$' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing agent contract matrix" >&2
  exit 1
}

grep -q '| `requirements-analyst` | 需求边界, 验收标准 | 代码实现, 发布操作 | architecture-planner, test-validation-engineer, code-review-governor | adk-requirements-triage, adk-task-breakdown |' "$CATALOG_OUT" || {
  echo "[FAIL] agent contract matrix missing requirements-analyst" >&2
  exit 1
}

grep -q '| `adk-delivery-gate` | agent-dev-kit 通用资产生产交付门禁 | core, embedded-fullstack | `code-review-governor` | `adk-verification-before-completion` | `workflows/adk-delivery-gate/WORKFLOW.md` |' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing workflow contract" >&2
  exit 1
}

grep -q '^## Workflow Matrix$' "$CATALOG_OUT" || {
  echo "[FAIL] catalog missing workflow matrix" >&2
  exit 1
}

grep -q '| `feature-delivery` | core, embedded-fullstack | low | `requirements-analyst` | `adk-requirements-triage` |' "$CATALOG_OUT" || {
  echo "[FAIL] workflow matrix missing feature-delivery" >&2
  exit 1
}

FIND_AGENT_OUTPUT="$(bash "$ROOT_DIR/scripts/devkit.sh" catalog find --type agent --keyword 硬件)"
echo "$FIND_AGENT_OUTPUT" | grep -q 'hardware-debugger' || {
  echo "[FAIL] find command missing expected agent" >&2
  exit 1
}

FIND_OUTPUT="$(bash "$ROOT_DIR/scripts/devkit.sh" catalog find --type skill --keyword bring-up)"
echo "$FIND_OUTPUT" | grep -q 'adk-driver-bringup-checklist' || {
  echo "[FAIL] find command missing expected skill" >&2
  exit 1
}

FIND_WORKFLOW_OUTPUT="$(bash "$ROOT_DIR/scripts/devkit.sh" catalog find --type workflow --keyword 交付门禁)"
echo "$FIND_WORKFLOW_OUTPUT" | grep -q 'adk-delivery-gate' || {
  echo "[FAIL] find command missing expected workflow" >&2
  exit 1
}

OFF_ROOT_OUTPUT="$(cd "$TMP_DIR" && bash "$ROOT_DIR/scripts/devkit.sh" catalog find --type skill --keyword bring-up)"
echo "$OFF_ROOT_OUTPUT" | grep -q 'adk-driver-bringup-checklist' || {
  echo "[FAIL] canonical catalog CLI lost ADK root outside repository cwd" >&2
  exit 1
}

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import difflib
import sys
from pathlib import Path

from agent_dev_kit.catalog_contract import (
    catalog_markdown,
    routing_matrix_markdown,
    workflow_matrix_markdown,
)
from agent_dev_kit.model import Manifest

root = Path(sys.argv[1]).resolve()
manifest = Manifest.load(root)

cli_source = (root / "src/agent_dev_kit/cli.py").read_text(encoding="utf-8")
runtime_source = (root / "src/agent_dev_kit/cli_runtime.py").read_text(encoding="utf-8")
assert "from .catalog_contract" not in cli_source, "public CLI reintroduced direct catalog dependency"
assert "run_catalog," in cli_source, "public CLI must consume the runtime catalog port"
assert "from .catalog_contract import main as catalog_main" in runtime_source
assert "def run_catalog(" in runtime_source

projections = (
    ("docs/agent-skill-catalog.md", catalog_markdown),
    ("docs/workflow-contract-matrix.md", workflow_matrix_markdown),
    ("docs/reference/skill-routing-matrix.md", routing_matrix_markdown),
)
failures = 0
for relative, render in projections:
    actual = (root / relative).read_text(encoding="utf-8")
    expected = render(manifest)
    if actual == expected:
        continue
    failures += 1
    print(f"[FAIL] generated projection drift: {relative}", file=sys.stderr)
    diff = list(
        difflib.unified_diff(
            actual.splitlines(),
            expected.splitlines(),
            fromfile=f"{relative}:committed",
            tofile=f"{relative}:generated",
            lineterm="",
        )
    )
    for line in diff[:120]:
        print(line, file=sys.stderr)

if failures:
    raise SystemExit(1)
PY

echo "[PASS] catalog"
