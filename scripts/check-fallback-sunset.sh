#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--summary-json" ]]; then
  printf '%s\n' '{"status":"removed","compatibility_enabled":false,"replacement":"pilot-readiness-and-runtime-footprint"}'
else
  echo "[REMOVED] external runtime fallback compatibility is disabled; use pilot-readiness and runtime footprint gates" >&2
fi

exit 3
