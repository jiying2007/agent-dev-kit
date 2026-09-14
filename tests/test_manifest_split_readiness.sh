#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

out="$(mktemp)"
trap 'rm -f "$out"' EXIT
set +e
bash "$ROOT/scripts/devkit.sh" manifest split-readiness --summary-json >"$out"
rc=$?
set -e
[[ "$rc" -eq 2 ]] || { echo "[FAIL] current split readiness must be blocked/exit 2, got $rc" >&2; exit 1; }

python3 - "$ROOT" "$out" <<'PY'
import json
import sys
from pathlib import Path

from agent_dev_kit.contracts.manifest_composition import split_migration_readiness

root = Path(sys.argv[1])
result = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert result["schema"] == "adk-manifest-split-readiness/v1"
assert result["status"] == "blocked"
assert result["authorization_state"] == "blocked"
assert result["change_id"] == "manifest-build-time-split"
assert result["change_stage"] is None
assert result["required_change_stage"] == "review-passed"
assert result["authoring_root_present"] is False
assert result["generator_path_present"] is False
assert result["activation_invariants"]["runtime_fragment_loading"] is False
assert result["activation_invariants"]["parallel_ssot_allowed"] is False
assert len(result["required_evidence"]) == 6
assert any("authorization is blocked" in item for item in result["blockers"])

policy = json.loads((root / "manifests/manifest_composition_policy.json").read_text(encoding="utf-8"))
rogue = split_migration_readiness(
    policy,
    change_stage="review-passed",
    authoring_root_present=True,
    generator_path_present=True,
)
assert rogue["status"] == "blocked"
assert any("physical authoring root is present" in item for item in rogue["blockers"])
assert any("generator path is present" in item for item in rogue["blockers"])

drifted = json.loads(json.dumps(policy))
drifted["migration_gate"]["state"] = "authorized"
invalid = split_migration_readiness(
    drifted,
    change_stage="review-passed",
    authoring_root_present=True,
    generator_path_present=True,
)
assert invalid["status"] == "invalid"
PY

echo '[PASS] manifest physical split remains blocked until deliberate contract migration'
