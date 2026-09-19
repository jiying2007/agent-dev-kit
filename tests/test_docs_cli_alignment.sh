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

import re
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
active_docs = (
    "README.md",
    "AGENTS.md",
    "CONTEXT.md",
    "docs/commands.md",
    "docs/usage.md",
    "docs/adk-usage-guide.md",
    "docs/agent-operating-rules.md",
    "docs/runbooks/workspace-maintenance-guide.md",
    "docs/runbooks/mcp-governance.md",
    "docs/runbooks/compatibility-matrix.md",
)
retired_tokens = (
    "tests/test_product_maturity_v3.sh",
    "tests/test_product_maturity_v4.sh",
    "tests/test_product_maturity_v5.sh",
    "tests/test_skill_governance_v3.sh",
    "tests/test_skill_governance_v3.py",
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
    "hermes-agent",
    "Hermes Agent",
)
path_pattern = re.compile(r"(?<![A-Za-z0-9_./-])((?:scripts|tests)/[A-Za-z0-9_./-]+\.sh)\b")

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
    "tests/test_product_maturity_v5.sh",
    "tests/test_skill_governance_v3.sh",
    "tests/test_skill_governance_v3.py",
)

failures: list[str] = []
for relative in retired_paths:
    if (root / relative).exists():
        failures.append(f"retired compatibility surface returned: {relative}")
for relative in active_docs:
    path = root / relative
    if not path.is_file():
        failures.append(f"active doc missing: {relative}")
        continue
    text = path.read_text(encoding="utf-8")
    for token in retired_tokens:
        if token in text:
            failures.append(f"retired active-doc token: {relative}: {token}")
    for referenced in sorted(set(path_pattern.findall(text))):
        if not (root / referenced).is_file():
            failures.append(f"dead active-doc command reference: {relative}: {referenced}")

if failures:
    for failure in failures:
        print(f"[FAIL] {failure}", file=sys.stderr)
    raise SystemExit(1)
PY

echo "docs/commands.md covers all devkit.sh help commands"
echo "active documentation command references resolve to current repository paths"
