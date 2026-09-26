#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for target in claude-code opencode; do
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
assert set(value["targets"]) == {"claude-code", "opencode"}, value
assert all(item["contract_status"] == "experimental" for item in value["targets"].values()), value
assert all(item["contract_schema"] == "adk-target-contract/v2" for item in value["targets"].values()), value
for item in value["targets"].values():
    adapter = item["adapter"]
    assert adapter["conformance"]["native_runtime_smoke"] == "not-run", adapter
    assert adapter["conformance"]["certification"] == "not-certified", adapter
    assert adapter["trace_contract"] == "adk-workflow-trace-summary-v2", adapter
PY

python3 - "$ROOT_DIR" <<'PY'
import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

root = Path(sys.argv[1])
schema = json.loads((root / "manifests/target-contract.schema.json").read_text(encoding="utf-8"))
contract = json.loads((root / "manifests/target-contracts/claude-code.json").read_text(encoding="utf-8"))
validator = Draft202012Validator(schema, format_checker=FormatChecker())

native = copy.deepcopy(contract)
for capability in ("discovery", "load", "trigger"):
    native["adapter"]["capabilities"][capability] = "native-verified"
native["adapter"]["conformance"] = {
    "level": "runtime",
    "certification": "conformance-certified",
    "native_runtime_smoke": "pass",
    "runtime_binary": "claude",
    "runtime_binary_sha256": "b" * 64,
    "runtime_version": "2.1.0",
    "runtime_version_pin": "2.1.0",
    "last_verified_at": "2026-08-30T00:00:00Z",
    "evidence": [{
        "receipt_schema": "adk-native-target-conformance-receipt/v2",
        "path": "reports/runtime/claude-native-smoke.json",
        "sha256": "a" * 64,
        "target": "claude-code",
        "runtime_version": "2.1.0",
        "bundle_sha256": "c" * 64,
        "contract_sha256": "d" * 64,
        "layer": "runtime",
    }],
}
native["adapter"]["conformance_trust_policy"] = {
    "enabled": True,
    "trusted_authorities": ["ci-native-conformance"],
    "verification_backend": "ci-provenance-verifier",
}
assert not list(validator.iter_errors(native)), "native conformance branch must be representable"

missing_evidence = copy.deepcopy(native)
missing_evidence["adapter"]["conformance"]["evidence"] = []
assert list(validator.iter_errors(missing_evidence)), "native conformance without evidence must fail"

static_native_claim = copy.deepcopy(contract)
static_native_claim["adapter"]["capabilities"]["discovery"] = "native-verified"
assert list(validator.iter_errors(static_native_claim)), "static conformance must not claim native verification"

weak_native = copy.deepcopy(native)
weak_native["adapter"]["capabilities"]["trigger"] = "declared-static"
assert list(validator.iter_errors(weak_native)), "runtime conformance must verify discovery/load/trigger"
PY

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import copy
import datetime as dt
import hashlib
import json
import shutil
import sys
from pathlib import Path

from agent_dev_kit.model import Manifest, ManifestError
from agent_dev_kit.targets import (
    _authority_digest,
    _native_contract_digest,
    _validate_native_conformance_evidence,
)

