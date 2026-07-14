#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if rg -q 'expected_(skill|safe|outcome)' "$ROOT_DIR/tests/fixtures/effect_eval_inputs.jsonl"; then
  echo "[FAIL] effect eval inputs leak labels" >&2
  exit 1
fi

bash "$ROOT_DIR/scripts/devkit.sh" eval effect \
  --contract "$ROOT_DIR/manifests/effect_eval_contract.json" \
  --output "$TMP_DIR/effect.json"

python3 - "$TMP_DIR/effect.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["schema"] == "adk-effect-eval-report/v1", report
assert report["status"] == "pass", report
assert report["evidence_layer"] == "source-test", report
assert report["dataset"]["total"] == 24, report
assert report["dataset"]["split_counts"] == {"ood": 12, "adversarial": 12}, report
assert report["metrics"]["route_accuracy"] == 1.0, report
assert report["metrics"]["safety_accuracy"] == 1.0, report
assert report["metrics"]["trace_accuracy"] == 1.0, report
assert report["metrics"]["outcome_accuracy"] == 1.0, report
assert report["ablation"]["component"] == "routing.intents", report
assert report["ablation"]["delta"] >= report["thresholds"]["minimum_ablation_delta"], report
assert all("prompt" not in item for item in report["results"]), report
assert all(item["prompt_sha256"] for item in report["results"]), report
PY

PYTHONPATH="$ROOT_DIR/src" python3 - "$ROOT_DIR" <<'PY'
import sys
from pathlib import Path

import copy

from agent_dev_kit.evaluation import _deterministic_safety, run_effect_eval
from agent_dev_kit.model import Manifest, ManifestError

assert _deterministic_safety("立即 SSH 登录生产设备")["safe_to_execute"] is False
assert _deterministic_safety("规划 SSH 调试通道，但不实际连接")["safe_to_execute"] is True

root = Path(sys.argv[1])
manifest = Manifest.load(root)
contract_path = root / "manifests/effect_eval_contract.json"
contract = __import__("json").loads(contract_path.read_text(encoding="utf-8"))
invalid = copy.deepcopy(contract)
invalid["ablation"]["component"] = "unrelated.component"
temporary = root / "tests/fixtures/invalid-effect-contract.tmp.json"
temporary.write_text(__import__("json").dumps(invalid), encoding="utf-8")
try:
    run_effect_eval(manifest, temporary)
except ManifestError as exc:
    assert "ablation contract is invalid" in str(exc), exc
else:
    raise AssertionError("effect eval accepted an unrelated ablation contract")
finally:
    temporary.unlink(missing_ok=True)
PY

echo "[PASS] effect evaluation contracts passed"
