#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Typed product code may mention manifest.yaml as a packaged compatibility
# artifact, but only the manifest compatibility contract may actually import a
# YAML parser. This separates provenance/packaging references from structured
# data consumption.
python3 - "$ROOT/src/agent_dev_kit" <<'PY'
import ast
import sys
from pathlib import Path

root = Path(sys.argv[1])
allowed = {
    Path("manifest_contract.py"),
    Path("domain/manifest.py"),
}
offenders = []
for path in sorted(root.rglob("*.py")):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports_yaml = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports_yaml = imports_yaml or any(alias.name == "yaml" or alias.name.startswith("yaml.") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports_yaml = imports_yaml or module == "yaml" or module.startswith("yaml.")
    relative = path.relative_to(root)
    if imports_yaml and relative not in allowed:
        offenders.append(str(relative))
if offenders:
    raise SystemExit("typed product modules import YAML outside compatibility boundary: " + ", ".join(offenders))
PY

# release.py may still package the compatibility projection, but it must not
# parse it or use it as release identity.
python3 - "$ROOT/src/agent_dev_kit/release.py" <<'PY'
import ast
import sys
from pathlib import Path

path = Path(sys.argv[1])
tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
yaml_import = False
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        yaml_import = yaml_import or any(alias.name == "yaml" or alias.name.startswith("yaml.") for alias in node.names)
    elif isinstance(node, ast.ImportFrom):
        module = node.module or ""
        yaml_import = yaml_import or module == "yaml" or module.startswith("yaml.")
assert not yaml_import, "release.py must not parse YAML"
assert "manifest.yaml" in path.read_text(encoding="utf-8"), "release source distribution should preserve compatibility artifact until retirement"
PY

# The migrated taxonomy contract must stay JSON-only even if the compatibility
# projection is absent.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cp "$ROOT/manifest.json" "$TMP_DIR/manifest.json"
python3 -m agent_dev_kit.asset_taxonomy_contract --root "$TMP_DIR" --summary-json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["status"]=="pass" and d["source"]=="manifest.json"'

echo "[PASS] typed manifest consumers stay on canonical JSON"
