#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -f "${ADK_TEST_SUITE_DIR:-/nonexistent}/validate-summary.json" ]]; then
  summary="$(<"${ADK_TEST_SUITE_DIR}/validate-summary.json")"
else
  summary="$("$ROOT_DIR/scripts/validate-assets.sh" --strict --summary-json)"
fi
echo "$summary" | grep -q '"workflows":7' || {
  echo "[FAIL] validate summary did not report seven workflows" >&2
  exit 1
}

core_summary="$("$ROOT_DIR/scripts/check-workflow-closure.sh" --profile core --summary-json)"
echo "$core_summary" | grep -q '"checked":4' || {
  echo "[FAIL] core workflow closure did not check four applicable workflows" >&2
  echo "$core_summary" >&2
  exit 1
}

embedded_summary="$("$ROOT_DIR/scripts/check-workflow-closure.sh" --profile embedded-fullstack --summary-json)"
echo "$embedded_summary" | grep -q '"checked":4' || {
  echo "[FAIL] embedded workflow closure did not check four applicable workflows" >&2
  echo "$embedded_summary" >&2
  exit 1
}

release_summary="$("$ROOT_DIR/scripts/check-workflow-closure.sh" --profile release-hardening --summary-json)"
echo "$release_summary" | grep -q '"checked":1' || {
  echo "[FAIL] release-hardening workflow closure did not check one applicable workflow" >&2
  echo "$release_summary" >&2
  exit 1
}

[[ -f "$ROOT_DIR/docs/workflow-contract-matrix.md" ]] || {
  echo "[FAIL] standalone workflow contract matrix missing" >&2
  exit 1
}

grep -q '| `release-hardening` | release-hardening | medium | `build-release-engineer` | `adk-release-versioning` |' "$ROOT_DIR/docs/workflow-contract-matrix.md" || {
  echo "[FAIL] standalone workflow matrix missing release-hardening risk contract" >&2
  exit 1
}

if "$ROOT_DIR/scripts/check-workflow-closure.sh" --profile research-intake >/tmp/adk-workflow-contract-research.out 2>&1; then
  echo "[FAIL] research-intake accepted its optional workflow without explicit selection" >&2
  exit 1
fi

grep -q "missing skill in selected profiles: adk-external-practice-absorption" /tmp/adk-workflow-contract-research.out || {
  echo "[FAIL] research-intake failure did not explain the missing optional skill" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-workflow-closure.sh" \
  --profile research-intake \
  --with-optional-skill adk-external-practice-absorption >/dev/null

grep -q '| `external-practice-absorption` | research-intake | low | `external-practice-curator` | `adk-external-practice-absorption` |' "$ROOT_DIR/docs/workflow-contract-matrix.md" || {
  echo "[FAIL] standalone workflow matrix missing external-practice optional contract" >&2
  exit 1
}

echo "[PASS] workflow contract"
