#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT_DIR"

help_output="$(bash scripts/devkit.sh help)"
docs_file="docs/commands.md"

missing=0

while IFS= read -r command_name; do
  [[ -n "$command_name" ]] || continue
  if ! rg -q "^## ${command_name}$" "$docs_file"; then
    echo "[FAIL] docs/commands.md missing section for devkit command: ${command_name}" >&2
    missing=$((missing + 1))
  fi
done < <(
  printf '%s\n' "$help_output" |
    awk '
      /^Commands:/ {in_commands=1; next}
      in_commands && /^$/ {exit}
      in_commands && /^[[:space:]]+[a-z][a-z-]+[[:space:]]/ {print $1}
    '
)

if [[ "$missing" -gt 0 ]]; then
  exit 1
fi

python3 - "$ROOT_DIR" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()

active_docs: set[str] = {"README.md", "AGENTS.md", "CONTEXT.md"}
active_docs.update(
    path.relative_to(root).as_posix()
    for path in (root / "docs").glob("*.md")
)
for directory in ("runbooks", "architecture", "reference", "specs", "workflows"):
    active_docs.update(
        path.relative_to(root).as_posix()
        for path in (root / "docs" / directory).rglob("*.md")
    )

historical_marker = "<!-- adk-doc-lifecycle: historical -->"
historical_docs = {"docs/comprehensive-analysis-embedded-harness.md"}
retired_tokens = (
    "tests/test_product_maturity_v3.sh",
    "tests/test_product_maturity_v4.sh",
    "tests/test_product_maturity_v5.sh",
    "tests/test_skill_governance_v3.sh",
    "tests/test_skill_governance_v3.py",
    "tests/test_runtime_control.sh",
    "tests/test_runtime_control.py",
    "RuntimeControlError",
    "manifest.yaml",
    "scripts/install-assets.sh",
    "scripts/convert-assets.sh",
    "scripts/validate-assets.sh",
    "scripts/platform-vnext.sh",
    "scripts/skill-match.sh",
    "scripts/check-content-architecture-vnext.py",
    "agent_dev_kit.matcher_vnext",
    "scripts/quality-gates.sh",
    "scripts/check-asset-taxonomy.sh",
    "scripts/check-fallback-sunset.sh",
    "bin/agent-dev-kit",
    ".github/workflows/scorecard.yml",
    "OpenSSF Scorecard",
)
path_pattern = re.compile(r"(?<![A-Za-z0-9_./-])((?:scripts|tests)/[A-Za-z0-9_./-]+\.(?:sh|py))\b")

retired_paths = (
    "scripts/install-assets.sh",
    "scripts/convert-assets.sh",
    "scripts/validate-assets.sh",
    "scripts/platform-vnext.sh",
    "scripts/skill-match.sh",
    "scripts/check-content-architecture-vnext.py",
    "src/agent_dev_kit/matcher_vnext.py",
    "tests/fixtures/content-architecture-vnext",
    "scripts/quality-gates.sh",
    "scripts/check-fallback-sunset.sh",
    "bin/agent-dev-kit",
    "src/agent_dev_kit/runtime_control",
    ".github/workflows/platform-vnext.yml",
    "tests/test_product_maturity_v5.sh",
    "tests/test_skill_governance_v3.sh",
    "tests/test_skill_governance_v3.py",
    "tests/test_runtime_control.sh",
    "tests/test_runtime_control.py",
)

failures: list[str] = []
for relative in retired_paths:
    if (root / relative).exists():
        failures.append(f"retired compatibility surface returned: {relative}")

active_text: dict[str, str] = {}
for relative in sorted(active_docs):
    path = root / relative
    if not path.is_file():
        failures.append(f"active doc missing: {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    has_historical_marker = historical_marker in "\n".join(text.splitlines()[:20])
    if relative in historical_docs:
        if not has_historical_marker:
            failures.append(f"historical doc missing lifecycle marker: {relative}")
        continue
    if has_historical_marker:
        failures.append(f"unexpected historical lifecycle marker on active doc: {relative}")
    active_text[relative] = text
    for token in retired_tokens:
        if token in text:
            failures.append(f"retired active-doc token: {relative}: {token}")
    for referenced in sorted(set(path_pattern.findall(text))):
        if not (root / referenced).is_file():
            failures.append(f"dead active-doc command reference: {relative}: {referenced}")

manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
expected_targets = [
    str(value.get("display_name"))
    for section in ("tool_targets", "external_handoff_targets")
    for value in (manifest.get(section) or {}).values()
    if isinstance(value, dict) and value.get("display_name")
]
for relative in (
    "docs/runbooks/runtime-routing.md",
    "docs/runbooks/compatibility-matrix.md",
):
    text = active_text.get(relative, "")
    for display_name in expected_targets:
        if display_name not in text:
            failures.append(f"runtime target missing from active doc: {relative}: {display_name}")
    for retired_target in ("Hermes Agent", "hermes-agent"):
        if retired_target in text:
            failures.append(f"retired runtime target in active doc: {relative}: {retired_target}")

knowledge = active_text.get("docs/workflows/knowledge-layer.md", "")
for retired_target in ("Hermes Agent", "hermes-agent"):
    if retired_target in knowledge:
        failures.append(f"retired runtime target in knowledge layer: {retired_target}")

workspace = active_text.get("docs/workspace-governance.md", "")
if "## 3. 面向运行体系的联动策略" in workspace:
    current_runtime_section = workspace.split("## 3. 面向运行体系的联动策略", 1)[1].split("\n## ", 1)[0]
    for retired_target in ("Hermes Agent", "hermes-agent"):
        if retired_target in current_runtime_section:
            failures.append(f"retired runtime target in current workspace strategy: {retired_target}")

if failures:
    for failure in failures:
        print(f"[FAIL] {failure}", file=sys.stderr)
    raise SystemExit(1)

print(f"active_docs_checked={len(active_text)}")
PY

echo "docs/commands.md covers all devkit.sh help commands"
echo "active documentation command references resolve to current repository paths"
