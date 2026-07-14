#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for target in claude-code opencode hermes-agent; do
  [[ -f "$ROOT_DIR/manifests/target-contracts/${target}.json" ]] || {
    echo "[FAIL] missing target contract: $target" >&2
    exit 1
  }
done

bash "$ROOT_DIR/scripts/devkit.sh" target check --all --level static --summary-json \
  >"$TMP_DIR/target-check.json"
python3 - "$TMP_DIR/target-check.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema"] == "adk-target-check/v1", value
assert value["status"] == "pass", value
assert set(value["targets"]) == {"claude-code", "hermes-agent", "opencode"}, value
assert all(item["contract_status"] == "experimental" for item in value["targets"].values()), value
PY

CLAUDE_OUT="$TMP_DIR/claude-export"
bash "$ROOT_DIR/scripts/devkit.sh" export \
  --target claude-code --profile core --out "$CLAUDE_OUT" --summary-json \
  >"$TMP_DIR/claude-export.json"
[[ -f "$CLAUDE_OUT/claude-code/agents/requirements-analyst.md" ]]
[[ -f "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage/SKILL.md" ]]
[[ -f "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage/references/embedded-discovery-brief.md" ]]
[[ ! -e "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage.md" ]]

OPENCODE_OUT="$TMP_DIR/opencode-export"
bash "$ROOT_DIR/scripts/devkit.sh" export \
  --target opencode --profile core --out "$OPENCODE_OUT" >/dev/null
[[ -f "$OPENCODE_OUT/opencode/agents/requirements-analyst.md" ]]
[[ -f "$OPENCODE_OUT/opencode/skills/adk-requirements-triage/SKILL.md" ]]
[[ ! -e "$OPENCODE_OUT/opencode/prompts" ]]

python3 - "$CLAUDE_OUT" "$OPENCODE_OUT" <<'PY'
import sys
from pathlib import Path

import yaml


def frontmatter(path):
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    _, raw, body = text.split("---", 2)
    value = yaml.safe_load(raw)
    assert isinstance(value, dict), value
    assert body.strip(), path
    return value


claude = Path(sys.argv[1]) / "claude-code"
opencode = Path(sys.argv[2]) / "opencode"
for target in (claude, opencode):
    skill = frontmatter(target / "skills/adk-requirements-triage/SKILL.md")
    assert skill["name"] == "adk-requirements-triage", skill
    assert skill["description"], skill
    assert skill["metadata"]["adk"]["target"] == target.name, skill

claude_read_only = frontmatter(claude / "agents/requirements-analyst.md")
assert claude_read_only["name"] == "requirements-analyst", claude_read_only
assert claude_read_only["description"], claude_read_only
assert "Read" in claude_read_only["tools"], claude_read_only
assert "Edit" not in claude_read_only["tools"], claude_read_only

opencode_read_only = frontmatter(opencode / "agents/requirements-analyst.md")
assert opencode_read_only["description"], opencode_read_only
assert opencode_read_only["mode"] == "subagent", opencode_read_only
assert opencode_read_only["permission"]["edit"] == "deny", opencode_read_only

opencode_writer = frontmatter(opencode / "agents/driver-engineer.md")
assert opencode_writer["permission"]["edit"] == "allow", opencode_writer
PY

set +e
bash "$ROOT_DIR/scripts/devkit.sh" export \
  --target hermes-agent --profile core --out "$TMP_DIR/hermes-invalid" \
  >"$TMP_DIR/hermes-invalid.out" 2>"$TMP_DIR/hermes-invalid.err"
hermes_invalid_rc=$?
set -e
[[ "$hermes_invalid_rc" -eq 2 ]] || {
  echo "[FAIL] unsupported Hermes Agent must return exit 2, got $hermes_invalid_rc" >&2
  exit 1
}
[[ ! -e "$TMP_DIR/hermes-invalid/hermes-agent" ]] || {
  echo "[FAIL] unsupported Hermes Agent produced partial output" >&2
  exit 1
}
rg -q 'unsupported_asset_kind' "$TMP_DIR/hermes-invalid.err"

HERMES_OUT="$TMP_DIR/hermes-export"
bash "$ROOT_DIR/scripts/devkit.sh" export \
  --target hermes-agent --asset-kind skill --profile core --out "$HERMES_OUT" >/dev/null
[[ -f "$HERMES_OUT/hermes-agent/skills/adk-requirements-triage/SKILL.md" ]]
[[ ! -e "$HERMES_OUT/hermes-agent/agents" ]]

set +e
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code --target "$TMP_DIR/symlink-target" --profile core \
  --mode symlink --output "$TMP_DIR/symlink-plan.json" \
  >"$TMP_DIR/symlink.out" 2>"$TMP_DIR/symlink.err"
symlink_rc=$?
set -e
[[ "$symlink_rc" -eq 2 ]]
[[ ! -e "$TMP_DIR/symlink-plan.json" ]]
rg -q 'unsupported_install_mode' "$TMP_DIR/symlink.err"

INSTALL_TARGET="$TMP_DIR/install-target"
INSTALL_PLAN="$TMP_DIR/install-plan.json"
bash "$ROOT_DIR/scripts/devkit.sh" install plan \
  --tool claude-code --target "$INSTALL_TARGET" --profile core \
  --mode copy --output "$INSTALL_PLAN" >/dev/null
python3 - "$INSTALL_PLAN" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema"] == "adk-install-plan/v2", value
assert value["asset_kind"] is None, value
assert value["active_receipt_sha256"] is None, value
assert all(item["mode"] == "copy" for item in value["operations"]), value
assert all("rendered_sha256" in item for item in value["operations"]), value
PY

