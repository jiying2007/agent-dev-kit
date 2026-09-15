#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

[[ ! -e scripts/openspec-bridge.sh ]] || {
  echo "[FAIL] OpenSpec bridge must not exist in ADK core" >&2
  exit 1
}

[[ ! -d openspec ]] || {
  echo "[FAIL] openspec/ must not be a core authoring root" >&2
  exit 1
}

python - <<'PY'
import json
from pathlib import Path

manifest = json.loads(Path("manifest.json").read_text(encoding="utf-8"))
profiles = manifest.get("profiles", {})
violations = [name for name in profiles if "openspec" in name.lower()]
if violations:
    raise SystemExit(f"[FAIL] OpenSpec profile remains in core: {violations}")

serialized = json.dumps(manifest, ensure_ascii=False).lower()
for forbidden in ("openspec-bridge", "/opsx:"):
    if forbidden in serialized:
        raise SystemExit(f"[FAIL] forbidden OpenSpec runtime/core marker in manifest: {forbidden}")
PY

if rg -n --fixed-strings 'openspec-driven' README.md scripts manifest.json >/dev/null 2>&1; then
  echo "[FAIL] openspec-driven core surface reintroduced" >&2
  exit 1
fi

if rg -n --fixed-strings 'openspec-bridge.sh' README.md scripts manifest.json >/dev/null 2>&1; then
  echo "[FAIL] OpenSpec bridge invocation reintroduced" >&2
  exit 1
fi

if rg -n --fixed-strings '/opsx:' README.md scripts manifest.json >/dev/null 2>&1; then
  echo "[FAIL] OpenSpec command surface reintroduced" >&2
  exit 1
fi

echo "[PASS] OpenSpec isolation ratchet"
