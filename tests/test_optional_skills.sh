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
