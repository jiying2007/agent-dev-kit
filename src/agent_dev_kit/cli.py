"""Public ADK 3.x command-line interface."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Optional, Sequence

from .campaign import campaign_markdown, campaign_plan, check_campaign, run_campaign
from .compiler import export_assets
from .doctor import run_doctor
from .evaluation import (
    compare_runtime_reports,
    eval_markdown,
    load_tasks,
    run_deterministic,
    run_effect_eval,
    run_runtime,
    runtime_plan,
)
from .installer import apply_plan, create_plan, rollback, write_plan
from .locking import clear_target_lock, target_lock_status
from .matcher import main as matcher_main
from .model import Manifest, ManifestError
from .quality import benchmark_markdown, run_benchmark, security_check
from .readiness import readiness_markdown, run_harness_readiness
from .release import build_release, check_release, publish_release, rehearse_release
from .repository_evaluation import certify_repository_report, repository_plan
from .targets import TargetUsageError, check_targets, run_target_smoke
from .task_cost import TASK_TYPES as TASK_COST_TYPES, classify_task_cost, validate_skill_usage


def _discover_root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    candidates = [Path.cwd()] + list(Path(__file__).resolve().parents)
    for candidate in candidates:
        if (candidate / "manifest.json").is_file() and (candidate / "scripts" / "devkit.sh").is_file():
            return candidate.resolve()
    return Path.cwd().resolve()


ROOT = _discover_root()
DEFAULT_TASKS = ROOT / "tests" / "fixtures" / "product_eval_tasks.jsonl"


LEGACY_COMMANDS = {
    "runtime-boundary": ["scripts/check-runtime-boundary.sh"],
    "token-budget": ["scripts/check-token-budget.sh"],
    "codify-governance": ["scripts/check-codify-governance.sh"],
    "knowledge-compile": ["scripts/check-knowledge-compile-model.sh"],
    "reuse-before-rebuild": ["scripts/check-reuse-before-rebuild.sh"],
    "context-experience": ["scripts/check-context-experience-patterns.sh"],
    "official-docs-governance": ["scripts/check-official-docs-governance.sh"],
    "runtime-capabilities": ["scripts/check-runtime-capabilities.sh"],
    "harness-loop-engineering": ["scripts/check-harness-loop-engineering-contracts.sh"],
    "workflow-closure": ["scripts/check-workflow-closure.sh"],
    "asset-taxonomy": ["scripts/check-asset-taxonomy.sh"],
    "file-modes": ["scripts/check-file-modes.sh", str(ROOT)],
    "propose": ["scripts/workflow.sh", "propose"],
    "apply": ["scripts/workflow.sh", "apply"],
    "verify": ["scripts/workflow.sh", "verify"],
    "review": ["scripts/workflow.sh", "review"],
    "archive": ["scripts/workflow.sh", "archive"],
    "bridge": ["scripts/openspec-bridge.sh"],
    "evidence": ["scripts/evidence-index.sh"],
    "health": ["scripts/health-check.sh"],
    "backup": ["scripts/backup-rollback.sh"],
    "version": ["scripts/version-manager.sh"],
}


PUBLIC_COMMANDS = [
    ("validate", "校验 v3 manifest 与资产结构"),
    ("doctor", "只读检查运行环境与 M5-ready 前置条件"),
    ("catalog", "生成或检索 Agent/Skill 目录"),
    ("match", "匹配 Skill 路由"),
    ("export", "确定性导出 direct target 资产"),
    ("target", "检查或执行 direct target contract smoke"),
    ("install", "plan/apply/rollback 安装事务"),
    ("lock", "检查或显式清理 target writer lock"),
    ("benchmark", "运行或展示资产平台性能基准"),
    ("security", "执行阻断式资产与发布安全检查"),
    ("eval", "运行确定性或真实运行时评测"),
    ("release", "检查、构建或发布制品"),
    ("test", "运行完整回归测试"),
    ("goal", "检查 ADK 目标契约"),
    ("capability", "检查 ADK 能力健康"),
    ("harness", "检查目标仓 Harness readiness"),
    ("task-cost", "生成确定性任务成本与执行预算 receipt"),
] + [(name, "治理兼容入口") for name in LEGACY_COMMANDS]


def _manifest() -> Manifest:
    if not (ROOT / "manifest.json").is_file():
        raise ManifestError("ADK asset root not found; run inside a checkout or set ADK_ROOT")
    return Manifest.load(ROOT)


def _json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


def _write_json(path: Path, value: Any) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _write_text(path: Path, value: str) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="." + path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
        delete=False,
    ) as stream:
        temp = Path(stream.name)
        stream.write(value)
    try:
        os.replace(str(temp), str(path))
    finally:
        temp.unlink(missing_ok=True)


def _help() -> None:
    print("Usage:")
    print("  ./scripts/devkit.sh <command> [options]")
    print("")
    print("Commands:")
    for name, description in PUBLIC_COMMANDS:
        print("  {:24s} {}".format(name, description))


def _run_legacy(command: str, argv: Sequence[str]) -> int:
    parts = LEGACY_COMMANDS[command]
    script = ROOT / parts[0]
    return subprocess.call(["bash", str(script)] + parts[1:] + list(argv), cwd=str(ROOT))


def _cmd_validate(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh validate")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    manifest = _manifest()
    failures = manifest.validate(strict=args.strict and not args.quick)
    if failures:
        if args.summary_json:
            _json({"schema_version": 1, "status": "fail", "failures": failures})
        else:
            for failure in failures:
                print("[FAIL] {}".format(failure), file=sys.stderr)
        return 1
    mirror_check = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_manifest_sync.py")],
        cwd=str(ROOT),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if mirror_check.returncode != 0:
        message = mirror_check.stderr.strip() or mirror_check.stdout.strip()
        if message:
            print(message, file=sys.stderr)
        return mirror_check.returncode
    legacy_args = list(argv)
    completed = subprocess.run(
        ["bash", str(ROOT / "scripts" / "validate-assets.sh")] + legacy_args,
        cwd=str(ROOT),
        check=False,
    )
    return completed.returncode


def _cmd_doctor(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh doctor")
    parser.add_argument("--require-runtime", action="append", choices=("codex", "claude"), default=[])
    parser.add_argument("--target")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    result = run_doctor(
        _manifest(),
        required_runtimes=args.require_runtime,
        target=Path(args.target) if args.target else None,
    )
    if args.summary_json:
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


def _cmd_catalog(argv: Sequence[str]) -> int:
    return subprocess.call(["bash", str(ROOT / "scripts" / "catalog-assets.sh")] + list(argv), cwd=str(ROOT))


def _cmd_match(argv: Sequence[str]) -> int:
    return matcher_main(argv)


def _cmd_export(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh export")
    parser.add_argument("--target", required=True)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--extra-profile", action="append", default=[])
    parser.add_argument("--with-optional-skill", action="append", default=[])
    parser.add_argument("--asset-kind", choices=("agent", "skill"))
    parser.add_argument("--out", default="dist")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--lock-timeout", type=float, default=0.0)
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    manifest = _manifest()
    profiles = [args.profile or manifest.default_profile] + args.extra_profile
    result = export_assets(
        manifest,
        target=args.target,
        output_root=Path(args.out),
        profiles=profiles,
        optional_skills=args.with_optional_skill,
        asset_kind=args.asset_kind,
        clean=args.clean,
        dry_run=args.dry_run,
        lock_timeout_seconds=args.lock_timeout,
    )
    if args.summary_json:
        _json(result)
    else:
        print("Export {}: {} agents, {} skills -> {}".format(result["status"], result["agents"], result["skills"], result["output"]))
    return 0


def _cmd_install(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh install")
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--tool", required=True)
    plan.add_argument("--target", required=True)
    plan.add_argument("--profile", default=None)
    plan.add_argument("--extra-profile", action="append", default=[])
    plan.add_argument("--with-optional-skill", action="append", default=[])
    plan.add_argument("--asset-kind", choices=("agent", "skill"))
    plan.add_argument("--mode", choices=("copy", "symlink"), default="copy")
    plan.add_argument("--output", required=True)
    plan.add_argument("--ttl-minutes", type=int, default=60)
    plan.add_argument("--summary-json", action="store_true")
    apply = sub.add_parser("apply")
    apply.add_argument("--plan", required=True)
    apply.add_argument("--lock-timeout", type=float, default=0.0)
    apply.add_argument("--summary-json", action="store_true")
    undo = sub.add_parser("rollback")
    undo.add_argument("--receipt", required=True)
    undo.add_argument("--lock-timeout", type=float, default=0.0)
    undo.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "plan":
        manifest = _manifest()
        profiles = [args.profile or manifest.default_profile] + args.extra_profile
        result = create_plan(
            manifest,
            args.tool,
            args.target,
            profiles,
            args.with_optional_skill,
            args.mode,
            args.ttl_minutes,
            args.asset_kind,
        )
        write_plan(result, Path(args.output))
        if args.summary_json:
            _json(result)
        else:
            print("Install plan {}: {} operations, {} conflicts -> {}".format(result["status"], len(result["operations"]), len(result["conflicts"]), args.output))
        return 0 if result["status"] == "ready" else 2
    if args.action == "apply":
        manifest = _manifest()
        result = apply_plan(manifest, Path(args.plan).resolve(), args.lock_timeout)
    else:
        result = rollback(Path(args.receipt).resolve(), args.lock_timeout)
    if args.summary_json:
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_target(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh target")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("check")
    selector = check.add_mutually_exclusive_group(required=True)
    selector.add_argument("--target")
    selector.add_argument("--all", action="store_true")
    check.add_argument("--level", choices=("static",), default="static")
    check.add_argument("--summary-json", action="store_true")
    smoke = sub.add_parser("smoke")
    smoke.add_argument("--target", required=True)
    smoke.add_argument("--stage", choices=("discovery", "load", "trigger", "permission"), required=True)
    smoke.add_argument("--profile")
    smoke.add_argument("--asset-kind", choices=("agent", "skill"))
    smoke.add_argument("--timeout-seconds", type=int, default=120)
    smoke.add_argument("--summary-json", action="store_true")
    smoke.add_argument("--runtime-command", nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args(argv)
    manifest = _manifest()
    if args.action == "check":
        result = check_targets(manifest, None if args.all else args.target)
    else:
        result = run_target_smoke(
            manifest,
            args.target,
            args.stage,
            args.runtime_command,
            profile=args.profile,
            asset_kind=args.asset_kind,
            timeout_seconds=args.timeout_seconds,
        )
    if getattr(args, "summary_json", False):
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "pass":
        return 0
    if result.get("status") == "not-run":
        return 2
    return 1


def _cmd_lock(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh lock")
    sub = parser.add_subparsers(dest="action", required=True)
    status = sub.add_parser("status")
    status.add_argument("--target", required=True)
    status.add_argument("--summary-json", action="store_true")
    clear = sub.add_parser("clear")
    clear.add_argument("--target", required=True)
    clear.add_argument("--expected-lock-id", required=True)
    clear.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "status":
        result = target_lock_status(Path(args.target))
    else:
        result = clear_target_lock(Path(args.target), args.expected_lock_id)
    if args.summary_json:
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_benchmark(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh benchmark")
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--iterations", type=int, default=5)
    run.add_argument("--output")
    run.add_argument("--summary-json", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("--input", required=True)
    report.add_argument("--output")
    args = parser.parse_args(argv)
    if args.action == "run":
        value = run_benchmark(_manifest(), args.iterations)
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value["status"] == "pass" else 1
    value = json.loads(Path(args.input).read_text(encoding="utf-8"))
    text = benchmark_markdown(value)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def _cmd_security(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh security")
    parser.add_argument("action", choices=("check",))
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    result = security_check(_manifest())
    if args.summary_json:
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "fail" else 0


def _cmd_eval(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh eval")
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run")
    run.add_argument("--suite", choices=("deterministic", "runtime"), default="deterministic")
    run.add_argument("--tasks", default=str(DEFAULT_TASKS))
    run.add_argument("--limit", type=int)
    run.add_argument("--runtime", choices=("codex", "claude"))
    run.add_argument("--model")
    run.add_argument("--condition", choices=("baseline", "adk"), default="adk")
    run.add_argument("--execute", action="store_true")
    run.add_argument("--output")
    run.add_argument("--summary-json", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("--input", required=True)
    report.add_argument("--output")
    compare = sub.add_parser("compare")
    compare.add_argument("--baseline", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--output")
    compare.add_argument("--summary-json", action="store_true")
    effect = sub.add_parser("effect")
    effect.add_argument("--contract", default=str(ROOT / "manifests" / "effect_eval_contract.json"))
    effect.add_argument("--output")
    effect.add_argument("--summary-json", action="store_true")
    repository = sub.add_parser("repository")
    repository_sub = repository.add_subparsers(dest="repository_action", required=True)
    repository_plan_parser = repository_sub.add_parser("plan")
    repository_plan_parser.add_argument(
        "--contract", default=str(ROOT / "manifests" / "repository_runtime_eval_contract.json")
    )
    repository_plan_parser.add_argument("--output")
    repository_plan_parser.add_argument("--summary-json", action="store_true")
    repository_certify_parser = repository_sub.add_parser("certify")
    repository_certify_parser.add_argument(
        "--contract", default=str(ROOT / "manifests" / "repository_runtime_eval_contract.json")
    )
    repository_certify_parser.add_argument("--report", required=True)
    repository_certify_parser.add_argument("--output")
    repository_certify_parser.add_argument("--summary-json", action="store_true")
    campaign = sub.add_parser("campaign")
    campaign_sub = campaign.add_subparsers(dest="campaign_action", required=True)
    campaign_plan_parser = campaign_sub.add_parser("plan")
    campaign_plan_parser.add_argument(
        "--contract", default=str(ROOT / "manifests" / "software_m5_eval_contract_rc4.json")
    )
    campaign_plan_parser.add_argument("--output")
    campaign_plan_parser.add_argument("--summary-json", action="store_true")
    campaign_run_parser = campaign_sub.add_parser("run")
    campaign_run_parser.add_argument(
        "--contract", default=str(ROOT / "manifests" / "software_m5_eval_contract_rc4.json")
    )
    campaign_run_parser.add_argument("--state-dir", required=True)
    campaign_run_parser.add_argument("--execute", action="store_true")
    campaign_run_parser.add_argument("--resume", action="store_true")
    campaign_run_parser.add_argument("--approve-budget-usd", type=float)
    campaign_run_parser.add_argument("--output")
    campaign_run_parser.add_argument("--summary-json", action="store_true")
    campaign_check_parser = campaign_sub.add_parser("check")
    campaign_check_parser.add_argument(
        "--contract", default=str(ROOT / "manifests" / "software_m5_eval_contract_rc4.json")
    )
    campaign_check_parser.add_argument("--state-dir", required=True)
    campaign_check_parser.add_argument("--certify", action="store_true")
    campaign_check_parser.add_argument("--output")
    campaign_check_parser.add_argument("--summary-json", action="store_true")
    campaign_report_parser = campaign_sub.add_parser("report")
    campaign_report_parser.add_argument("--input", required=True)
    campaign_report_parser.add_argument("--output")
    certify = sub.add_parser("certify")
    certify.add_argument("--contract", default=str(ROOT / "manifests" / "software_m5_eval_contract_rc4.json"))
    certify.add_argument("--state-dir", required=True)
    certify.add_argument("--output")
    certify.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "repository":
        if args.repository_action == "plan":
            value = repository_plan(_manifest(), Path(args.contract))
        else:
            value = certify_repository_report(_manifest(), Path(args.contract), Path(args.report))
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value.get("status") in ("ready", "fixture-pass", "pass") else 1
    if args.action == "effect":
        value = run_effect_eval(_manifest(), Path(args.contract))
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value.get("status") == "pass" else 1
    if args.action == "campaign":
        if args.campaign_action == "report":
            value = json.loads(Path(args.input).read_text(encoding="utf-8"))
            text = campaign_markdown(value)
            if args.output:
                Path(args.output).write_text(text, encoding="utf-8")
            else:
                print(text, end="")
            return 0
        contract = Path(args.contract).resolve()
        if args.campaign_action == "plan":
            value = campaign_plan(_manifest(), contract)
        elif args.campaign_action == "run":
            if args.execute:
                if args.approve_budget_usd is None:
                    parser.error("--approve-budget-usd is required with campaign run --execute")
                value = run_campaign(
                    _manifest(),
                    contract,
                    Path(args.state_dir),
                    args.approve_budget_usd,
                    args.resume,
                )
            else:
                value = campaign_plan(_manifest(), contract)
        else:
            value = check_campaign(
                _manifest(), contract, Path(args.state_dir), certify=args.certify
            )
        if getattr(args, "output", None):
            _write_json(Path(args.output), value)
        if getattr(args, "summary_json", False) or not getattr(args, "output", None):
            _json(value)
        return 0 if value.get("status") in ("ready", "complete", "pass") else 1
    if args.action == "certify":
        value = check_campaign(_manifest(), Path(args.contract).resolve(), Path(args.state_dir), certify=True)
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value.get("status") == "pass" else 1
    if args.action == "report":
        value = json.loads(Path(args.input).read_text(encoding="utf-8"))
        text = eval_markdown(value)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.action == "compare":
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
        value = compare_runtime_reports(baseline, candidate)
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value["status"] == "pass" else 1
    tasks = load_tasks(Path(args.tasks), args.limit)
    if args.suite == "deterministic":
        value = run_deterministic(_manifest(), tasks)
    else:
        if args.runtime is None:
            parser.error("--runtime is required for runtime suite")
        plan = runtime_plan(args.runtime, args.condition, len(tasks))
        value = (
            run_runtime(_manifest(), tasks, args.runtime, args.condition, model=args.model)
            if args.execute and plan.get("status") == "planned"
            else plan
        )
    if args.output:
        _write_json(Path(args.output), value)
    if args.summary_json or not args.output:
        _json(value)
    return 1 if value.get("status") == "fail" else 0


def _cmd_release(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh release")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("check")
    check.add_argument("--summary-json", action="store_true")
    build = sub.add_parser("build")
    build.add_argument("--version")
    build.add_argument("--out", default="dist")
    build.add_argument("--summary-json", action="store_true")
    publish = sub.add_parser("publish")
    publish.add_argument("--version", required=True)
    publish.add_argument("--backend")
    publish.add_argument("--artifact")
    publish.add_argument("--repository")
    publish.add_argument("--dry-run", action="store_true")
    publish.add_argument("--summary-json", action="store_true")
    rehearse = sub.add_parser("rehearse")
    rehearse.add_argument("--previous-artifact", required=True)
    rehearse.add_argument("--candidate-artifact", required=True)
    rehearse.add_argument("--output")
    rehearse.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "check":
        result = check_release(_manifest())
    elif args.action == "build":
        result = build_release(_manifest(), Path(args.out), args.version)
    elif args.action == "rehearse":
        result = rehearse_release(
            Path(args.previous_artifact).resolve(),
            Path(args.candidate_artifact).resolve(),
        )
        if args.output:
            _write_json(Path(args.output), result)
    else:
        result = publish_release(
            args.version,
            args.backend,
            Path(args.artifact).resolve() if args.artifact else None,
            args.repository,
            args.dry_run,
        )
    if getattr(args, "summary_json", False):
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get("status") == "fail" else 0


def _cmd_goal(argv: Sequence[str]) -> int:
    if not argv or argv[0] != "check":
        raise ManifestError("usage: devkit.sh goal check [--summary-json]")
    return subprocess.call(["bash", str(ROOT / "scripts" / "check-goal-contracts.sh")] + list(argv[1:]), cwd=str(ROOT))


def _cmd_capability(argv: Sequence[str]) -> int:
    if not argv or argv[0] != "health":
        raise ManifestError("usage: devkit.sh capability health [--summary-json]")
    return subprocess.call(["bash", str(ROOT / "scripts" / "check-capability-health.sh")] + list(argv[1:]), cwd=str(ROOT))


def _cmd_harness(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh harness")
    sub = parser.add_subparsers(dest="action", required=True)
    readiness = sub.add_parser("readiness")
    readiness.add_argument("--root", default=".")
    readiness.add_argument(
        "--contract", default=str(ROOT / "manifests" / "harness_readiness_contracts.json")
    )
    readiness.add_argument("--output")
    readiness.add_argument("--summary-json", action="store_true")
    readiness.add_argument("--gate", action="store_true")
    readiness.add_argument(
        "--as-of", help="固定 report-only 评估日期（YYYY-MM-DD）；--gate 强制使用当天"
    )
    args = parser.parse_args(argv)
    as_of = date.fromisoformat(args.as_of) if args.as_of else None
    report = run_harness_readiness(
        Path(args.root),
        Path(args.contract),
        mode="gate" if args.gate else "report-only",
        as_of=as_of,
    )
    markdown = readiness_markdown(report)
    if args.output:
        _write_text(Path(args.output), markdown)
    if args.summary_json:
        _json(report)
    elif not args.output:
        print(markdown, end="")
    else:
        print("Harness readiness {} -> {}".format(report["overall_status"], Path(args.output).resolve()))
    if args.gate and report["overall_status"] != "pass":
        return 2
    return 0


def _cmd_task_cost(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh task-cost")
    parser.add_argument("--task", required=True)
    parser.add_argument("--task-type", choices=sorted(TASK_COST_TYPES), default="general")
    parser.add_argument("--risk-level", choices=("low", "medium", "high"), default="low")
    parser.add_argument("--changed-files", type=int, default=0)
    parser.add_argument("--project-facts", action="store_true")
    parser.add_argument("--long-task", action="store_true")
    parser.add_argument("--shared-contract", action="store_true")
    parser.add_argument("--external-write", action="store_true")
    parser.add_argument("--destructive", action="store_true")
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    receipt = classify_task_cost(
        args.task,
        task_type=args.task_type,
        risk_level=args.risk_level,
        changed_files=args.changed_files,
        project_facts=args.project_facts,
        long_task=args.long_task,
        shared_contract=args.shared_contract,
        external_write=args.external_write,
        destructive=args.destructive,
    )
    receipt["skill_usage"] = validate_skill_usage(receipt, args.skill)
    if args.output:
        _write_json(Path(args.output), receipt)
    if args.summary_json:
        _json(receipt)
    elif not args.output:
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if receipt["skill_usage"]["status"] == "pass" else 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("help", "-h", "--help"):
        _help()
        return 0
    command, rest = argv[0], argv[1:]
    try:
        if command in LEGACY_COMMANDS:
            return _run_legacy(command, rest)
        if command == "validate":
            return _cmd_validate(rest)
        if command == "doctor":
            return _cmd_doctor(rest)
        if command == "catalog":
            return _cmd_catalog(rest)
        if command == "match":
            return _cmd_match(rest)
        if command == "export":
            return _cmd_export(rest)
        if command == "target":
            return _cmd_target(rest)
        if command == "install":
            return _cmd_install(rest)
        if command == "lock":
            return _cmd_lock(rest)
        if command == "benchmark":
            return _cmd_benchmark(rest)
        if command == "security":
            return _cmd_security(rest)
        if command == "eval":
            return _cmd_eval(rest)
        if command == "release":
            return _cmd_release(rest)
        if command == "goal":
            return _cmd_goal(rest)
        if command == "capability":
            return _cmd_capability(rest)
        if command == "harness":
            return _cmd_harness(rest)
        if command == "task-cost":
            return _cmd_task_cost(rest)
        if command == "test":
            return subprocess.call(["bash", str(ROOT / "tests" / "run_all.sh")] + rest, cwd=str(ROOT))
        if command in ("propose", "apply", "verify", "review", "archive"):
            return subprocess.call(["bash", str(ROOT / "scripts" / "workflow.sh"), command] + rest, cwd=str(ROOT))
        print("[FAIL] unknown command: {}".format(command), file=sys.stderr)
        _help()
        return 2
    except TargetUsageError as exc:
        print("[USAGE] {}".format(exc), file=sys.stderr)
        return 2
    except (ManifestError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("[FAIL] {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
