#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_runtime_control.py"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()

import agent_dev_kit.execution_policy as preferred
import agent_dev_kit.runtime_control as compatibility
from agent_dev_kit.execution_policy import contracts as preferred_contracts
from agent_dev_kit.execution_policy import engine as preferred_engine
from agent_dev_kit.runtime_control import engine as compatibility_engine
from agent_dev_kit.runtime_control import engine_support as compatibility_support

assert preferred.__all__ == compatibility.__all__
for name in compatibility.__all__:
    assert getattr(preferred, name) is getattr(compatibility, name), name

for name in ("evaluate", "reduce_events", "validate_policy", "RuntimeControlError"):
    assert getattr(preferred_engine, name) is getattr(compatibility_engine, name), name

for name in (
    "RuntimeControlError",
    "validate_policy",
    "goal_intake_attestation_sha256",
    "EVENT_SCHEMA",
    "STATE_SCHEMA",
    "POLICY_SCHEMA",
    "POLICY_SCHEMA_V2",
):
    assert getattr(preferred_contracts, name) is getattr(compatibility_support, name), name

assert preferred.POLICY_SCHEMA == compatibility.POLICY_SCHEMA
assert preferred.POLICY_SCHEMA_V2 == compatibility.POLICY_SCHEMA_V2
assert preferred.DECISION_SCHEMA == compatibility.DECISION_SCHEMA
assert preferred.DECISION_SCHEMA_V2 == compatibility.DECISION_SCHEMA_V2

preferred_engine_path = Path(preferred_engine.__file__).resolve()
preferred_contracts_path = Path(preferred_contracts.__file__).resolve()
compatibility_engine_path = Path(compatibility_engine.__file__).resolve()
compatibility_support_path = Path(compatibility_support.__file__).resolve()

assert preferred_engine_path == root / "src/agent_dev_kit/execution_policy/engine.py"
assert preferred_contracts_path == root / "src/agent_dev_kit/execution_policy/contracts.py"
assert compatibility_engine_path == root / "src/agent_dev_kit/runtime_control/engine.py"
assert compatibility_support_path == root / "src/agent_dev_kit/runtime_control/engine_support.py"
assert not (root / "src/agent_dev_kit/execution_policy/engine_support.py").exists()

canonical_engine = preferred_engine_path.read_text(encoding="utf-8")
canonical_contracts = preferred_contracts_path.read_text(encoding="utf-8")
legacy_engine = compatibility_engine_path.read_text(encoding="utf-8")
legacy_support = compatibility_support_path.read_text(encoding="utf-8")
preferred_init = (root / "src/agent_dev_kit/execution_policy/__init__.py").read_text(encoding="utf-8")

assert "from .contracts import" in canonical_engine
assert "..runtime_control" not in canonical_engine
assert "..runtime_control" not in canonical_contracts
assert "..runtime_control" not in preferred_init
assert "..execution_policy.engine import *" in legacy_engine
assert "..execution_policy.contracts import *" in legacy_support
assert len(legacy_engine.encode("utf-8")) < 2048
assert len(legacy_support.encode("utf-8")) < 2048

print(
    "[PASS] execution_policy owns the canonical 5.x engine/contracts; "
    "runtime_control is a thin object-identical compatibility facade"
)
PY
