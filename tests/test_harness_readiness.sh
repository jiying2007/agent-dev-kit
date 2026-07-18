#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PASS_ROOT="$ROOT_DIR/fixtures/harness-readiness/pass/team-repo"
SECRET_ROOT="$ROOT_DIR/fixtures/harness-readiness/fail/hardcoded-mcp"
GAP_ROOT="$ROOT_DIR/fixtures/harness-readiness/fail/evidence-gap"

bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$PASS_ROOT" --as-of 2026-07-18 --summary-json >"$TMP_DIR/pass.json"
bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$PASS_ROOT" --as-of 2026-07-18 --summary-json >"$TMP_DIR/pass-second.json"
cmp "$TMP_DIR/pass.json" "$TMP_DIR/pass-second.json"

python3 - "$TMP_DIR/pass.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["schema_version"] == "adk-harness-readiness-report/v1", report
assert report["overall_status"] == "pass", report
assert report["as_of"] == "2026-07-18", report
assert report["score"] is None, report
assert report["field_evidence_status"] == "not-verified", report
assert len(report["dimensions"]) == 7, report
assert all(item["status"] == "pass" for item in report["dimensions"]), report
assert not report["scan"]["truncated"], report
PY

CURRENT_PASS_ROOT="$TMP_DIR/current-pass"
cp -R "$PASS_ROOT" "$CURRENT_PASS_ROOT"
python3 - "$CURRENT_PASS_ROOT/.adk/harness-readiness.json" <<'PY'
import datetime as dt
import json
import sys

path = sys.argv[1]
metadata = json.load(open(path, encoding="utf-8"))
for item in metadata["dimensions"].values():
    item["last_verified_at"] = dt.date.today().isoformat()
