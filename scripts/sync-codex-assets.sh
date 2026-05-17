#!/usr/bin/env bash
set -euo pipefail

cat >&2 <<'EOF'
[FAIL] sync-codex-assets.sh has been retired.

Codex delivery is hard-switched to:

  bash scripts/devkit.sh convert --target codex ...
  bash scripts/devkit.sh codex-handoff --codex-root ~/codex

Do not sync agent-dev-kit output directly into ~/.codex.
EOF
exit 1
