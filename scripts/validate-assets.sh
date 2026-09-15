#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
PYTHON_BIN="${ADK_PYTHON_BIN:-python3}"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/validate-assets.sh [--strict] [--quick] [--summary-json]

Options:
  --strict        启用严格校验与治理门禁
  --quick         快速预检，跳过跨 profile / workflow 深度校验
  --summary-json  输出低 token compact JSON 摘要
  -h, --help
USAGE
}

STRICT=0
QUICK=0
SUMMARY_JSON=0
VALIDATOR_ARGS=(--root "$ROOT_DIR")
while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict)
      STRICT=1
      VALIDATOR_ARGS+=(--strict)
      shift
      ;;
    --quick)
      QUICK=1
      VALIDATOR_ARGS+=(--quick)
      shift
      ;;
    --summary-json)
      SUMMARY_JSON=1
      VALIDATOR_ARGS+=(--summary-json)
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  "$PYTHON_BIN" -m agent_dev_kit.validation_contract "${VALIDATOR_ARGS[@]}" \
    | "$PYTHON_BIN" -c 'import json,sys; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, sort_keys=True, separators=(",", ":")))'
else
  "$PYTHON_BIN" -m agent_dev_kit.validation_contract "${VALIDATOR_ARGS[@]}"
fi

# Keep this legacy shell filename only as a stable command shim. Structured
# Manifest validation lives in typed Python and manifest.json is the sole SSOT.
if [[ "$STRICT" -eq 1 && "$QUICK" -eq 0 ]]; then
  "$ROOT_DIR/scripts/check-runtime-boundary.sh" >/dev/null
  "$ROOT_DIR/scripts/check-official-docs-governance.sh" >/dev/null
  "$ROOT_DIR/scripts/check-agent-ecosystem-standards.sh" >/dev/null
  "$PYTHON_BIN" "$ROOT_DIR/scripts/check-content-architecture-vnext.py" >/dev/null
  default_profile="$($PYTHON_BIN -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["default_profile"])' "$ROOT_DIR/manifest.json")"
  "$ROOT_DIR/scripts/check-workflow-closure.sh" --profile "$default_profile" >/dev/null
fi

if [[ "$SUMMARY_JSON" -eq 0 ]]; then
  echo "Validation orchestration passed. strict=$STRICT quick=$QUICK"
fi
