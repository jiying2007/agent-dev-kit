#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT_DIR/tests/test_runtime_bundle.py"

if ! git -C "$ROOT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  if [[ -n "${CI:-}" ]]; then
    echo "[FAIL] runtime bundle identity CI requires a native Git checkout" >&2
    exit 1
  fi
  exit 0
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

RECEIPT="$TMP_DIR/embedded-fullstack-runtime-bundle-identity.json"
PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
  python3 "$ROOT_DIR/scripts/verify-runtime-bundle-identity.py" \
  --profile embedded-fullstack \
  --output "$RECEIPT" >/dev/null

python3 - "$RECEIPT" <<'PY'
import json
import re
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["schema"] == "adk-runtime-bundle-identity/v1"
assert receipt["status"] == "pass"
assert receipt["profile"] == "embedded-fullstack"
assert receipt["independent_builds"] == 2
assert receipt["reproducible"] is True
source = receipt["source_provenance"]
assert source["kind"] == "git-clean-commit"
assert source["release_eligible"] is True
assert source["dirty"] is False
assert re.fullmatch(r"[0-9a-f]{40}", source["commit"])
assert re.fullmatch(r"[0-9a-f]{40}", source["tree"])
assert re.fullmatch(r"[0-9a-f]{64}", receipt["manifest_sha256"])
bundle = receipt["bundle"]
assert bundle["schema"] == "adk-runtime-bundle/v1"
assert bundle["artifact_name"].startswith("adk-runtime-embedded-fullstack-")
assert re.fullmatch(r"[0-9a-f]{64}", bundle["sha256"])
assert bundle["source_distribution"] is False
PY
