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

    actual_support = {
        path.relative_to(root).as_posix()
        for path in source_root.rglob("*_support.py")
    }
    unexpected_support = sorted(actual_support - transitional_support_set)
    if unexpected_support:
        failures.append(
            "new *_support.py modules are forbidden; split by owned bounded context instead: "
            + ", ".join(unexpected_support)
        )
    missing_support = sorted(transitional_support_set - actual_support)
    if missing_support:
        failures.append(
            "retired governed support modules must also be removed from policy: "
            + ", ".join(missing_support)
        )

    repository_certification = source_root / "repository_evaluation.py"
    repository_contract = source_root / "repository_evaluation_contract.py"
    if not repository_contract.is_file():
        failures.append("missing repository_evaluation_contract bounded context")
    else:
        try:
            certification_tree = ast.parse(
                repository_certification.read_text(encoding="utf-8"),
                filename=str(repository_certification),
            )
            contract_tree = ast.parse(
                repository_contract.read_text(encoding="utf-8"),
                filename=str(repository_contract),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse repository evaluation bounded contexts: {exc}")
        else:
            certification_defs = {
                node.name for node in certification_tree.body if isinstance(node, ast.FunctionDef)
            }
            contract_defs = {
                node.name for node in contract_tree.body if isinstance(node, ast.FunctionDef)
            }
            leaked_contract_defs = sorted(
                {"load_repository_contract", "repository_plan"} & certification_defs
            )
            if leaked_contract_defs:
                failures.append(
                    "repository certification must not own contract/plan functions: "
                    + ", ".join(leaked_contract_defs)
                )
            missing_contract_defs = sorted(
                {"load_repository_contract", "repository_plan"} - contract_defs
            )
            if missing_contract_defs:
                failures.append(
                    "repository contract bounded context is incomplete: "
                    + ", ".join(missing_contract_defs)
                )
            reverse_imports = [
                node
                for node in ast.walk(contract_tree)
                if isinstance(node, ast.ImportFrom)
                and node.module == "repository_evaluation"
            ]
            if reverse_imports:
                failures.append(
                    "repository contract must not depend on repository certification"
                )

    preferred = source_root / architecture.get("preferred_execution_namespace", "") / "__init__.py"
    retired = source_root / "runtime_control"
    if not preferred.is_file():
        failures.append("missing preferred execution_policy package")
    if retired.exists():
        failures.append("retired runtime_control compatibility package must not exist")

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

    max_import_fan_out = architecture.get("max_import_fan_out")
    if (
        not isinstance(max_import_fan_out, int)
        or isinstance(max_import_fan_out, bool)
        or not 1 <= max_import_fan_out <= 35
    ):
        failures.append("max_import_fan_out must be an integer between 1 and 35")
        max_import_fan_out = 0

    observed_import_fan_out = 0
    import_fan_out_hotspot = ""
    for path in sorted(source_root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse Python import graph: {path.relative_to(root)}: {exc}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    imports.add("." * node.level + (node.module or "<package>"))
                elif node.module:
                    imports.add(node.module.split(".", 1)[0])
        fan_out = len(imports)
        if fan_out > observed_import_fan_out:
            observed_import_fan_out = fan_out
            import_fan_out_hotspot = path.relative_to(root).as_posix()
        if max_import_fan_out and fan_out > max_import_fan_out:
            failures.append(
                f"Python import fan-out exceeds reviewed budget: "
                f"{path.relative_to(root).as_posix()} observed={fan_out} max={max_import_fan_out}"
            )

if failures:
    raise SystemExit("\n".join(failures))

print(json.dumps({
    "schema": policy["schema"],
    "status": "pass",
    "default_max_bytes": default_max,
    "legacy_exception_count": len(exceptions),
    "support_module_count": len(list(source_root.rglob("*_support.py"))),
    "transitional_support_debt_count": len(architecture["transitional_support_modules"]),
    "preferred_execution_namespace": architecture["preferred_execution_namespace"],
    "max_import_fan_out": architecture["max_import_fan_out"],
    "observed_max_import_fan_out": observed_import_fan_out,
    "import_fan_out_hotspot": import_fan_out_hotspot,
    "largest_baseline_bytes": max(
        (item["baseline_bytes"] for item in exceptions.values()),
        default=0,
    ),
}, sort_keys=True))
PY

echo '[PASS] module size and bounded-context architecture policy pass'