python3 - "$INSTALL_PLAN" "$TMP_DIR/extended-plan.json" <<'PY'
import datetime as dt
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
created = dt.datetime.fromisoformat(value["created_at"].replace("Z", "+00:00"))
value["expires_at"] = (created + dt.timedelta(days=2)).isoformat().replace("+00:00", "Z")
with open(sys.argv[2], "w", encoding="utf-8") as stream:
    json.dump(value, stream)
PY
if bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/extended-plan.json" \
  >"$TMP_DIR/extended-plan.out" 2>"$TMP_DIR/extended-plan.err"; then
  echo "[FAIL] install accepted a plan lifetime above 1440 minutes" >&2
  exit 1
fi
rg -q 'plan lifetime must be between 1 and 1440 minutes' "$TMP_DIR/extended-plan.err"

bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$INSTALL_PLAN" >/dev/null
python3 - "$INSTALL_TARGET/.adk-install-receipt.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["schema"] == "adk-install-receipt/v3", value
assert value["contract_sha256"], value
PY

python3 - "$CLAUDE_OUT/claude-code" "$INSTALL_TARGET" <<'PY'
import hashlib
import sys
from pathlib import Path


def inventory(root, ignored):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name in ignored or any(part.startswith(".adk-") for part in path.parts):
            continue
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


exported = inventory(sys.argv[1], {"adk-export-manifest.json"})
installed = inventory(sys.argv[2], {".adk-install-receipt.json"})
assert exported == installed, (set(exported) ^ set(installed), exported, installed)
PY

bash "$ROOT_DIR/scripts/devkit.sh" install rollback \
  --receipt "$INSTALL_TARGET/.adk-install-receipt.json" >/dev/null
[[ ! -e "$INSTALL_TARGET/agents/requirements-analyst.md" ]]
[[ ! -e "$INSTALL_TARGET/skills/adk-requirements-triage/SKILL.md" ]]

python3 - "$INSTALL_PLAN" "$TMP_DIR/legacy-plan.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
value["schema"] = "adk-install-plan/v1"
with open(sys.argv[2], "w", encoding="utf-8") as stream:
    json.dump(value, stream)
PY
if bash "$ROOT_DIR/scripts/devkit.sh" install apply --plan "$TMP_DIR/legacy-plan.json" >/dev/null 2>&1; then
  echo "[FAIL] legacy v1 plan unexpectedly applied" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import copy
import sys
from pathlib import Path

from agent_dev_kit.model import Manifest

root = Path(sys.argv[1])
manifest = Manifest.load(root)
unknown = copy.deepcopy(manifest.data)
unknown["unexpected_top_level"] = True
failures = Manifest(root, unknown, root / "manifest.json").validate(strict=True)
assert any("unexpected_top_level" in item for item in failures), failures
PY

set +e
bash "$ROOT_DIR/scripts/devkit.sh" target smoke \
  --target claude-code --stage discovery --summary-json \
  >"$TMP_DIR/not-run.json"
not_run_rc=$?
set -e
[[ "$not_run_rc" -eq 2 ]]
python3 - "$TMP_DIR/not-run.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["status"] == "not-run", value
assert value["certification"] == "not-certified", value
PY

set +e
bash "$ROOT_DIR/scripts/devkit.sh" target smoke \
  --target claude-code --stage discovery --timeout-seconds 0 \
  --runtime-command python3 "$ROOT_DIR/tests/fixtures/fake_target_runtime.py" \
  >"$TMP_DIR/timeout.out" 2>"$TMP_DIR/timeout.err"
timeout_rc=$?
set -e
[[ "$timeout_rc" -eq 2 ]]
rg -q 'invalid_timeout_seconds' "$TMP_DIR/timeout.err"

bash "$ROOT_DIR/scripts/devkit.sh" target smoke \
  --target claude-code --stage discovery --summary-json \
  --runtime-command python3 "$ROOT_DIR/tests/fixtures/fake_target_runtime.py" \
  >"$TMP_DIR/fake-smoke.json"
python3 - "$TMP_DIR/fake-smoke.json" <<'PY'
import json
import sys

value = json.load(open(sys.argv[1], encoding="utf-8"))
assert value["status"] == "pass", value
assert value["certification"] == "caller-supplied-smoke", value
assert value["started_at"].endswith("Z"), value
assert value["duration_ms"] >= 0, value
assert len(value["runtime_command_sha256"]) == 64, value
PY

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" "$TMP_DIR" <<'PY'
import shutil
import sys
from pathlib import Path

from agent_dev_kit.model import Asset, Manifest, ManifestError
from agent_dev_kit.targets import load_target_contract, render_asset

root = Path(sys.argv[1])
temp = root / "tests/fixtures/target-support-symlink.tmp"
if temp.exists():
    raise AssertionError("temporary support-symlink fixture already exists")
try:
    asset_root = temp / "adk-requirements-triage"
    asset_root.mkdir(parents=True)
    (asset_root / "SKILL.md").write_text(
        "---\nname: adk-requirements-triage\ndescription: fixture\n---\n\n# Fixture\n",
        encoding="utf-8",
    )
    (asset_root / "scripts").mkdir()
    outside = temp / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (asset_root / "scripts" / "unsafe-link").symlink_to(outside)
    manifest = Manifest.load(root)
    contract = load_target_contract(manifest, "claude-code")
    asset = Asset("skill", "adk-requirements-triage", asset_root)
    try:
        render_asset(manifest, contract, asset)
    except ManifestError as exc:
        assert "symlink forbidden" in str(exc), exc
    else:
        raise AssertionError("target renderer accepted a symlinked support file")
finally:
    shutil.rmtree(str(temp), ignore_errors=True)
PY

echo "[PASS] target contracts"
