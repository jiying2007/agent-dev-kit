#!/usr/bin/env bash
set -euo pipefail

MODE="${ADK_LOCAL_CI_MODE:-full}"
PHASE="${ADK_LOCAL_CI_PHASE:-gates}"
case "$MODE" in
  quick|full) ;;
  *)
    echo "[FAIL] ADK_LOCAL_CI_MODE must be quick or full" >&2
    exit 2
    ;;
esac
case "$PHASE" in
  gates|audit) ;;
  *)
    echo "[FAIL] ADK_LOCAL_CI_PHASE must be gates or audit" >&2
    exit 2
    ;;
esac

[[ -d /source ]] || {
  echo "[FAIL] read-only source mount is missing at /source" >&2
  exit 2
}

mkdir -p /work/home /work/source /work/dist /work/tmp
tar \
  --directory /source \
  --exclude=.git \
  --exclude=.ruff_cache \
  --exclude=build \
  --exclude=dist \
  --exclude='*.egg-info' \
  --exclude='__pycache__' \
  --create \
  --file - \
  . | tar --directory /work/source --no-same-owner --extract --file -
chmod -R u=rwX,go=rX /work/source
cd /work/source

export HOME=/work/home
export TMPDIR=/work/tmp
export PYTHONDONTWRITEBYTECODE=1
python -m venv --system-site-packages /work/venv
# shellcheck disable=SC1091
source /work/venv/bin/activate

if [[ "$PHASE" == "audit" ]]; then
  pip-audit --strict --progress-spinner off .
  echo "[PASS] local CI dependency audit python=$(python -c 'import platform; print(platform.python_version())')"
  exit 0
fi

python -m pip install --disable-pip-version-check --no-build-isolation --no-deps .
bash scripts/devkit.sh doctor --summary-json
bash scripts/devkit.sh validate --strict
bash scripts/check-format.sh
shellcheck -S error -x -P scripts scripts/*.sh tests/*.sh tools/local-ci/*.sh
ruff check src tools tests/fixtures/fake_target_runtime.py
python -m agent_dev_kit.cli target check --all --level static --summary-json

if [[ "$MODE" == "quick" ]]; then
  bash tests/run_all.sh --quick --timing-json /work/test-timing.json
else
  bash tests/run_all.sh --timing-json /work/test-timing.json
fi
bash scripts/check-performance-budgets.sh --strict --timing-json /work/test-timing.json

bash scripts/devkit.sh security check
bash scripts/devkit.sh eval run --suite deterministic --summary-json
bash scripts/devkit.sh release check
python -m pip wheel --disable-pip-version-check --no-build-isolation --no-deps --wheel-dir /work/dist .
python -m venv --system-site-packages /work/wheel-venv
/work/wheel-venv/bin/python -m pip install \
  --disable-pip-version-check --no-index --no-deps /work/dist/agent_dev_kit-*.whl
cd /work
env -u PYTHONPATH /work/wheel-venv/bin/python -c \
  'from agent_dev_kit.trace_summary import load_trace_summary_schema; assert load_trace_summary_schema()["$id"].endswith("adk-workflow-trace-summary-v2.schema.json")'
env -u PYTHONPATH /work/wheel-venv/bin/python -c \
  'from agent_dev_kit.evidence_graph import _validate_schema; _validate_schema({"invalid": True}, None)' \
  >/work/wheel-evidence-schema.out 2>/work/wheel-evidence-schema.err && {
    echo "[FAIL] installed-wheel evidence graph validator accepted invalid input" >&2
    exit 1
  }

echo "[PASS] local CI parity python=$(python -c 'import platform; print(platform.python_version())') mode=$MODE"
