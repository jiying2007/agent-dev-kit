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

if rg -n $'\r' README.md manifest.json docs scripts agents skills optional-skills templates tests .github >/tmp/adk_crlf_check.txt 2>/dev/null; then
  cat /tmp/adk_crlf_check.txt >&2
  fail "detected CRLF line endings"
fi

if rg -n '\t' manifest.json >/tmp/adk_tab_check.txt 2>/dev/null; then
  cat /tmp/adk_tab_check.txt >&2
  fail "manifest.json contains tab characters"
fi

DIFF_BASE_REF="${ADK_FORMAT_BASE_REF:-}"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [[ -n "$DIFF_BASE_REF" ]]; then
    if ! git diff --check "$DIFF_BASE_REF" >/tmp/adk_diff_check.txt 2>&1; then
      cat /tmp/adk_diff_check.txt >&2
      fail "detected whitespace errors in diff against $DIFF_BASE_REF"
    fi
  elif git rev-parse --verify origin/main >/dev/null 2>&1; then
    if ! git diff --check origin/main >/tmp/adk_diff_check.txt 2>&1; then
      cat /tmp/adk_diff_check.txt >&2
      fail "detected whitespace errors in diff against origin/main"
    fi
  elif ! git diff --check >/tmp/adk_diff_check.txt 2>&1; then
    cat /tmp/adk_diff_check.txt >&2
    fail "detected whitespace errors in working tree diff"
  fi
fi

for script in scripts/*.sh tests/*.sh; do
  [[ -f "$script" ]] || continue
  head -n 1 "$script" | grep -q '^#!/usr/bin/env bash$' || fail "missing bash shebang: $script"
  [[ "$script" == scripts/lib-*.sh ]] && continue
  [[ -x "$script" ]] || warn "script is not executable: $script"
done

echo "Format check passed"
