#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCORE_TSV="$(mktemp)"
CANDIDATE_TSV="$(mktemp)"
trap 'rm -f "$SCORE_TSV" "$CANDIDATE_TSV"' EXIT

"$ROOT_DIR/scripts/check-fallback-sunset.sh"
"$ROOT_DIR/scripts/check-fallback-sunset.sh" --score-tsv "$SCORE_TSV" >/tmp/adk_fallback_score.out
"$ROOT_DIR/scripts/check-fallback-sunset.sh" --candidate-tsv "$CANDIDATE_TSV" >/tmp/adk_fallback_candidates.out

head -n 1 "$SCORE_TSV" | grep -Fxq $'fallback_skill\tstatus\tmatched_skill\trouting\tprofile\tpilot\thandoff\tlive\tscore\tmax_score' || {
  echo "[FAIL] score TSV header mismatch" >&2
  exit 1
}

grep -q '^using-superpowers	' "$SCORE_TSV" || {
  echo "[FAIL] score TSV missing using-superpowers row" >&2
  exit 1
}

head -n 1 "$CANDIDATE_TSV" | grep -Fxq $'fallback_skill\tcurrent_status\tmatched_skill\tscore\tlive\tcandidate_state\tnext_step\tpilot_refs' || {
  echo "[FAIL] candidate TSV header mismatch" >&2
  exit 1
}

grep -q $'\tcandidate-sunset\t' "$CANDIDATE_TSV" || {
  echo "[FAIL] candidate TSV missing candidate-sunset rows" >&2
  exit 1
}

grep -q $'\tcandidate\t' "$CANDIDATE_TSV" || {
  echo "[FAIL] candidate TSV missing candidate rows" >&2
  exit 1
}

grep -q $'\treview-second-pilot-before-candidate\t' "$CANDIDATE_TSV" || {
  echo "[FAIL] candidate TSV missing review queue rows" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-fallback-sunset.sh" --summary-json | grep -q '"status":"pass"' || {
  echo "[FAIL] summary json did not pass" >&2
  exit 1
}

echo "[PASS] fallback sunset matrix"
