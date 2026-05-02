#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage:
  ./scripts/evidence_index.sh append --file <path> --command <cmd> --exit-code <n> --summary <text> --evidence-path <path> --layer <Agent|Skill|Workflow> [--artifact <name>]
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

ACTION="$1"
shift

FILE=""
COMMAND=""
EXIT_CODE=""
SUMMARY=""
EVIDENCE_PATH=""
LAYER=""
ARTIFACT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)
      FILE="$2"
      shift 2
      ;;
    --command)
      COMMAND="$2"
      shift 2
      ;;
    --exit-code)
      EXIT_CODE="$2"
      shift 2
      ;;
    --summary)
      SUMMARY="$2"
      shift 2
      ;;
    --evidence-path)
      EVIDENCE_PATH="$2"
      shift 2
      ;;
    --layer)
      LAYER="$2"
      shift 2
      ;;
    --artifact)
      ARTIFACT="$2"
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

escape_cell() {
  printf '%s' "$1" | sed 's/|/\\|/g'
}

append_evidence() {
  [[ -n "$FILE" ]] || { echo "[FAIL] --file is required" >&2; exit 1; }
  [[ -n "$COMMAND" ]] || { echo "[FAIL] --command is required" >&2; exit 1; }
  [[ "$EXIT_CODE" =~ ^[0-9]+$ ]] || { echo "[FAIL] --exit-code must be a non-negative integer" >&2; exit 1; }
  [[ -n "$SUMMARY" ]] || { echo "[FAIL] --summary is required" >&2; exit 1; }
  [[ -n "$EVIDENCE_PATH" ]] || { echo "[FAIL] --evidence-path is required" >&2; exit 1; }
  case "$LAYER" in
    Agent|Skill|Workflow)
      ;;
    *)
      echo "[FAIL] --layer must be Agent, Skill, or Workflow" >&2
      exit 1
      ;;
  esac

  if [[ ! -f "$FILE" ]]; then
    {
      echo "## Evidence Index（命令级）"
      echo "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"
      echo "|---|---|---|---|---|---|"
    } > "$FILE"
  elif ! rg -q '^## Evidence Index（命令级）' "$FILE"; then
    {
      echo
      echo "## Evidence Index（命令级）"
      echo "| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |"
      echo "|---|---|---|---|---|---|"
    } >> "$FILE"
  fi

  printf '| %s | %s | %s | %s | %s | %s |\n' \
    "$(escape_cell "$COMMAND")" \
    "$EXIT_CODE" \
    "$(escape_cell "$SUMMARY")" \
    "$(escape_cell "$EVIDENCE_PATH")" \
    "$LAYER" \
    "$(escape_cell "${ARTIFACT:-none}")" >> "$FILE"

  echo "[OK] evidence appended: $FILE"
}

case "$ACTION" in
  append)
    append_evidence
    ;;
  *)
    echo "[FAIL] unsupported action: $ACTION" >&2
    usage >&2
    exit 1
    ;;
esac