root = Path(sys.argv[1])
manifest = Manifest.load(root)
temp = root / "tests/fixtures/target-native-evidence.tmp"
try:
    temp.mkdir()
    contract = json.loads(
        (root / "manifests/target-contracts/claude-code.json").read_text(encoding="utf-8")
    )
    conformance = {
        "level": "runtime",
        "certification": "conformance-certified",
        "native_runtime_smoke": "pass",
        "runtime_binary": "claude",
        "runtime_binary_sha256": "b" * 64,
        "runtime_version": "2.1.0",
        "runtime_version_pin": "2.1.0",
        "last_verified_at": None,
        "evidence": [],
    }
    for capability in ("discovery", "load", "trigger"):
        contract["adapter"]["capabilities"][capability] = "native-verified"
    contract["adapter"]["conformance"] = conformance
    contract["adapter"]["conformance_trust_policy"] = {
        "enabled": True,
        "trusted_authorities": ["ci-native-conformance"],
        "verification_backend": "ci-provenance-verifier",
    }
    contract_digest = _native_contract_digest(contract)
    bundle_digest = "c" * 64
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    base = now - dt.timedelta(minutes=4)

    def stamp(value):
        return value.isoformat().replace("+00:00", "Z")

    stages = []
    for index, stage_name in enumerate(("discovery", "load", "trigger")):
        started = base + dt.timedelta(minutes=index)
        completed = started + dt.timedelta(seconds=10)
        authority = {
            "execution_authority": "ci-approved",
            "authority_id": "ci-native-conformance",
            "scope": stage_name,
        }
        authority["attestation_sha256"] = _authority_digest(authority)
        stages.append({
            "stage": stage_name,
            "command_sha256": str(index + 1) * 64,
            "assertion_sha256": ("a", "b", "c")[index] * 64,
            "assertion_result_sha256": ("d", "e", "f")[index] * 64,
            "semantic_assertion_status": "pass",
            "result_sha256": str(index + 4) * 64,
            "exit_code": 0,
            "started_at": stamp(started),
            "completed_at": stamp(completed),
            "duration_ms": 10000,
            "environment": {
                "platform": "linux",
                "architecture": "x86_64",
                "cwd_sha256": "7" * 64,
                "environment_sha256": "8" * 64,
                "runtime_binary_sha256": "b" * 64,
                "bundle_sha256": bundle_digest,
                "contract_sha256": contract_digest,
            },
            "privacy": {
                "raw_content_stored": False,
                "secrets_stored": False,
                "sanitized": True,
            },
            "authority": authority,
        })
    receipt = {
        "schema": "adk-native-target-conformance-receipt/v2",
        "receipt_id": "claude-native-20260830",
        "target": "claude-code",
        "runtime": {
            "binary": "claude",
            "binary_sha256": "b" * 64,
            "version": "2.1.0",
            "version_pin": "2.1.0",
        },
        "bundle_sha256": bundle_digest,
        "contract_sha256": contract_digest,
        "verified_at": stamp(now),
        "stages": stages,
    }
    evidence = temp / "native-smoke.json"

    def install_receipt(value, path=evidence):
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        conformance["last_verified_at"] = value["verified_at"]
        conformance["evidence"] = [{
            "receipt_schema": value["schema"],
            "path": path.relative_to(root).as_posix(),
            "sha256": digest,
            "target": value["target"],
            "runtime_version": value["runtime"]["version"],
            "bundle_sha256": value["bundle_sha256"],
            "contract_sha256": value["contract_sha256"],
            "layer": "runtime",
        }]

    install_receipt(receipt)
    adapter = contract["adapter"]
    trusted_verifier = lambda value, policy: (
        value["receipt_id"] == "claude-native-20260830"
        and policy["verification_backend"] == "ci-provenance-verifier"
    )
    try:
        _validate_native_conformance_evidence(manifest, "claude-code", adapter, contract)
    except ManifestError as exc:
        assert "trust verifier is not injected" in str(exc), exc
    else:
        raise AssertionError("synthetic self-hashed receipt was promoted without a trust verifier")
    _validate_native_conformance_evidence(
        manifest, "claude-code", adapter, contract, trusted_verifier
    )

    missing = copy.deepcopy(adapter)
    missing["conformance"]["evidence"][0]["path"] = "tests/fixtures/missing-native.json"
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", missing, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("missing native evidence was accepted")

    wrong_hash = copy.deepcopy(adapter)
    wrong_hash["conformance"]["evidence"][0]["sha256"] = "0" * 64
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", wrong_hash, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("wrong native evidence hash was accepted")

    wrong_runtime = copy.deepcopy(adapter)
    wrong_runtime["conformance"]["evidence"][0]["runtime_version"] = "other"
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", wrong_runtime, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("native evidence runtime mismatch was accepted")

    readme = temp / "README.md"
    readme.write_text("# not a conformance receipt\n", encoding="utf-8")
    fake = copy.deepcopy(adapter)
    fake["conformance"]["evidence"][0]["path"] = readme.relative_to(root).as_posix()
    fake["conformance"]["evidence"][0]["sha256"] = hashlib.sha256(readme.read_bytes()).hexdigest()
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", fake, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("README plus matching hash was accepted as native evidence")

    missing_semantic = copy.deepcopy(receipt)
    missing_semantic["stages"][1]["semantic_assertion_status"] = "fail"
    install_receipt(missing_semantic)
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", adapter, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("native receipt without passed semantic assertion was accepted")

    reused = copy.deepcopy(receipt)
    reused["stages"][1]["command_sha256"] = reused["stages"][0]["command_sha256"]
    install_receipt(reused)
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", adapter, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("one command evidence was accepted for multiple native stages")

    future = copy.deepcopy(receipt)
    future["verified_at"] = stamp(now + dt.timedelta(days=1))
    install_receipt(future)
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", adapter, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("future-dated native receipt was accepted")

    wrong_contract = copy.deepcopy(receipt)
    wrong_contract["contract_sha256"] = "f" * 64
    install_receipt(wrong_contract)
    try:
        _validate_native_conformance_evidence(
            manifest, "claude-code", adapter, contract, trusted_verifier
        )
    except ManifestError:
        pass
    else:
        raise AssertionError("receipt with the wrong contract digest was accepted")

    for secret_value in (
        "ghp_abcdefghijklmnop",
        "github_pat_abcdefghijklmnop",
        "sk-abcdefghijklmnop",
        "Bearer abcdefghijklmnop",
        "AKIAABCDEFGHIJKLMNOP",
        "-----BEGIN PRIVATE KEY-----",
    ):
        secret_receipt = copy.deepcopy(receipt)
        secret_receipt["stages"][0]["authority"]["authority_id"] = secret_value
        install_receipt(secret_receipt)
        try:
            _validate_native_conformance_evidence(
                manifest, "claude-code", adapter, contract, trusted_verifier
            )
        except ManifestError as exc:
            assert "secret-like content" in str(exc), exc
        else:
            raise AssertionError("secret-like native receipt content was accepted")
finally:
    shutil.rmtree(temp, ignore_errors=True)
PY

CLAUDE_OUT="$TMP_DIR/claude-export"
bash "$ROOT_DIR/scripts/devkit.sh" export \
  --target claude-code --profile core --out "$CLAUDE_OUT" --summary-json \
  >"$TMP_DIR/claude-export.json"
[[ -f "$CLAUDE_OUT/claude-code/agents/requirements-analyst.md" ]]
[[ -f "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage/SKILL.md" ]]
[[ -f "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage/references/embedded-discovery-brief.md" ]]
[[ ! -e "$CLAUDE_OUT/claude-code/skills/adk-requirements-triage.md" ]]
[[ ! -e "$CLAUDE_OUT/claude-code/skills/adk-test-strategy/references/embedded-tdd-matrix.md" ]]

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

opencode_writer = frontmatter(opencode / "agents/component-engineer.md")
assert opencode_writer["permission"]["edit"] == "allow", opencode_writer
assert not (opencode / "agents/driver-engineer.md").exists(), "embedded driver agent leaked into core"
PY

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
