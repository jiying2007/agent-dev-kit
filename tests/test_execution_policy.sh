#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_execution_policy.py"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
import agent_dev_kit.execution_policy as policy
from agent_dev_kit.execution_policy import contracts, engine

assert engine.__file__ is not None
assert contracts.__file__ is not None
assert Path(engine.__file__).resolve() == root / "src/agent_dev_kit/execution_policy/engine.py"
assert Path(contracts.__file__).resolve() == root / "src/agent_dev_kit/execution_policy/contracts.py"
assert not (root / "src/agent_dev_kit/runtime_control").exists()
assert not (root / "src/agent_dev_kit/execution_policy/engine_support.py").exists()
assert not hasattr(policy, "Runtime" + "ControlError")
assert not (root / "tests" / ("test_" + "runtime_control.py")).exists()
assert not (root / "tests" / ("test_" + "runtime_control.sh")).exists()
for name in ("evaluate", "reduce_events", "validate_policy", "ExecutionPolicyError"):
    assert getattr(policy, name) is getattr(engine, name), name

print("[PASS] execution_policy is the sole Python namespace for execution decisions")
PY
