#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

# Keep the anti-template ratchet, but stop forcing every Agent and Skill into the
# same SOP headings. vNext validates role-specific Agent contracts and
# class-derived Skill policy instead.
BANNED_PATTERNS=(
  "明确上下文和约束"
  "产出结构化结果并给出验证标准"
  "标注风险和后续动作"
)

for pattern in "${BANNED_PATTERNS[@]}"; do
  if rg -n "$pattern" "$ROOT_DIR/agents" "$ROOT_DIR/skills" "$ROOT_DIR/optional-skills" >/tmp/adk_asset_content_quality.txt 2>/dev/null; then
    cat /tmp/adk_asset_content_quality.txt >&2
    fail "template phrase still exists: $pattern"
  fi
done

python3 "$ROOT_DIR/scripts/check-content-architecture-vnext.py"

# Every explicit routing primary must resolve as v2 primary. Capability class is
# orthogonal: task/workflow/tool/guardrail/meta can all be direct user-task
# surfaces, while support/knowledge assets cannot silently become primary.
python3 - "$ROOT_DIR" <<'PY'
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "src"))
from agent_dev_kit.matcher_vnext import resolve_skill_content
from agent_dev_kit.model import Manifest
manifest = Manifest.load(root)
for intent in manifest.data.get("routing", {}).get("intents", []):
    primary = intent.get("primary_skill")
    if not primary:
        continue
    metadata = resolve_skill_content(manifest, primary)
    assert metadata["runtime_role"] == "primary", (intent.get("intent"), primary, metadata)
PY

# Runtime consumption ratchet: a supporting Skill may still be loaded by an
# explicit request, but an implicit trigger must not promote it to task primary.
# Use an actual v2 trigger from the rewritten Skill, not the retired v1 wording.
explicit_context="$($ROOT_DIR/scripts/skill-match.sh --skill adk-context-engineering --text '上下文工程')"
[[ "$explicit_context" == *"match=true"* ]] || fail "explicit supporting Skill load must remain available"

implicit_context="$($ROOT_DIR/scripts/skill-match.sh --text '上下文工程' 2>&1 || true)"
if [[ "$implicit_context" == *"source=skill_trigger skill=adk-context-engineering"* ]]; then
  fail "supporting Skill was implicitly promoted to primary"
fi

# A real primary fallback remains eligible; the v2 adapter must not disable
# normal trigger discovery while filtering support/governance surfaces.
primary_fallback="$($ROOT_DIR/scripts/skill-match.sh --text '设计寄存器')"
[[ "$primary_fallback" == *"match=true"* && "$primary_fallback" == *"skill=adk-register-map-design"* ]] \
  || fail "primary fallback trigger was rejected by Skill v2 eligibility"

echo "[PASS] asset content quality vNext"
