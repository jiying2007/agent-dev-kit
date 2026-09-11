#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
policy_path = root / "manifests" / "module_size_budget.json"
policy = json.loads(policy_path.read_text(encoding="utf-8"))
assert policy.get("schema") == "adk-module-size-budget/v1", policy
assert policy.get("policy") == "no-new-oversize-and-legacy-monotonic-shrink", policy
default_max = policy.get("default_max_bytes")
assert isinstance(default_max, int) and not isinstance(default_max, bool) and 1 <= default_max <= 30000, policy
exceptions = policy.get("exceptions")
assert isinstance(exceptions, dict) and exceptions, policy

failures = []
seen = set()
source_root = root / "src" / "agent_dev_kit"
for path in sorted(source_root.rglob("*.py")):
    rel = path.relative_to(root).as_posix()
    size = path.stat().st_size
    entry = exceptions.get(rel)
    if entry is None:
        if size > default_max:
            failures.append(f"unregistered oversize Python module: {rel} bytes={size} max={default_max}")
        continue
    seen.add(rel)
    if not isinstance(entry, dict):
        failures.append(f"invalid exception entry: {rel}")
        continue
    baseline = entry.get("baseline_bytes")
    target = entry.get("target_max_bytes")
    hint = entry.get("split_hint")
    if not isinstance(baseline, int) or isinstance(baseline, bool) or baseline <= default_max:
        failures.append(f"invalid legacy baseline: {rel}")
        continue
    if not isinstance(target, int) or isinstance(target, bool) or target != default_max:
        failures.append(f"target must converge to default max: {rel}")
    if not isinstance(hint, str) or not hint.strip():
        failures.append(f"missing split hint: {rel}")
    if size > baseline:
        failures.append(f"legacy module grew: {rel} bytes={size} baseline={baseline}")
    if size <= default_max:
        failures.append(f"legacy exception must be removed after convergence: {rel} bytes={size}")

unknown = sorted(set(exceptions) - seen)
for rel in unknown:
    failures.append(f"exception path is missing or not a Python module: {rel}")

if failures:
    raise SystemExit("\n".join(failures))

print(json.dumps({
    "schema": policy["schema"],
    "status": "pass",
    "default_max_bytes": default_max,
    "legacy_exception_count": len(exceptions),
    "largest_baseline_bytes": max(item["baseline_bytes"] for item in exceptions.values()),
}, sort_keys=True))
PY

echo '[PASS] module size debt is frozen and must shrink monotonically'
