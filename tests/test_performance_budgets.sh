#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$ROOT_DIR/scripts/check-performance-budgets.sh"
"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json >"$TMP_DIR/perf-budget.json"
rg -q '"status":"pass"' "$TMP_DIR/perf-budget.json" || {
  echo "[FAIL] performance budget summary did not pass" >&2
  cat "$TMP_DIR/perf-budget.json" >&2
  exit 1
}

cat >"$TMP_DIR/quick-pass.json" <<'JSON'
{
  "schema_version": 1,
  "mode": "quick",
  "status": "pass",
  "total": 1,
  "pass": 1,
  "fail": 0,
  "elapsed_ms": 1000,
  "slow_threshold_sec": 10,
  "tests": [],
  "slow_tests": []
}
JSON
"$ROOT_DIR/scripts/check-performance-budgets.sh" --strict --timing-json "$TMP_DIR/quick-pass.json"

cat >"$TMP_DIR/quick-fail.json" <<'JSON'
{
  "schema_version": 1,
  "mode": "quick",
  "status": "pass",
  "total": 1,
  "pass": 1,
  "fail": 0,
  "elapsed_ms": 999999,
  "slow_threshold_sec": 10,
  "tests": [],
  "slow_tests": []
}
JSON
if "$ROOT_DIR/scripts/check-performance-budgets.sh" --strict --timing-json "$TMP_DIR/quick-fail.json" >"$TMP_DIR/fail.out" 2>"$TMP_DIR/fail.err"; then
  echo "[FAIL] strict performance budget should fail on exceeded timing" >&2
  exit 1
fi
rg -q 'timing budget exceeded' "$TMP_DIR/fail.err" || {
  echo "[FAIL] strict budget failure did not explain exceeded timing" >&2
  cat "$TMP_DIR/fail.err" >&2
  exit 1
}

"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/quick-fail.json" >"$TMP_DIR/report-only.json"
python3 - "$TMP_DIR/report-only.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
assert report["status"] == "warn", report
assert report["strict"] == 0 and report["failures"] == 0, report
assert report["elapsed_ms"] == 999999 and report["budget_ms"] > 0, report
PY

python3 - "$TMP_DIR/quick-pass.json" "$TMP_DIR/full-pass.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
report.update(mode="full", elapsed_ms=331902)
with open(sys.argv[2], "w", encoding="utf-8") as stream:
    json.dump(report, stream, indent=2)
PY
"$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/full-pass.json" >"$TMP_DIR/full-budget.json"
python3 - "$TMP_DIR/full-budget.json" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    report = json.load(stream)
assert report["status"] == "pass" and report["mode"] == "full", report
assert report["elapsed_ms"] == 331902 and report["budget_ms"] == 600000, report
assert report["strict"] == 0, report
PY

if "$ROOT_DIR/scripts/check-performance-budgets.sh" --summary-json \
  --timing-json "$TMP_DIR/missing.json" >"$TMP_DIR/missing-budget.json"; then
  echo "[FAIL] missing timing must not be reported as a successful observation" >&2
  exit 1
fi

PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" python3 - "$ROOT_DIR" "$TMP_DIR" <<'PY'
import json
import subprocess
import sys
from pathlib import Path
from agent_dev_kit.performance_timing import timing_values

root, temporary = map(Path, sys.argv[1:])
path = temporary / "timing-boundary.json"
command = ["bash", str(root / "scripts/check-performance-budgets.sh"),
           "--summary-json", "--timing-json", str(path)]
valid = {"schema_version": 1, "mode": "full", "elapsed_ms": 331902}

# Formatting and unrelated nested fields never select the measured observation.
for value in (valid, {"tests": [{"mode": "quick", "elapsed_ms": 1}], **valid}):
    for indent in (None, 2):
        path.write_text(json.dumps(value, indent=indent, separators=(",", ":")), encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        report = json.loads(result.stdout)
        assert result.returncode == 0 and report["status"] == "pass", (result, report)
        assert report["mode"] == "full" and report["elapsed_ms"] == 331902, report

invalid = [json.dumps({**valid, "elapsed_ms": value})
           for value in (-1, 0.5, 1000.0, True, "1000", None, 1 << 63)]
invalid.extend([
    '{"schema_version":1,"mode":"full","elapsed_ms":1,"elapsed_ms":999999}',
    '{"schema_version":1,"mode":"quick","mode":"full","elapsed_ms":1}',
    '{"schema_version":1,"mode":"full","elapsed_ms":NaN}',
    '{"schema_version":1,"mode":"full","elapsed_ms":Infinity}',
    '{"schema_version":1,"mode":"full","elapsed_ms":1e999}',
    json.dumps({"tests": [valid]}),
    json.dumps([valid]),
    json.dumps({**valid, "schema_version": True}),
    json.dumps({**valid, "schema_version": 1.0}),
    json.dumps({**valid, "schema_version": 2}),
    json.dumps({"mode": "full", "elapsed_ms": 1}),
    json.dumps({**valid, "mode": "unknown"}),
    json.dumps({**valid, "mode": 'full"\n'}),
    '{"schema_version":1,"mode":"full","elapsed_ms":1,',
])
for raw in invalid:
    path.write_text(raw, encoding="utf-8")
    try:
        timing_values(root / "manifests/adk_performance_budgets.json", path)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid timing was accepted: " + raw)

# Exercise the shell error-report path in both enforcement modes without
# paying a process startup for every equivalent parser rejection above.
for raw in (invalid[1], invalid[7], json.dumps({"tests": [valid]})):
    path.write_text(raw, encoding="utf-8")
    for flags in ([], ["--strict"]):
        result = subprocess.run(command + flags, capture_output=True, text=True, check=False)
        report = json.loads(result.stdout)
        assert result.returncode != 0 and report["status"] == "fail", (raw, result)
        assert report["failures"] > 0, report

# Large valid observations must not wrap shell arithmetic or truncate digits.
path.write_text(json.dumps({**valid, "elapsed_ms": (1 << 63) - 1}), encoding="utf-8")
result = subprocess.run(command, capture_output=True, text=True, check=False)
report = json.loads(result.stdout)
assert result.returncode == 0 and report["status"] == "warn", report
assert report["elapsed_ms"] == (1 << 63) - 1, report

# Explicit interpreter budgets win regardless of JSON array order.
manifest = temporary / "budgets.json"
version = ".".join(map(str, sys.version_info[:2]))
default = {"mode": "full", "max_elapsed_ms": 600000}
specific = {"mode": "full", "python": version, "max_elapsed_ms": 700000}
for choices in ([default, specific], [specific, default]):
    manifest.write_text(json.dumps({"budgets": choices}), encoding="utf-8")
    assert timing_values(manifest, path) == ("full", (1 << 63) - 1, 700000)
for choices in ([default, default], [specific, specific],
                [{**default, "max_elapsed_ms": True}],
                [{**default, "max_elapsed_ms": 600000.0}]):
    manifest.write_text(json.dumps({"budgets": choices}), encoding="utf-8")
    try:
        timing_values(manifest, path)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid or ambiguous budget was accepted")
print("[PASS] strict timing: 4 format/order cases, %d parser rejections, "
      "6 shell rejection cases, integer boundary and 6 budget-selection cases" % len(invalid))
PY

echo "[PASS] performance budgets"
