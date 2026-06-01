#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

require_file() {
  local file="$1"
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing reuse-before-rebuild asset: $file"
}

require_text() {
  local file="$1"
  local pattern="$2"
  rtk rg -q -- "$pattern" "$ROOT_DIR/$file" || fail "$file missing pattern: $pattern"
}

TEMPLATE="templates/governance/reuse-before-rebuild-decision.md"
FIXTURE="tests/fixtures/reuse-before-rebuild/adapt_existing.md"
UPSTREAM="docs/runbooks/upstream-intake.md"
CURATION="docs/runbooks/skill-curation-delivery.md"

require_file "$TEMPLATE"
require_file "$FIXTURE"
require_file "$UPSTREAM"
require_file "$CURATION"

for field in \
  problem_statement \
  existing_asset_search \
  candidate_assets \
  decision \
  build_fresh_reason \
  verification_evidence; do
  require_text "$TEMPLATE" "^${field}:"
  require_text "$FIXTURE" "^${field}:"
done

for decision in use-as-is adapt-existing build-fresh reference-only; do
  require_text "$UPSTREAM" "$decision"
done

require_text "$UPSTREAM" "reuse-before-rebuild"
require_text "$UPSTREAM" "templates/governance/reuse-before-rebuild-decision.md"
require_text "$CURATION" "reuse-before-rebuild"
require_text "$CURATION" "existing_asset_search"
require_text "$FIXTURE" "decision: adapt-existing"
require_text "$FIXTURE" "build-fresh skill rejected"
require_text "$FIXTURE" "negative_or_disproved_path"

echo "[PASS] reuse-before-rebuild"

