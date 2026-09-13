#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" <<'PY'
import ast
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
    architecture = {}
else:
    if architecture.get("preferred_execution_namespace") != "execution_policy":
        failures.append("preferred execution namespace must be execution_policy")
    if architecture.get("compatibility_execution_namespace") != "runtime_control":
        failures.append("runtime_control must remain the 5.x compatibility namespace")
    if architecture.get("compatibility_sunset") != "future-major-only":
        failures.append("execution namespace compatibility may only sunset in a future major")
    if architecture.get("no_new_support_modules") is not True:
        failures.append("no_new_support_modules must stay enabled")

    transitional_support = architecture.get("transitional_support_modules")
    if not isinstance(transitional_support, list) or not all(
        isinstance(item, str) and item for item in transitional_support
    ):
        failures.append("transitional_support_modules must be a string list")
        transitional_support = []
    transitional_support_set = set(transitional_support)
    if len(transitional_support_set) != len(transitional_support):
        failures.append("transitional_support_modules contains duplicates")

    support_max_count = architecture.get("transitional_support_max_count")
    if support_max_count != 0:
        failures.append("transitional_support_max_count must remain zero after structural convergence")
    if transitional_support_set:
        failures.append(
            "ordinary transitional support debt must remain zero after convergence: "
            + ", ".join(sorted(transitional_support_set))
        )

    compatibility_facades = architecture.get("compatibility_support_facades")
    if not isinstance(compatibility_facades, list) or not compatibility_facades:
        failures.append("compatibility_support_facades must explicitly register retained compatibility seams")
        compatibility_facades = []

    expected_facade = {
        "path": "src/agent_dev_kit/runtime_control/engine_support.py",
        "canonical_owner": "src/agent_dev_kit/execution_policy/contracts.py",
        "namespace": "runtime_control",
        "sunset": "future-major-only",
        "mode": "re-export-only",
    }
    if compatibility_facades != [expected_facade]:
        failures.append("compatibility_support_facades must exactly describe the retained 5.x engine_support seam")

    compatibility_support_set = set()
    for entry in compatibility_facades:
        if not isinstance(entry, dict):
            failures.append("compatibility_support_facades entries must be objects")
            continue
        path_value = entry.get("path")
        owner_value = entry.get("canonical_owner")
        if not isinstance(path_value, str) or not path_value:
            failures.append("compatibility facade path must be a non-empty string")
            continue
        compatibility_support_set.add(path_value)
        if entry.get("namespace") != architecture.get("compatibility_execution_namespace"):
            failures.append(f"compatibility facade namespace mismatch: {path_value}")
        if entry.get("sunset") != architecture.get("compatibility_sunset"):
            failures.append(f"compatibility facade sunset mismatch: {path_value}")
        if entry.get("mode") != "re-export-only":
            failures.append(f"compatibility facade must remain re-export-only: {path_value}")
        facade_path = root / path_value
        owner_path = root / owner_value if isinstance(owner_value, str) else None
        if not facade_path.is_file():
            failures.append(f"registered compatibility facade is missing: {path_value}")
            continue
        if owner_path is None or not owner_path.is_file():
            failures.append(f"compatibility facade canonical owner is missing: {owner_value}")
        if facade_path.stat().st_size > 512:
            failures.append(f"compatibility facade grew beyond re-export budget: {path_value}")

        try:
            tree = ast.parse(facade_path.read_text(encoding="utf-8"), filename=path_value)
        except SyntaxError as exc:
            failures.append(f"compatibility facade is not valid Python: {path_value}: {exc}")
            continue
        if not ast.get_docstring(tree):
            failures.append(f"compatibility facade must document its compatibility role: {path_value}")
        executable = [
            node
            for node in tree.body
            if not (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            )
        ]
        if len(executable) != 1 or not isinstance(executable[0], ast.ImportFrom):
            failures.append(f"compatibility facade may contain only one re-export import: {path_value}")
        else:
            statement = executable[0]
            if (
                statement.level != 2
                or statement.module != "execution_policy.contracts"
                or len(statement.names) != 1
                or statement.names[0].name != "*"
                or statement.names[0].asname is not None
            ):
                failures.append(f"compatibility facade must only re-export execution_policy.contracts: {path_value}")

    if transitional_support_set & compatibility_support_set:
        failures.append("support modules cannot be both transitional debt and compatibility facades")

    actual_support = {
        path.relative_to(root).as_posix()
        for path in source_root.rglob("*_support.py")
    }
    governed_support = transitional_support_set | compatibility_support_set
    unexpected_support = sorted(actual_support - governed_support)
    if unexpected_support:
        failures.append(
            "new *_support.py modules are forbidden; split by owned bounded context instead: "
            + ", ".join(unexpected_support)
        )
    missing_support = sorted(governed_support - actual_support)
    if missing_support:
        failures.append(
            "retired governed support modules must also be removed from policy: "
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
    "transitional_support_debt_count": len(architecture["transitional_support_modules"]),
    "compatibility_support_facade_count": len(architecture["compatibility_support_facades"]),
    "compatibility_sunset": architecture["compatibility_sunset"],
    "preferred_execution_namespace": architecture["preferred_execution_namespace"],
    "largest_baseline_bytes": max(
        (item["baseline_bytes"] for item in exceptions.values()),
        default=0,
    ),
}, sort_keys=True))
PY

echo '[PASS] module size and bounded-context architecture policy pass'
