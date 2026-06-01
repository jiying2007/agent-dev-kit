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
  [[ -f "$ROOT_DIR/$file" ]] || fail "missing knowledge compile asset: $file"
}

require_text() {
  local file="$1"
  local pattern="$2"
  rtk rg -q -- "$pattern" "$ROOT_DIR/$file" || fail "$file missing pattern: $pattern"
}

RUNBOOK="docs/runbooks/knowledge-compile-model.md"
TEMPLATE="templates/memory/knowledge-compile-note.md"
SKILL="skills/adk-token-context-governance/SKILL.md"
EXAMPLE="tests/fixtures/knowledge-compile/example-note.md"

require_file "$RUNBOOK"
require_file "$TEMPLATE"
require_file "$SKILL"
require_file "$EXAMPLE"

for layer in raw_sources maintained_wiki schema; do
  require_text "$RUNBOOK" "$layer"
done

for operation in ingest query lint; do
  require_text "$RUNBOOK" "$operation"
done

for field in \
  raw_source_path \
  wiki_page_path \
  schema_path \
  source_url_or_local_path \
  retrieved_at \
  review_status \
  expires_at \
  summary \
  cross_references \
  duplicate_concept_check \
  stale_claims \
  raw_fallback \
  change_log; do
  require_text "$RUNBOOK" "$field"
  require_text "$TEMPLATE" "$field"
done

require_text "$RUNBOOK" "综合页用于降低重复阅读成本，不是原始证据"
require_text "$RUNBOOK" "raw sources 保持不可变"
require_text "$RUNBOOK" "weak links"
require_text "$RUNBOOK" "orphan pages"
require_text "$RUNBOOK" "duplicate concept pages"
require_text "$RUNBOOK" "unresolved questions"
require_text "$RUNBOOK" "过期来源"

require_text "$SKILL" "Compiled Knowledge"
require_text "$SKILL" "综合页不是原始证据"
require_text "$SKILL" "raw_fallback"
require_text "$SKILL" "raw_sources"
require_text "$SKILL" "maintained_wiki"
require_text "$SKILL" "schema"
require_text "$SKILL" "duplicate_concept_check"
require_text "$SKILL" "expires_at"

for pattern in \
  "raw_source_path" \
  "raw_sources/runtime-pilot-raw.md" \
  "retrieved_at: 2026-05-30" \
  "review_status: reviewed" \
  "expires_at: 2026-06-30" \
  "duplicate_concept_check" \
  "decision: update-existing" \
  "wiki_page_path" \
  "maintained_wiki/runtime-pilot.md" \
  "schema_path" \
  "schema/knowledge-compile.schema.json" \
  "raw_fallback" \
  "required_for: promotion, dispute, stale claim review" \
  "change_log"; do
  require_text "$EXAMPLE" "$pattern"
done

echo "[PASS] knowledge compile model"
