#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

python3 -m unittest \
  tests.test_skill_governance_v3.SkillGovernanceV3Tests.test_dependency_graph_is_valid_acyclic_and_forward_only \
  -v

echo "[PASS] skill dependency graph is valid, acyclic, and lifecycle-ordered"
