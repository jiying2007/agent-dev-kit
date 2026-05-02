#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$SCRIPT_DIR/test_validate.sh"
"$SCRIPT_DIR/test_asset_content_quality.sh"
"$SCRIPT_DIR/test_format.sh"
"$SCRIPT_DIR/test_no_external_repo_refs.sh"
"$SCRIPT_DIR/test_install.sh"
"$SCRIPT_DIR/test_optional_skills.sh"
"$SCRIPT_DIR/test_convert.sh"
"$SCRIPT_DIR/test_change_governance.sh"
"$SCRIPT_DIR/test_evidence_index.sh"
"$SCRIPT_DIR/test_workflow.sh"
"$SCRIPT_DIR/test_openspec_bridge.sh"
"$SCRIPT_DIR/test_catalog.sh"
"$SCRIPT_DIR/test_skill_trigger_matrix.sh"

echo "All tests passed"
