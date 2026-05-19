#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SCORE_TSV="$(mktemp)"
trap 'rm -f "$SCORE_TSV"' EXIT

"$ROOT_DIR/scripts/check-fallback-sunset.sh"
"$ROOT_DIR/scripts/check-fallback-sunset.sh" --score-tsv "$SCORE_TSV" >/tmp/adk_fallback_score.out

head -n 1 "$SCORE_TSV" | grep -Fxq $'fallback_skill\tstatus\tmatched_skill\trouting\tprofile\tpilot\thandoff\tlive\tscore\tmax_score' || {
  echo "[FAIL] score TSV header mismatch" >&2
  exit 1
}

grep -q '^using-superpowers	' "$SCORE_TSV" || {
  echo "[FAIL] score TSV missing using-superpowers row" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-fallback-sunset.sh" --summary-json | grep -q '"status":"pass"' || {
  echo "[FAIL] summary json did not pass" >&2
  exit 1
}

echo "[PASS] fallback sunset matrix"
