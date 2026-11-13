#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src"
cd "$ROOT_DIR"
# Content v2 has no universal SOP headings or minimum line count.
python3 -m unittest tests.test_skill_content_contract tests.test_document_authoring_skills tests.test_skill_openai_metadata tests.test_commit_message_policy -v
echo "[PASS] Skills content v2, OpenAI metadata and Commit Policy"
