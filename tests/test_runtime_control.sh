#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_runtime_control.py"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PY'
import agent_dev_kit.execution_policy as preferred
import agent_dev_kit.runtime_control as compatibility
from agent_dev_kit.execution_policy import engine as preferred_engine
from agent_dev_kit.runtime_control import engine as compatibility_engine

assert preferred.__all__ == compatibility.__all__
for name in compatibility.__all__:
    assert getattr(preferred, name) is getattr(compatibility, name), name

for name in ("evaluate", "reduce_events", "validate_policy", "RuntimeControlError"):
    assert getattr(preferred_engine, name) is getattr(compatibility_engine, name), name

assert preferred.POLICY_SCHEMA == compatibility.POLICY_SCHEMA
assert preferred.POLICY_SCHEMA_V2 == compatibility.POLICY_SCHEMA_V2
assert preferred.DECISION_SCHEMA == compatibility.DECISION_SCHEMA
assert preferred.DECISION_SCHEMA_V2 == compatibility.DECISION_SCHEMA_V2
print("[PASS] execution_policy and runtime_control expose one 5.x implementation surface")
PY
