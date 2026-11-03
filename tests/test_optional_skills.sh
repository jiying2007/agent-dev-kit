#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

python3 - "$ROOT_DIR/manifest.json" <<'PY'
import json, sys
manifest=json.load(open(sys.argv[1], encoding="utf-8"))
names={item["name"] for item in manifest["optional_skills"]}
for required in (
    "adk-incident-rca-report",
    "adk-external-practice-absorption",
    "adk-test-flakiness-triage",
):
    assert required in names, required
assert "adk-artifact-gated-lite" not in names
PY

# Retired Core Skill compatibility mirror must not reappear in optional tree.
[[ ! -e "$ROOT_DIR/optional-skills/adk-planning-execution-loop" ]] || {
  echo "[FAIL] retired optional planning Skill mirror returned" >&2
  exit 1
}

# Parent composition is advisory: optional children require an explicit selection.
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import sys
from agent_dev_kit.model import Manifest

root = Path(sys.argv[1])
manifest = Manifest.load(root)
parent = {item.name for item in manifest.resolve_profiles(["core"], ["adk-data-fetch"]).skills}
assert "adk-data-fetch" in parent
assert "adk-email-imap-fetch" not in parent
assert "adk-fetch-url-content" not in parent
with_url = {item.name for item in manifest.resolve_profiles(
    ["core"], ["adk-data-fetch", "adk-fetch-url-content"]
).skills}
assert "adk-fetch-url-content" in with_url
instructions = (root / "optional-skills/adk-data-fetch/SKILL.md").read_text(encoding="utf-8")
assert "不自动安装子 Skill" in instructions
PY

TARGET="$TMP_DIR/.claude"
PLAN="$TMP_DIR/optional-plan.json"

bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code \
  --mode copy \
  --target "$TARGET" \
  --profile core \
  --with-optional-skill adk-external-practice-absorption \
  --with-optional-skill adk-test-flakiness-triage \
  --with-optional-skill adk-incident-rca-report \
  --output "$PLAN" \
  --summary-json >"$TMP_DIR/plan.json"

bash "$ROOT_DIR/scripts/devkit.sh" install apply \
  --plan "$PLAN" \
  --summary-json >"$TMP_DIR/apply.json"

[[ -d "$TARGET/skills/adk-test-flakiness-triage" ]] || {
  echo "[FAIL] missing installed optional skill adk-test-flakiness-triage" >&2
  exit 1
}
[[ -d "$TARGET/skills/adk-external-practice-absorption" ]] || {
  echo "[FAIL] missing installed optional skill adk-external-practice-absorption" >&2
  exit 1
}
[[ -d "$TARGET/skills/adk-incident-rca-report" ]] || {
  echo "[FAIL] missing installed optional skill adk-incident-rca-report" >&2
  exit 1
}
[[ ! -e "$ROOT_DIR/scripts/install-assets.sh" ]] || {
  echo "[FAIL] retired install compatibility wrapper returned" >&2
  exit 1
}

echo "[PASS] optional skills install through canonical CLI"
