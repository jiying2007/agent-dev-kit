#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

help_output="$(bash scripts/devkit.sh help)"
docs_file="docs/commands.md"

missing=0

while IFS= read -r command_name; do
  [[ -n "$command_name" ]] || continue
  if ! rg -q "^## ${command_name}$" "$docs_file"; then
    echo "[FAIL] docs/commands.md missing section for devkit command: ${command_name}" >&2
    missing=$((missing + 1))
  fi
done < <(
  printf '%s\n' "$help_output" |
    awk '
      /^Commands:/ {in_commands=1; next}
      in_commands && /^$/ {exit}
      in_commands && /^[[:space:]]+[a-z][a-z-]+[[:space:]]/ {print $1}
    '
)

if [[ "$missing" -gt 0 ]]; then
  exit 1
fi

echo "docs/commands.md covers all devkit.sh help commands"
