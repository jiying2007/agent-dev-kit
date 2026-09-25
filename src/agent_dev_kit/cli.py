"""Public ADK command-line interface."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Optional, Sequence

from .catalog_contract import main as catalog_main
from .cli_runtime import (
    ROOT,
    _help,
    _json,
    _manifest,
    _write_json,
    _write_text,
)
from .contracts.manifest_composition import composition_check
from .doctor import run_doctor
from .delivery_cli import main as delivery_main
from .evaluation_cli import main as evaluation_main
from .matcher import main as matcher_main
from .agent_platform_cli import main as platform_main
from .phase_context import main as phase_context_main
from .profile_context_footprint import main as profile_context_footprint_main
from .skill_relationships import main as skill_relationships_main
from .model import ManifestError, canonical_json_bytes, sha256_bytes
from .quality import benchmark_markdown, run_benchmark, security_check
from .readiness import readiness_markdown, run_harness_readiness
from .task_cost import TASK_TYPES as TASK_COST_TYPES
from .task_cost import classify_task_cost, validate_skill_usage
from .validation_contract import validate_repository


def _cmd_manifest(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh manifest")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("composition-check")
    check.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)

    manifest = _manifest()
    policy = json.loads(
        (ROOT / "manifests" / "manifest_composition_policy.json").read_text(encoding="utf-8")
    )
    result = composition_check(
        manifest.data,
        policy,
        source_digest=manifest.digest,
        source_is_canonical=manifest.source == (ROOT / "manifest.json").resolve(),
        digest=lambda value: sha256_bytes(canonical_json_bytes(value)),
    )
    if args.summary_json:
        _json(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


def _cmd_validate(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh validate")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)

    result = validate_repository(ROOT, strict=args.strict, quick=args.quick)
    if args.summary_json:
        _json(result)
    elif result["status"] == "pass":
        print(
            "Validation passed. strict={} quick={}".format(
                int(args.strict),
                int(args.quick),
            )
        )
    else:
        for failure in result.get("failures", []):
            print("[FAIL] {}".format(failure), file=sys.stderr)
    return 0 if result["status"] == "pass" else 1

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
    return catalog_main([*list(argv), "--root", str(ROOT)])


def _cmd_match(argv: Sequence[str]) -> int:
    return matcher_main(argv)


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
        if command == "manifest":
            return _cmd_manifest(rest)
        if command == "validate":
            return _cmd_validate(rest)
        if command == "doctor":
            return _cmd_doctor(rest)
        if command == "catalog":
            return _cmd_catalog(rest)
        if command == "match":
            return _cmd_match(rest)
        if command == "phase-context":
            phase_args = rest if "--root" in rest else ["--root", str(ROOT), *rest]
            return phase_context_main(phase_args)
        if command == "profile-footprint":
            footprint_args = rest if "--root" in rest else ["--root", str(ROOT), *rest]
            return profile_context_footprint_main(footprint_args)
        if command == "skill-relationships":
            relationship_args = rest if "--root" in rest else ["--root", str(ROOT), *rest]
            return skill_relationships_main(relationship_args)
        if command == "platform":
            return platform_main(rest)
        if command in ("export", "target", "install", "lock", "release"):
            return delivery_main([command, *rest])
        if command == "benchmark":
            return _cmd_benchmark(rest)
        if command == "security":
            return _cmd_security(rest)
        if command == "eval":
            return evaluation_main(rest)
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
    except (ManifestError, OSError, ValueError, json.JSONDecodeError) as exc:
        print("[FAIL] {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
