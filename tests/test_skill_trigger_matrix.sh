#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_FILE="$SCRIPT_DIR/fixtures/skill_trigger_cases.tsv"

[[ -f "$CASES_FILE" ]] || {
  echo "[FAIL] cases file not found: $CASES_FILE" >&2
  exit 1
}

tail -n +2 "$CASES_FILE" | while IFS=$'\t' read -r skill scope expected input_text; do
  [[ -n "$skill" ]] || continue

  if bash "$ROOT_DIR/scripts/devkit.sh" match --skill "$skill" --scope "$scope" --text "$input_text" >/tmp/adk_skill-match.txt 2>&1; then
    actual=1
  else
    actual=0
  fi

  if [[ "$actual" != "$expected" ]]; then
    cat /tmp/adk_skill-match.txt >&2
    echo "[FAIL] mismatch case skill=$skill scope=$scope expected=$expected actual=$actual" >&2
    exit 1
  fi
done

echo "[PASS] skill trigger matrix"
