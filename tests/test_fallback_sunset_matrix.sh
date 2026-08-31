#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output=""
rc=0
output="$("${ROOT}/scripts/check-fallback-sunset.sh" --summary-json 2>&1)" || rc=$?

[[ "${rc}" -eq 3 ]] || {
  echo "[FAIL] retired compatibility gate must fail closed with exit 3" >&2
  exit 1
}
[[ "${output}" == *'"status":"removed"'* && "${output}" == *'"compatibility_enabled":false'* ]] || {
  echo "[FAIL] retired compatibility gate output mismatch: ${output}" >&2
  exit 1
}

echo "[PASS] external runtime fallback compatibility remains retired"