with open(path, "w", encoding="utf-8") as stream:
    json.dump(metadata, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
PY

bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$CURRENT_PASS_ROOT" --gate --output "$TMP_DIR/pass.md" >/dev/null
rg -q '^# Harness Readiness Report$' "$TMP_DIR/pass.md"
rg -q 'score: `not-used`' "$TMP_DIR/pass.md"

historical_gate_rc=0
bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$CURRENT_PASS_ROOT" --as-of 2000-01-01 --gate --summary-json \
  >"$TMP_DIR/historical-gate.out" 2>"$TMP_DIR/historical-gate.err" || historical_gate_rc=$?
if [[ "$historical_gate_rc" -ne 1 ]]; then
  echo "[FAIL] Harness readiness gate accepted an explicit historical evaluation date" >&2
  exit 1
fi
rg -q 'gate does not accept an explicit as_of' "$TMP_DIR/historical-gate.err"

bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$SECRET_ROOT" --summary-json >"$TMP_DIR/blocked.json"

python3 - "$TMP_DIR/blocked.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["overall_status"] == "blocked", report
tool = next(item for item in report["dimensions"] if item["dimension_id"] == "tool_and_permission_boundary")
assert tool["status"] == "blocked", tool
codes = {item["code"] for item in tool["blockers"]}
assert "hardcoded_mcp_secret" in codes, tool
assert "unpinned_mcp_dependency" in codes, tool
assert any("#mcpServers.unsafe-example.headers.Authorization" in item["evidence_ref"] for item in tool["blockers"]), tool
assert any("#mcpServers.unsafe-example.headers.accessToken" in item["evidence_ref"] for item in tool["blockers"]), tool
assert any("#mcpServers.unsafe-example.headers.password" in item["evidence_ref"] for item in tool["blockers"]), tool
assert any("#mcpServers.unsafe-example.headers.apiKey" in item["evidence_ref"] for item in tool["blockers"]), tool
PY

if rg -q 'fixture-literal-value|fixture-camelcase-value|prefix-|FIXTURE_API_KEY' "$TMP_DIR/blocked.json"; then
  echo "[FAIL] Harness readiness report leaked a sensitive fixture value" >&2
  exit 1
fi

secret_gate_rc=0
bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$SECRET_ROOT" --gate --summary-json >"$TMP_DIR/blocked-gate.json" || secret_gate_rc=$?
if [[ "$secret_gate_rc" -ne 2 ]]; then
  echo "[FAIL] blocked Harness readiness gate should return 2, got $secret_gate_rc" >&2
  exit 1
fi

bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$GAP_ROOT" --summary-json >"$TMP_DIR/gap.json"

agents_lines="$(wc -l <"$ROOT_DIR/AGENTS.md" | tr -d ' ')"
if [[ "$agents_lines" -gt 180 ]]; then
  echo "[FAIL] root AGENTS index exceeds the readiness line budget: $agents_lines" >&2
  exit 1
fi
rg -q 'docs/agent-operating-rules.md' "$ROOT_DIR/AGENTS.md"
for section in R1 R2 R3 R4 R5 R6 R7 R8 '八阶段生命周期' 'Gate 机制设计原则'; do
  rg -q "$section" "$ROOT_DIR/docs/agent-operating-rules.md" || {
    echo "[FAIL] detailed operating rules lost required section: $section" >&2
    exit 1
  }
done
rg -q '命中条目时必须显式声明' "$ROOT_DIR/docs/agent-operating-rules.md"
rg -q 'Reflect 阶段按提名条件扫描' "$ROOT_DIR/docs/agent-operating-rules.md"

bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$ROOT_DIR" --gate --summary-json >"$TMP_DIR/self.json"

python3 - "$TMP_DIR/self.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["overall_status"] == "pass", report
assert report["counts"] == {
    "pass": 6,
    "partial": 0,
    "needs-review": 0,
    "blocked": 0,
    "not-applicable": 1,
}, report
assert report["field_evidence_status"] == "not-verified", report
PY

python3 - "$TMP_DIR/gap.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["overall_status"] == "needs-review", report
tool = next(item for item in report["dimensions"] if item["dimension_id"] == "tool_and_permission_boundary")
assert tool["status"] == "not-applicable", tool
assert report["counts"]["not-applicable"] == 1, report
for dimension_id in (
    "spec_and_execution_contract",
    "verification_review_and_eval",
    "recovery_and_rollback",
    "freshness_and_entropy_control",
):
    dimension = next(item for item in report["dimensions"] if item["dimension_id"] == dimension_id)
    assert dimension["status"] == "needs-review", dimension
    assert not any("template" in ref or ref == "tests/README.md" for ref in dimension["evidence_refs"]), dimension
PY

mkdir -p "$TMP_DIR/ownership-decoy/src/module" "$TMP_DIR/ownership-decoy/scripts"
printf '# local module owner\n' >"$TMP_DIR/ownership-decoy/src/module/OWNERS"
printf '#!/usr/bin/env bash\n' >"$TMP_DIR/ownership-decoy/scripts/check-format.sh"
PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" "$TMP_DIR/ownership-decoy" <<'PY'
import sys
from pathlib import Path

from agent_dev_kit.readiness import RepositoryIndex, _evaluate_freshness, load_readiness_contract

root = Path(sys.argv[1])
decoy = Path(sys.argv[2])
contract = load_readiness_contract(root / "manifests" / "harness_readiness_contracts.json")
status, evidence, blockers = _evaluate_freshness(RepositoryIndex(decoy, contract))
assert status == "partial", (status, evidence, blockers)
assert "src/module/OWNERS" not in evidence, evidence
assert "missing_ownership_evidence" in {item["code"] for item in blockers}, blockers
PY

gap_gate_rc=0
bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$GAP_ROOT" --gate --summary-json >"$TMP_DIR/gap-gate.json" || gap_gate_rc=$?
if [[ "$gap_gate_rc" -ne 2 ]]; then
  echo "[FAIL] evidence-gap Harness readiness gate should return 2, got $gap_gate_rc" >&2
  exit 1
fi

malformed_rc=0
bash "$ROOT_DIR/scripts/devkit.sh" harness readiness \
  --root "$GAP_ROOT" \
  --contract "$ROOT_DIR/fixtures/harness-readiness/fail/malformed-contract.json" \
  --summary-json >"$TMP_DIR/malformed.out" 2>"$TMP_DIR/malformed.err" || malformed_rc=$?
if [[ "$malformed_rc" -ne 1 ]]; then
  echo "[FAIL] malformed contract should return 1, got $malformed_rc" >&2
  exit 1
fi
rg -q '^\[FAIL\] Harness readiness dimension fields are invalid$' "$TMP_DIR/malformed.err"
if rg -q 'Traceback|KeyError' "$TMP_DIR/malformed.err"; then
  echo "[FAIL] malformed contract leaked a traceback" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" "$PASS_ROOT" <<'PY'
import json
import sys
import tempfile
from pathlib import Path

from agent_dev_kit.readiness import (
    ReadinessContractError,
    RepositoryIndex,
    _blocker,
    _evaluate_tools,
    _finish_dimension,
    _load_metadata,
    _metadata_for_dimension,
    load_readiness_contract,
)

root = Path(sys.argv[1])
pass_root = Path(sys.argv[2])
contract = load_readiness_contract(root / "manifests" / "harness_readiness_contracts.json")

with tempfile.TemporaryDirectory(prefix="harness-readiness-contract-") as temp:
    deeply_nested = Path(temp) / "deep.json"
    deeply_nested.write_text("[" * 1200 + "0" + "]" * 1200, encoding="utf-8")
    try:
        load_readiness_contract(deeply_nested)
    except ReadinessContractError:
        pass
    else:
        raise AssertionError("deep contract must fail through ReadinessContractError")

small_contract = dict(contract)
small_contract["scan"] = dict(contract["scan"])
small_contract["scan"]["max_file_bytes"] = 8
small_index = RepositoryIndex(pass_root, small_contract)
_, metadata_errors = _load_metadata(small_index, small_contract)
assert {item["code"] for item in metadata_errors} == {"unreadable_readiness_metadata"}, metadata_errors

with tempfile.TemporaryDirectory(prefix="harness-readiness-") as temp:
    temp_root = Path(temp)
    for index in range(2):
        config_dir = temp_root / "config-{}".format(index)
        config_dir.mkdir()
        (config_dir / "mcp.json").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    bounded_contract = dict(contract)
    bounded_contract["mcp"] = dict(contract["mcp"])
    bounded_contract["mcp"]["max_configs"] = 1
    status, _, blockers = _evaluate_tools(RepositoryIndex(temp_root, bounded_contract), bounded_contract)
    assert status == "needs-review", (status, blockers)
    assert "mcp_config_limit_exceeded" in {item["code"] for item in blockers}, blockers

with tempfile.TemporaryDirectory(prefix="harness-readiness-blockers-") as temp:
    temp_root = Path(temp)
    servers = {
        "server-{}".format(index): {"headers": {"token": "fixture-value"}}
        for index in range(contract["scan"]["max_blockers_per_dimension"] + 10)
    }
    (temp_root / "mcp.json").write_text(json.dumps({"mcpServers": servers}), encoding="utf-8")
    status, _, blockers = _evaluate_tools(RepositoryIndex(temp_root, contract), contract)
    assert status == "blocked", (status, blockers)
    assert len(blockers) == contract["scan"]["max_blockers_per_dimension"], blockers
    assert blockers[-1]["code"] == "blockers_truncated", blockers

with tempfile.TemporaryDirectory(prefix="harness-readiness-negated-permissions-") as temp:
    temp_root = Path(temp)
    (temp_root / "docs").mkdir()
    (temp_root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"server": {"command": "local-server", "args": []}}}),
        encoding="utf-8",
    )
    (temp_root / "docs" / "security.md").write_text(
        "This setup is not read-only, requires no approval, and hardcodes credentials. It is an anti-pattern.",
        encoding="utf-8",
    )
    status, evidence, blockers = _evaluate_tools(RepositoryIndex(temp_root, contract), contract)
    assert status != "pass", (status, evidence, blockers)
    assert "docs/security.md" not in evidence, evidence
    assert "missing_structured_permission_boundary" in {item["code"] for item in blockers}, blockers

dimension_id = "context_legibility"
for verified_at, expected_code in (
    ("2099-01-01", "future_last_verified_at"),
    ("2000-01-01", "stale_last_verified_at"),
):
    _, _, blockers = _metadata_for_dimension(
        {
            "dimensions": {
                dimension_id: {
                    "owner": "platform-team",
                    "last_verified_at": verified_at,
                }
            }
        },
        dimension_id,
        contract["metadata_path"],
    )
    assert expected_code in {item["code"] for item in blockers}, (verified_at, blockers)

dimension = contract["dimensions"][0]
many_blockers = [_blocker("fixture-{}".format(index), "fixture") for index in range(60)]
result = _finish_dimension(
    dimension,
    "needs-review",
    [],
    many_blockers,
    {},
    [],
    contract["metadata_path"],
    contract["scan"]["max_evidence_per_dimension"],
    contract["scan"]["max_blockers_per_dimension"],
)
assert len(result["blockers"]) == contract["scan"]["max_blockers_per_dimension"], result
assert result["blockers"][-1]["code"] == "blockers_truncated", result
PY

echo "[PASS] Harness readiness deterministic report, gate, negative fixture, and redaction"
