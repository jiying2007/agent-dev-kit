#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

warn() {
  echo "[WARN] $1" >&2
}

cd "$ROOT_DIR"

if rg -n $'\r' README.md manifest.yaml docs scripts agents skills optional-skills templates tests .github >/tmp/adk_crlf_check.txt 2>/dev/null; then
  cat /tmp/adk_crlf_check.txt >&2
  fail "detected CRLF line endings"
fi

if rg -n '\t' manifest.yaml >/tmp/adk_tab_check.txt 2>/dev/null; then
  cat /tmp/adk_tab_check.txt >&2
  fail "manifest.yaml contains tab characters"
fi

for script in scripts/*.sh tests/*.sh; do
  [[ -f "$script" ]] || continue
  head -n 1 "$script" | grep -q '^#!/usr/bin/env bash$' || fail "missing bash shebang: $script"
  [[ "$script" == scripts/lib-*.sh ]] && continue
  [[ -x "$script" ]] || warn "script is not executable: $script"
done

echo "Format check passed"
