#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

CATALOG_OUT="$TMP_DIR/catalog.md"
"$ROOT_DIR/scripts/catalog-assets.sh" build --out "$CATALOG_OUT"

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

FIND_AGENT_OUTPUT="$("$ROOT_DIR/scripts/catalog-assets.sh" find --type agent --keyword 硬件)"
echo "$FIND_AGENT_OUTPUT" | grep -q 'hardware-debugger' || {
  echo "[FAIL] find command missing expected agent" >&2
  exit 1
}

FIND_OUTPUT="$("$ROOT_DIR/scripts/catalog-assets.sh" find --type skill --keyword bring-up)"
echo "$FIND_OUTPUT" | grep -q 'adk-driver-bringup-checklist' || {
  echo "[FAIL] find command missing expected skill" >&2
  exit 1
}

FIND_WORKFLOW_OUTPUT="$("$ROOT_DIR/scripts/catalog-assets.sh" find --type workflow --keyword 交付门禁)"
echo "$FIND_WORKFLOW_OUTPUT" | grep -q 'adk-delivery-gate' || {
  echo "[FAIL] find command missing expected workflow" >&2
  exit 1
}

echo "[PASS] catalog"
