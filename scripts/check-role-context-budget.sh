#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAX_ROLE_AGENT_BYTES=6000
MAX_ROLE_AGENTS_BYTES=64000
SUMMARY_JSON=0

usage() {
  cat <<USAGE
Usage: ./scripts/check-role-context-budget.sh [--summary-json] [--max-role-agent-bytes <n>] [--max-role-agents-bytes <n>]

Fail-closed byte budget for built-in role AGENTS.md context surfaces.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    --max-role-agent-bytes)
      MAX_ROLE_AGENT_BYTES="${2:-}"
      shift 2
      ;;
    --max-role-agents-bytes)
      MAX_ROLE_AGENTS_BYTES="${2:-}"
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

for value in "$MAX_ROLE_AGENT_BYTES" "$MAX_ROLE_AGENTS_BYTES"; do
  [[ "$value" =~ ^[0-9]+$ ]] || {
    echo "[FAIL] role context budgets must be numeric" >&2
    exit 1
  }
done

failures=()
role_agent_files=0
role_agents_bytes=0
max_role_agent_bytes=0
max_role_agent_file="-"

while IFS= read -r -d '' file; do
  bytes="$(wc -c <"$file" | tr -d ' ')"
  role_agent_files=$((role_agent_files + 1))
  role_agents_bytes=$((role_agents_bytes + bytes))
  if [[ "$bytes" -gt "$max_role_agent_bytes" ]]; then
    max_role_agent_bytes="$bytes"
    max_role_agent_file="${file#$ROOT_DIR/}"
  fi
  if [[ "$bytes" -gt "$MAX_ROLE_AGENT_BYTES" ]]; then
    failures+=("role AGENTS context budget exceeded: ${file#$ROOT_DIR/} bytes=${bytes} limit=${MAX_ROLE_AGENT_BYTES}")
  fi
done < <(find "$ROOT_DIR/agents" -mindepth 2 -maxdepth 2 -type f -name AGENTS.md -print0 | sort -z)

if [[ "$role_agent_files" -eq 0 ]]; then
  failures+=("no built-in role AGENTS.md files found")
fi
if [[ "$role_agents_bytes" -gt "$MAX_ROLE_AGENTS_BYTES" ]]; then
  failures+=("aggregate role AGENTS context budget exceeded: bytes=${role_agents_bytes} limit=${MAX_ROLE_AGENTS_BYTES}")
fi

role_agents_estimated_tokens=$(((role_agents_bytes + 3) / 4))
status="pass"
[[ "${#failures[@]}" -eq 0 ]] || status="fail"

if [[ "$SUMMARY_JSON" -eq 1 ]]; then
  printf '{"status":"%s","estimate_method":"utf8-bytes-ceil-div-4","role_agent_files":%s,"role_agents_bytes":%s,"role_agents_limit":%s,"role_agents_estimated_tokens":%s,"max_role_agent_bytes":%s,"max_role_agent_limit":%s,"max_role_agent_file":"%s","failures":%s}\n' \
    "$status" "$role_agent_files" "$role_agents_bytes" "$MAX_ROLE_AGENTS_BYTES" \
    "$role_agents_estimated_tokens" "$max_role_agent_bytes" "$MAX_ROLE_AGENT_BYTES" \
    "$max_role_agent_file" "${#failures[@]}"
else
  echo "[INFO] role_agent_files=${role_agent_files} role_agents_bytes=${role_agents_bytes}/${MAX_ROLE_AGENTS_BYTES} estimated_tokens=${role_agents_estimated_tokens}"
  echo "[INFO] max_role_agent=${max_role_agent_file} bytes=${max_role_agent_bytes}/${MAX_ROLE_AGENT_BYTES}"
  for failure in "${failures[@]}"; do
    echo "[FAIL] $failure" >&2
  done
fi

[[ "$status" == "pass" ]]
