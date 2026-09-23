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

    readiness_orchestrator = source_root / "readiness.py"
    readiness_tools = source_root / "readiness_tools.py"
    if not readiness_tools.is_file():
        failures.append("missing readiness_tools bounded context")
    else:
        try:
            readiness_tree = ast.parse(
                readiness_orchestrator.read_text(encoding="utf-8"),
                filename=str(readiness_orchestrator),
            )
            readiness_tools_tree = ast.parse(
                readiness_tools.read_text(encoding="utf-8"),
                filename=str(readiness_tools),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse readiness bounded contexts: {exc}")
        else:
            readiness_defs = {
                node.name for node in readiness_tree.body if isinstance(node, ast.FunctionDef)
            }
            tool_defs = {
                node.name for node in readiness_tools_tree.body if isinstance(node, ast.FunctionDef)
            }
            if "_evaluate_tools" in readiness_defs:
                failures.append("readiness orchestrator must not own tool/permission evaluation")
            if "_evaluate_tools" not in tool_defs:
                failures.append("readiness_tools must own tool/permission evaluation")
            imports_tools = any(
                isinstance(node, ast.ImportFrom)
                and node.module == "readiness_tools"
                and any(alias.name == "_evaluate_tools" for alias in node.names)
                for node in readiness_tree.body
            )
            if not imports_tools:
                failures.append("readiness orchestrator must depend on readiness_tools authority")
            reverse_imports = [
                node
                for node in ast.walk(readiness_tools_tree)
                if isinstance(node, ast.ImportFrom)
                and node.module == "readiness"
            ]
            if reverse_imports:
                failures.append("readiness_tools must not depend on readiness orchestrator")

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

    runtime_evaluation = source_root / "evaluation.py"
    evaluation_runtime_authority = source_root / "evaluation_runtime.py"
    effect_evaluation = source_root / "effect_evaluation.py"
    evaluation_cli = source_root / "evaluation_cli.py"
    if not effect_evaluation.is_file():
        failures.append("missing effect_evaluation bounded context")
    else:
        try:
            runtime_eval_tree = ast.parse(
                runtime_evaluation.read_text(encoding="utf-8"),
                filename=str(runtime_evaluation),
            )
            evaluation_runtime_authority_tree = ast.parse(
                evaluation_runtime_authority.read_text(encoding="utf-8"),
                filename=str(evaluation_runtime_authority),
            )
            effect_eval_tree = ast.parse(
                effect_evaluation.read_text(encoding="utf-8"),
                filename=str(effect_evaluation),
            )
            evaluation_cli_tree = ast.parse(
                evaluation_cli.read_text(encoding="utf-8"),
                filename=str(evaluation_cli),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse evaluation bounded contexts: {exc}")
        else:
            runtime_eval_defs = {
                node.name for node in runtime_eval_tree.body if isinstance(node, ast.FunctionDef)
            }
            effect_eval_defs = {
                node.name for node in effect_eval_tree.body if isinstance(node, ast.FunctionDef)
            }
            if "run_effect_eval" in runtime_eval_defs:
                failures.append("runtime evaluation must not own deterministic effect evaluation")
            if "run_effect_eval" not in effect_eval_defs:
                failures.append("effect_evaluation must own run_effect_eval")
            reverse_imports = [
                node
                for node in ast.walk(effect_eval_tree)
                if isinstance(node, ast.ImportFrom)
                and node.module == "evaluation"
            ]
            if reverse_imports:
                failures.append("effect_evaluation must not depend on runtime evaluation")
            cli_effect_import = any(
                isinstance(node, ast.ImportFrom)
                and node.module == "effect_evaluation"
                and any(alias.name == "run_effect_eval" for alias in node.names)
                for node in evaluation_cli_tree.body
            )
            if not cli_effect_import:
                failures.append("evaluation CLI must consume effect_evaluation authority directly")

    retired_evaluation_runtime_exports = {
        node.name
        for node in evaluation_runtime_authority_tree.body
        if isinstance(node, ast.FunctionDef)
    } | {"RUNTIME_THRESHOLDS"}
    evaluation_named_runtime_imports = [
        alias.name
        for node in runtime_eval_tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module == "evaluation_runtime"
        for alias in node.names
        if alias.name in retired_evaluation_runtime_exports
    ]
    if evaluation_named_runtime_imports:
        failures.append(
            "evaluation must not re-export evaluation_runtime authority: "
            + ", ".join(sorted(evaluation_named_runtime_imports))
        )
    evaluation_module_boundary = any(
        isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module is None
        and any(
            alias.name == "evaluation_runtime" and alias.asname == "runtime_eval"
            for alias in node.names
        )
        for node in runtime_eval_tree.body
    )
    if not evaluation_module_boundary:
        failures.append("evaluation must consume evaluation_runtime through private module boundary")

    evaluation_runtime_import_leaks = []
    for python_path in sorted(source_root.rglob("*.py")):
        try:
            module_tree = ast.parse(
                python_path.read_text(encoding="utf-8"),
                filename=str(python_path),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse evaluation consumer {python_path}: {exc}")
            continue
        for node in ast.walk(module_tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module not in {"evaluation", "agent_dev_kit.evaluation"}:
                continue
            leaked = sorted(
                alias.name
                for alias in node.names
                if alias.name in retired_evaluation_runtime_exports
            )
            if leaked:
                evaluation_runtime_import_leaks.append(
                    f"{python_path.relative_to(root).as_posix()}:{','.join(leaked)}"
                )
    if evaluation_runtime_import_leaks:
        failures.append(
            "evaluation consumers must import runtime authority directly: "
            + "; ".join(evaluation_runtime_import_leaks)
        )

    public_cli = source_root / "cli.py"
    delivery_cli = source_root / "delivery_cli.py"
    try:
        public_cli_tree = ast.parse(
            public_cli.read_text(encoding="utf-8"),
            filename=str(public_cli),
        )
        delivery_cli_tree = ast.parse(
            delivery_cli.read_text(encoding="utf-8"),
            filename=str(delivery_cli),
        )
    except (OSError, SyntaxError, UnicodeError) as exc:
        failures.append(f"cannot parse delivery CLI bounded context: {exc}")
    else:
        delivery_handlers = {
            "_cmd_export",
            "_cmd_install",
            "_cmd_target",
            "_cmd_lock",
            "_cmd_release",
        }
        public_defs = {
            node.name
            for node in public_cli_tree.body
            if isinstance(node, ast.FunctionDef)
        }
        delivery_defs = {
            node.name
            for node in delivery_cli_tree.body
            if isinstance(node, ast.FunctionDef)
        }
        leaked_handlers = sorted(delivery_handlers & public_defs)
        if leaked_handlers:
            failures.append(
                "public CLI must not own delivery lifecycle handlers: "
                + ", ".join(leaked_handlers)
            )
        missing_handlers = sorted(delivery_handlers - delivery_defs)
        if missing_handlers:
            failures.append(
                "delivery_cli bounded context is incomplete: "
                + ", ".join(missing_handlers)
            )
        forbidden_delivery_imports = {"compiler", "installer", "locking", "release", "targets"}
        direct_delivery_imports = sorted({
            node.module
            for node in public_cli_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module in forbidden_delivery_imports
        })
        if direct_delivery_imports:
            failures.append(
                "public CLI must delegate delivery dependencies: "
                + ", ".join(direct_delivery_imports)
            )
        delegates_delivery = any(
            isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "delivery_cli"
            and any(alias.name == "main" and alias.asname == "delivery_main" for alias in node.names)
            for node in public_cli_tree.body
        )
        if not delegates_delivery:
            failures.append("public CLI must delegate through delivery_cli.main")

    retired_installer = source_root / "installer.py"
    installation_contract = source_root / "installation_contract.py"
    installation_plan = source_root / "installation_plan.py"
    installation_transaction = source_root / "installation_transaction.py"
    if retired_installer.exists():
        failures.append("installer monolith must remain retired")
    if not all(path.is_file() for path in (
        installation_contract,
        installation_plan,
        installation_transaction,
    )):
        failures.append("installation bounded contexts are incomplete")
    else:
        try:
            install_contract_tree = ast.parse(
                installation_contract.read_text(encoding="utf-8"),
                filename=str(installation_contract),
            )
            install_plan_tree = ast.parse(
                installation_plan.read_text(encoding="utf-8"),
                filename=str(installation_plan),
            )
            install_tx_tree = ast.parse(
                installation_transaction.read_text(encoding="utf-8"),
                filename=str(installation_transaction),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse installation bounded contexts: {exc}")
        else:
            contract_defs = {
                node.name for node in install_contract_tree.body
                if isinstance(node, ast.FunctionDef)
            }
            plan_defs = {
                node.name for node in install_plan_tree.body
                if isinstance(node, ast.FunctionDef)
            }
            tx_defs = {
                node.name for node in install_tx_tree.body
                if isinstance(node, ast.FunctionDef)
            }
            if not {"_read_receipt", "_load_receipt", "_receipt_digest"} <= contract_defs:
                failures.append("installation_contract must own receipt contract primitives")
            if not {"create_plan", "write_plan", "validate_plan"} <= plan_defs:
                failures.append("installation_plan must own plan lifecycle")
            if not {"apply_plan", "rollback"} <= tx_defs:
                failures.append("installation_transaction must own apply/rollback lifecycle")
            plan_reverse = [
                node for node in ast.walk(install_plan_tree)
                if isinstance(node, ast.ImportFrom)
                and node.module == "installation_transaction"
            ]
            contract_reverse = [
                node for node in ast.walk(install_contract_tree)
                if isinstance(node, ast.ImportFrom)
                and node.module in {"installation_plan", "installation_transaction"}
            ]
            if plan_reverse:
                failures.append("installation_plan must not depend on installation_transaction")
            if contract_reverse:
                failures.append("installation_contract must not depend on plan/transaction")
            tx_imports_plan = any(
                isinstance(node, ast.ImportFrom)
                and node.level == 1
                and node.module is None
                and any(alias.name == "installation_plan" for alias in node.names)
                for node in install_tx_tree.body
            )
            if not tx_imports_plan:
                failures.append("installation_transaction must consume installation_plan authority")
            delivery_plan_import = any(
                isinstance(node, ast.ImportFrom)
                and node.level == 1
                and node.module == "installation_plan"
                and {alias.name for alias in node.names} >= {"create_plan", "write_plan"}
                for node in delivery_cli_tree.body
            )
            delivery_tx_import = any(
                isinstance(node, ast.ImportFrom)
                and node.level == 1
                and node.module == "installation_transaction"
                and {alias.name for alias in node.names} >= {"apply_plan", "rollback"}
                for node in delivery_cli_tree.body
            )
            if not delivery_plan_import or not delivery_tx_import:
                failures.append(
                    "delivery_cli must consume installation plan/transaction authorities directly"
                )

    agent_platform_authority = source_root / "agent_platform.py"
    agent_platform_cli = source_root / "agent_platform_cli.py"
    try:
        platform_authority_tree = ast.parse(
            agent_platform_authority.read_text(encoding="utf-8"),
            filename=str(agent_platform_authority),
        )
        platform_cli_tree = ast.parse(
            agent_platform_cli.read_text(encoding="utf-8"),
            filename=str(agent_platform_cli),
        )
    except (OSError, SyntaxError, UnicodeError) as exc:
        failures.append(f"cannot parse Agent Platform authority boundary: {exc}")
    else:
        platform_authority_defs = {
            node.name
            for node in platform_authority_tree.body
            if isinstance(node, ast.FunctionDef)
        }
        named_platform_imports = [
            alias.name
            for node in platform_cli_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "agent_platform"
            for alias in node.names
            if alias.name in platform_authority_defs
        ]
        if named_platform_imports:
            failures.append(
                "agent_platform_cli must not re-export platform authority: "
                + ", ".join(sorted(named_platform_imports))
            )
        platform_module_boundary = any(
            isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module is None
            and any(
                alias.name == "agent_platform" and alias.asname == "platform_domain"
                for alias in node.names
            )
            for node in platform_cli_tree.body
        )
        if not platform_module_boundary:
            failures.append(
                "agent_platform_cli must consume agent_platform through private module boundary"
            )

    retired_manifest_cli_exports = {
        "ManifestContract",
        "canonical_manifest",
        "load_canonical_manifest",
        "load_contract",
    }
    manifest_cli_import_leaks = []
    for python_path in sorted(source_root.rglob("*.py")):
        try:
            module_tree = ast.parse(
                python_path.read_text(encoding="utf-8"),
                filename=str(python_path),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse manifest consumer {python_path}: {exc}")
            continue
        for node in ast.walk(module_tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module not in {"manifest_contract", "agent_dev_kit.manifest_contract"}:
                continue
            leaked = sorted(
                alias.name for alias in node.names if alias.name in retired_manifest_cli_exports
            )
            if leaked:
                manifest_cli_import_leaks.append(
                    f"{python_path.relative_to(root).as_posix()}:{','.join(leaked)}"
                )
    if manifest_cli_import_leaks:
        failures.append(
            "manifest_contract CLI must not re-export domain authority: "
            + "; ".join(manifest_cli_import_leaks)
        )

    retired_agent_value_exports = {
        "CONTRACT_SCHEMA_VERSION",
        "RECEIPT_SCHEMA_VERSION",
        "MEASUREMENT_SCHEMA_VERSION",
        "EvidenceVerifier",
        "load_contract",
        "validate_contract",
        "validate_receipt",
    }
    agent_value_import_leaks = []
    for python_path in sorted(source_root.rglob("*.py")):
        try:
            module_tree = ast.parse(
                python_path.read_text(encoding="utf-8"),
                filename=str(python_path),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse agent-value consumer {python_path}: {exc}")
            continue
        for node in ast.walk(module_tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module not in {"agent_value", "agent_dev_kit.agent_value"}:
                continue
            leaked = sorted(
                alias.name for alias in node.names if alias.name in retired_agent_value_exports
            )
            if leaked:
                agent_value_import_leaks.append(
                    f"{python_path.relative_to(root).as_posix()}:{','.join(leaked)}"
                )
    if agent_value_import_leaks:
        failures.append(
            "agent_value must not re-export contract authority: "
            + "; ".join(agent_value_import_leaks)
        )

    execution_policy_root = source_root / "execution_policy"
    execution_engine = execution_policy_root / "engine.py"
    execution_reducer = execution_policy_root / "reducer.py"
    execution_decision = execution_policy_root / "decision.py"
    execution_public = execution_policy_root / "__init__.py"
    if execution_engine.exists():
        failures.append("execution_policy engine monolith must remain retired")
    if not execution_reducer.is_file() or not execution_decision.is_file():
        failures.append("execution_policy reducer and decision bounded contexts are required")
    else:
        try:
            reducer_tree = ast.parse(
                execution_reducer.read_text(encoding="utf-8"),
                filename=str(execution_reducer),
            )
            decision_tree = ast.parse(
                execution_decision.read_text(encoding="utf-8"),
                filename=str(execution_decision),
            )
            public_tree = ast.parse(
                execution_public.read_text(encoding="utf-8"),
                filename=str(execution_public),
            )
        except (OSError, SyntaxError, UnicodeError) as exc:
            failures.append(f"cannot parse execution_policy bounded contexts: {exc}")
        else:
            reducer_defs = {
                node.name for node in reducer_tree.body if isinstance(node, ast.FunctionDef)
            }
            decision_defs = {
                node.name for node in decision_tree.body if isinstance(node, ast.FunctionDef)
            }
            if "reduce_events" not in reducer_defs or "evaluate" in reducer_defs:
                failures.append("execution_policy reducer must exclusively own reduce_events")
            if "evaluate" not in decision_defs or "reduce_events" in decision_defs:
                failures.append("execution_policy decision must exclusively own evaluate")
            cross_imports = []
            for label, tree, forbidden in (
                ("reducer", reducer_tree, "decision"),
                ("decision", decision_tree, "reducer"),
            ):
                if any(
                    isinstance(node, ast.ImportFrom)
                    and node.level == 1
                    and node.module == forbidden
                    for node in ast.walk(tree)
                ):
                    cross_imports.append(label)
            if cross_imports:
                failures.append(
                    "execution_policy reducer/decision contexts must remain independent: "
                    + ", ".join(cross_imports)
                )
            public_imports = {
                (node.module, alias.name)
                for node in public_tree.body
                if isinstance(node, ast.ImportFrom) and node.level == 1
                for alias in node.names
            }
            if ("reducer", "reduce_events") not in public_imports:
                failures.append("execution_policy public API must import reduce_events from reducer")
            if ("decision", "evaluate") not in public_imports:
                failures.append("execution_policy public API must import evaluate from decision")

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
