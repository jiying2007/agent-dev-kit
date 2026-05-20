#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SUMMARY_JSON=0
MAX_SKILL_LINES=140
MAX_DOC_LINES=560

usage() {
  cat <<USAGE
Usage:
  ./scripts/check-token-budget.sh [--summary-json] [--max-skill-lines <n>] [--max-doc-lines <n>]

Checks active adk assets for token-budget regressions:
  - SKILL.md entry files stay compact; long details belong in references/.
  - active docs stay below a hard line budget; archive reports are excluded.
  - high-signal governance scripts expose --summary-json.
  - full regression runner defaults to compact bounded output.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    --max-skill-lines)
      MAX_SKILL_LINES="${2:-}"
      shift 2
      ;;
    --max-doc-lines)
      MAX_DOC_LINES="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[FAIL] unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

[[ "${MAX_SKILL_LINES}" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --max-skill-lines must be numeric" >&2
  exit 1
}
[[ "${MAX_DOC_LINES}" =~ ^[0-9]+$ ]] || {
  echo "[FAIL] --max-doc-lines must be numeric" >&2
  exit 1
}

failures=()
skill_files=0
doc_files=0
max_skill_lines=0
max_skill_file="-"
max_doc_lines=0
max_doc_file="-"
summary_scripts=0
compact_test_runner=0

record_failure() {
  failures+=("$1")
}

line_count() {
  wc -l <"$1" | tr -d ' '
}

check_file_budget() {
  local file="$1"
  local limit="$2"
  local kind="$3"
  local lines
  lines="$(line_count "$file")"
  case "$kind" in
    skill)
      skill_files=$((skill_files + 1))
      if [[ "$lines" -gt "$max_skill_lines" ]]; then
        max_skill_lines="$lines"
        max_skill_file="${file#$ROOT_DIR/}"
      fi
      ;;
    doc)
      doc_files=$((doc_files + 1))
      if [[ "$lines" -gt "$max_doc_lines" ]]; then
        max_doc_lines="$lines"
        max_doc_file="${file#$ROOT_DIR/}"
      fi
      ;;
  esac
  if [[ "$lines" -gt "$limit" ]]; then
    record_failure "${kind} token budget exceeded: ${file#$ROOT_DIR/} lines=${lines} limit=${limit}"
  fi
}

while IFS= read -r -d '' file; do
  check_file_budget "$file" "$MAX_SKILL_LINES" skill
done < <(find "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" -name SKILL.md -print0)

while IFS= read -r -d '' file; do
  check_file_budget "$file" "$MAX_DOC_LINES" doc
done < <(
  find "$ROOT_DIR/docs" "$ROOT_DIR/templates" -type f \
    \( -name '*.md' -o -name '*.tsv' -o -name '*.yaml' -o -name '*.yml' \) \
    -not -path '*/archive/*' \
    -print0
)

for script in \
  "$ROOT_DIR/scripts/validate-assets.sh" \
  "$ROOT_DIR/scripts/convert-assets.sh" \
  "$ROOT_DIR/scripts/check-codex-handoff.sh" \
  "$ROOT_DIR/scripts/check-runtime-boundary.sh" \
  "$ROOT_DIR/scripts/check-workflow-closure.sh" \
  "$ROOT_DIR/scripts/pilot-readiness.sh" \
  "$ROOT_DIR/scripts/check-fallback-sunset.sh"; do
  summary_scripts=$((summary_scripts + 1))
  if ! rg -q -- '--summary-json' "$script"; then
    record_failure "summary-json missing: ${script#$ROOT_DIR/}"
  fi
done

if rg -q -- '--verbose' "$ROOT_DIR/tests/run_all.sh" \
  && rg -q -- 'MAX_FAILURE_LINES' "$ROOT_DIR/tests/run_all.sh"; then
  compact_test_runner=1
else
  record_failure "compact test runner missing: tests/run_all.sh must default to bounded output and expose --verbose"
fi

status="pass"
if [[ "${#failures[@]}" -gt 0 ]]; then
  status="fail"
fi

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"status":"%s","skill_files":%s,"max_skill_lines":%s,"max_skill_file":"%s","doc_files":%s,"max_doc_lines":%s,"max_doc_file":"%s","summary_scripts":%s,"compact_test_runner":%s,"failures":%s}\n' \
    "$status" \
    "$skill_files" \
    "$max_skill_lines" \
    "$max_skill_file" \
    "$doc_files" \
    "$max_doc_lines" \
    "$max_doc_file" \
    "$summary_scripts" \
    "$compact_test_runner" \
    "${#failures[@]}"
else
  echo "[INFO] skill_files=${skill_files} max_skill_lines=${max_skill_lines} max_skill_file=${max_skill_file} limit=${MAX_SKILL_LINES}"
  echo "[INFO] doc_files=${doc_files} max_doc_lines=${max_doc_lines} max_doc_file=${max_doc_file} limit=${MAX_DOC_LINES}"
  echo "[INFO] summary_json_scripts=${summary_scripts}"
  echo "[INFO] compact_test_runner=${compact_test_runner}"
  if [[ "${#failures[@]}" -gt 0 ]]; then
    echo "[FAIL] token budget check failed" >&2
    printf '  - %s\n' "${failures[@]}" >&2
    exit 1
  fi
  echo "[PASS] token budget checks passed"
fi

if [[ "${#failures[@]}" -gt 0 ]]; then
  exit 1
fi
