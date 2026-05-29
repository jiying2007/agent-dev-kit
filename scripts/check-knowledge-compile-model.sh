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

require_file "$RUNBOOK"
require_file "$TEMPLATE"
require_file "$SKILL"

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
  summary \
  cross_references \
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
require_text "$RUNBOOK" "unresolved questions"

require_text "$SKILL" "Compiled Knowledge"
require_text "$SKILL" "综合页不是原始证据"
require_text "$SKILL" "raw_fallback"
require_text "$SKILL" "raw_sources"
require_text "$SKILL" "maintained_wiki"
require_text "$SKILL" "schema"

echo "[PASS] knowledge compile model"
