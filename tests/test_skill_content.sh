#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/skills"

pass=0
fail=0
errors=""

fail_skill() {
  local skill="$1" check="$2"
  fail=$((fail + 1))
  errors+="  [FAIL] $skill: $check"$'\n'
}

pass_skill() {
  local skill="$1" check="$2"
  pass=$((pass + 1))
}

for skill_dir in "$SKILLS_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  skill_file="$skill_dir/SKILL.md"

  if [ ! -f "$skill_file" ]; then
    fail_skill "$skill_name" "SKILL.md not found"
    continue
  fi

  content="$(cat "$skill_file")"
  body="$(sed -n '/^---$/,/^---$/d; p' "$skill_file")"
  body_lines="$(echo "$body" | wc -l)"

  # Check 1: frontmatter must contain 'name'
  if echo "$content" | head -30 | rg -q '^name:'; then
    pass_skill "$skill_name" "frontmatter has name"
  else
    fail_skill "$skill_name" "frontmatter missing 'name'"
  fi

  # Check 2: frontmatter must contain 'description'
  if echo "$content" | head -30 | rg -q '^description:'; then
    pass_skill "$skill_name" "frontmatter has description"
  else
    fail_skill "$skill_name" "frontmatter missing 'description'"
  fi

  # Check 3: frontmatter must contain 'triggers'
  if echo "$content" | head -30 | rg -q '^triggers:'; then
    pass_skill "$skill_name" "frontmatter has triggers"
  else
    fail_skill "$skill_name" "frontmatter missing 'triggers'"
  fi

  # Check 4: body must contain '## Goal' section
  if rg -q '^## Goal$' "$skill_file"; then
    pass_skill "$skill_name" "body has Goal section"
  else
    fail_skill "$skill_name" "body missing '## Goal' section"
  fi

  # Check 5: body must contain '## Workflow' section
  if rg -q '^## Workflow$' "$skill_file"; then
    pass_skill "$skill_name" "body has Workflow section"
  else
    fail_skill "$skill_name" "body missing '## Workflow' section"
  fi

  # Check 6: body must be >= 40 lines
  if [ "$body_lines" -ge 40 ]; then
    pass_skill "$skill_name" "body has $body_lines lines (>= 40)"
  else
    fail_skill "$skill_name" "body has $body_lines lines (< 40)"
  fi

  # Check 7: triggers must be non-empty (has at least one list item after 'triggers:')
  trigger_block="$(sed -n '/^triggers:/,/^[a-z]/p' "$skill_file" | grep '^\s*-\s' || true)"
  if [ -n "$trigger_block" ]; then
    pass_skill "$skill_name" "triggers is non-empty"
  else
    fail_skill "$skill_name" "triggers is empty"
  fi
done

echo ""
echo "=== Skill Content Quality Test Results ==="
echo "Passed: $pass"
echo "Failed: $fail"
echo ""

if [ -n "$errors" ]; then
  echo "Failures:"
  echo "$errors"
  exit 1
fi

echo "[PASS] skill content quality"
