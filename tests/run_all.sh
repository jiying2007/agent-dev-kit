#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 原有测试
"$SCRIPT_DIR/test_validate.sh"
"$SCRIPT_DIR/test_asset_content_quality.sh"
"$SCRIPT_DIR/test_format.sh"
"$SCRIPT_DIR/test_no_external_repo_refs.sh"
"$SCRIPT_DIR/test_file_modes.sh"
"$SCRIPT_DIR/test_install.sh"
"$SCRIPT_DIR/test_profile_coherence.sh"
"$SCRIPT_DIR/test_optional_skills.sh"
"$SCRIPT_DIR/test_convert.sh"
"$SCRIPT_DIR/test_convert_codex_handoff.sh"
"$SCRIPT_DIR/test_runtime_boundary.sh"
"$SCRIPT_DIR/test_workflow_closure.sh"
"$SCRIPT_DIR/test_change_governance.sh"
"$SCRIPT_DIR/test_evidence_index.sh"
"$SCRIPT_DIR/test_workflow.sh"
"$SCRIPT_DIR/test_openspec_bridge.sh"
"$SCRIPT_DIR/test_catalog.sh"
"$SCRIPT_DIR/test_skill_trigger_matrix.sh"
"$SCRIPT_DIR/test_boundary_conditions_match.sh"

# 新增测试
"$SCRIPT_DIR/test_enhanced_gate_check.sh"
"$SCRIPT_DIR/test_templates.sh"
"$SCRIPT_DIR/test_context_md.sh"
"$SCRIPT_DIR/test_boundary_conditions.sh"
"$SCRIPT_DIR/test_integration.sh"
"$SCRIPT_DIR/test_profile_coherence_enhanced.sh"
"$SCRIPT_DIR/test_match_effectiveness.sh"
"$SCRIPT_DIR/test_skill_content.sh"
"$SCRIPT_DIR/test_scripts_smoke.sh"

echo "All tests passed"
