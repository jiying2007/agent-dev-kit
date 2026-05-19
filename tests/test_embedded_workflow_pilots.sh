#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

OUT_DIR="$TMP_DIR/workflow-pilots"

"$ROOT_DIR/scripts/run-embedded-workflow-pilots.sh" --pilot all --out "$OUT_DIR" > "$TMP_DIR/runner.out"

for pilot in \
  embedded-fullstack-long-task-recovery \
  embedded-bugfix-systematic-debugging \
  embedded-tdd-test-strategy \
  embedded-review-code-review-loop \
  embedded-verification-completion \
  embedded-parallel-worktree-governance \
  embedded-branch-closeout
do
  [[ -f "$OUT_DIR/$pilot/evidence.md" ]] || {
    echo "[FAIL] missing evidence for $pilot" >&2
    exit 1
  }
  [[ -f "$OUT_DIR/$pilot/summary.json" ]] || {
    echo "[FAIL] missing summary for $pilot" >&2
    exit 1
  }
  rg -q '"status": "pass"' "$OUT_DIR/$pilot/summary.json" || {
    echo "[FAIL] pilot did not pass: $pilot" >&2
    cat "$OUT_DIR/$pilot/summary.json" >&2
    exit 1
  }
done

rg -q "pass-expected-failure" "$OUT_DIR/embedded-tdd-test-strategy/evidence.md" || {
  echo "[FAIL] test strategy pilot did not record red-path evidence" >&2
  exit 1
}

rg -q "root_cause:" "$OUT_DIR/embedded-bugfix-systematic-debugging/root-cause.md" || {
  echo "[FAIL] bugfix pilot did not record root cause" >&2
  exit 1
}

rg -q "scope_write_checked: pass" "$OUT_DIR/embedded-parallel-worktree-governance/subagent-review.md" || {
  echo "[FAIL] parallel governance pilot did not record subagent review" >&2
  exit 1
}

rg -q "Final Gate Result: pass" "$OUT_DIR/embedded-verification-completion/final-gate.md" || {
  echo "[FAIL] verification pilot did not record final gate result" >&2
  exit 1
}

rg -q "decision:" "$OUT_DIR/embedded-branch-closeout/closeout-decision.md" || {
  echo "[FAIL] branch closeout pilot did not record a decision" >&2
  exit 1
}

echo "[PASS] embedded workflow pilots"
