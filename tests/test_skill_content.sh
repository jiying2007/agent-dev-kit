#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src"
cd "$ROOT_DIR"
# Content v2 has no universal SOP headings or minimum line count.
python3 -m unittest tests.test_skill_content_contract tests.test_document_authoring_skills tests.test_skill_method_efficiency tests.test_skill_quality_methods tests.test_verification_stage_economy tests.test_skill_portfolio_quality tests.test_external_method_intake tests.test_external_core_methods tests.test_external_domain_methods tests.test_repository_workflow_efficiency tests.test_skill_execution_tasks tests.test_skill_command_examples tests.test_review_raw_diff tests.test_skill_domain_execution tests.test_skill_runtime_methods tests.test_skill_openai_metadata tests.test_commit_message_policy -v
echo "[PASS] Skills content v2, OpenAI metadata and Commit Policy"
