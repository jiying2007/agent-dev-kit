#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

"$ROOT_DIR/scripts/devkit.sh" skill-relationships --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass", d; assert d["legacy_depends_on_authoritative_for_delivery_sequencing"] is False, d; assert d["delivery_lifecycle"]["status"]=="pass", d'

echo "[PASS] Skill relationship graph is valid; legacy depends_on is non-sequencing"
