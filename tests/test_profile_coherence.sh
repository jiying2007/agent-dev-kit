#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

bash "$ROOT_DIR/scripts/check-profile-coherence.sh"

[[ ! -e "$ROOT_DIR/skills/adk-test-strategy/references/embedded-tdd-matrix.md" ]] || {
  echo "[FAIL] embedded TDD matrix leaked into platform-neutral test strategy" >&2
  exit 1
}
[[ -f "$ROOT_DIR/skills/adk-unit-test-embedded/references/embedded-tdd-matrix.md" ]] || {
  echo "[FAIL] embedded TDD matrix missing from embedded-only unit test skill" >&2
  exit 1
}

echo "[PASS] profile coherence"
