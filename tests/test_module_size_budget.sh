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
assert isinstance(exceptions, dict), policy

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

architecture = policy.get("architecture_policy")
if not isinstance(architecture, dict):
    failures.append("missing architecture_policy")
else:
    if architecture.get("preferred_execution_namespace") != "execution_policy":
        failures.append("preferred execution namespace must be execution_policy")
    if architecture.get("compatibility_execution_namespace") != "runtime_control":
        failures.append("runtime_control must remain the 5.x compatibility namespace")
    if architecture.get("compatibility_sunset") != "future-major-only":
        failures.append("execution namespace compatibility may only sunset in a future major")
    if architecture.get("no_new_support_modules") is not True:
        failures.append("no_new_support_modules must stay enabled")

    allowed_support = architecture.get("transitional_support_modules")
    if not isinstance(allowed_support, list) or not all(isinstance(item, str) and item for item in allowed_support):
        failures.append("transitional_support_modules must be a non-empty string list")
        allowed_support = []
    allowed_support_set = set(allowed_support)
    if len(allowed_support_set) != len(allowed_support):
        failures.append("transitional_support_modules contains duplicates")

    actual_support = {
        path.relative_to(root).as_posix()
        for path in source_root.rglob("*_support.py")
    }
    unexpected_support = sorted(actual_support - allowed_support_set)
    if unexpected_support:
        failures.append(
            "new *_support.py modules are forbidden; split by owned bounded context instead: "
            + ", ".join(unexpected_support)
        )
    missing_support = sorted(allowed_support_set - actual_support)
    if missing_support:
        failures.append(
            "retired transitional support modules must also be removed from the policy: "
            + ", ".join(missing_support)
        )

    preferred = source_root / architecture.get("preferred_execution_namespace", "") / "__init__.py"
    compatibility = source_root / architecture.get("compatibility_execution_namespace", "") / "__init__.py"
    if not preferred.is_file():
        failures.append("missing preferred execution_policy package")
    if not compatibility.is_file():
        failures.append("missing runtime_control compatibility package")

    metrics = architecture.get("design_metrics")
    expected_metrics = {
        "bounded-context",
        "dependency-direction",
        "import-fan-out",
        "public-api-surface",
        "responsibility-count",
    }
    if not isinstance(metrics, list) or set(metrics) != expected_metrics:
        failures.append("architecture design_metrics must define the reviewed second-stage metrics")

if failures:
    raise SystemExit("\n".join(failures))

print(json.dumps({
    "schema": policy["schema"],
    "status": "pass",
    "default_max_bytes": default_max,
    "legacy_exception_count": len(exceptions),
    "support_module_count": len(list(source_root.rglob("*_support.py"))),
    "preferred_execution_namespace": architecture["preferred_execution_namespace"],
    "largest_baseline_bytes": max(
        (item["baseline_bytes"] for item in exceptions.values()),
        default=0,
    ),
}, sort_keys=True))
PY

echo '[PASS] module size and bounded-context architecture policy pass'
