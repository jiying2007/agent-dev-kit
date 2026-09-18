"""CLI adapter for stable Agent Platform primitives."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .model import Manifest
from .agent_platform import (
    aci_benchmark,
    asset_usage_report,
    hooks_report,
    load_contract,
    loop_decision,
    maturity_report,
    portable_skill_audit,
    resolve_effective_profile,
    run_target_conformance,
    target_conformance_plan,
    validate_independent_verifier,
    validate_trace,
    write_json,
)


def _root() -> Path:
    configured = os.environ.get("ADK_ROOT")
    return Path(configured).expanduser().resolve() if configured else Path.cwd().resolve()


def _emit(value: Mapping[str, object], output: Optional[str]) -> int:
    if output:
        write_json(Path(output), value)
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))
    return 0 if value.get("status") in {"pass", "ready", "not-measured"} else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devkit.sh platform")
    sub = parser.add_subparsers(dest="action", required=True)

    maturity = sub.add_parser("maturity")
    maturity.add_argument("--output")

    resolve = sub.add_parser("resolve")
    resolve.add_argument("--profile", action="append", default=[])
    resolve.add_argument("--with-optional-skill", action="append", default=[])
    resolve.add_argument("--target")
    resolve.add_argument("--permission-profile")
    resolve.add_argument("--project-capability", action="append", default=[])
    resolve.add_argument("--session-capability", action="append", default=[])
    resolve.add_argument("--output")

    skills = sub.add_parser("portable-skills")
    skills.add_argument("--output")

    trace = sub.add_parser("trace-validate")
    trace.add_argument("--input", required=True)
    trace.add_argument("--output")

    verifier = sub.add_parser("verifier-validate")
    verifier.add_argument("--input", required=True)
    verifier.add_argument("--output")

    loop = sub.add_parser("loop-decision")
    loop.add_argument("--iterations", type=int, required=True)
    loop.add_argument("--wall-time-seconds", type=float, required=True)
    loop.add_argument("--cost-usd", type=float, required=True)
    loop.add_argument("--tokens", type=int, required=True)
    loop.add_argument("--consecutive-no-progress", type=int, required=True)
    loop.add_argument("--evaluator-pass", action="store_true")
    loop.add_argument("--approval-escape", action="store_true")
    loop.add_argument("--output")

    usage = sub.add_parser("asset-usage")
    usage.add_argument("--telemetry")
    usage.add_argument("--output")

    aci = sub.add_parser("aci")
    aci.add_argument("--metrics", required=True)
    aci.add_argument("--output")

    conformance = sub.add_parser("target-conformance")
    conformance.add_argument("--target", required=True)
    conformance.add_argument("--profile")
    conformance.add_argument("--commands")
    conformance.add_argument("--timeout-seconds", type=int, default=120)
    conformance.add_argument("--output")

    hooks = sub.add_parser("hooks")
    hooks.add_argument("--output")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    root = _root()
    manifest = Manifest.load(root)
    contract = load_contract(root)

    if args.action == "maturity":
        value = maturity_report(manifest, contract)
    elif args.action == "resolve":
        value = resolve_effective_profile(
            manifest,
            contract,
            profiles=args.profile or [manifest.default_profile],
            optional_skills=args.with_optional_skill,
            target=args.target,
            permission_profile=args.permission_profile,
            project_capabilities=args.project_capability,
            session_capabilities=args.session_capability,
        )
    elif args.action == "portable-skills":
        value = portable_skill_audit(manifest, contract)
    elif args.action == "trace-validate":
        value = validate_trace(root, Path(args.input).resolve())
    elif args.action == "verifier-validate":
        value = validate_independent_verifier(root, Path(args.input).resolve())
    elif args.action == "loop-decision":
        value = loop_decision(
            contract,
            iterations=args.iterations,
            wall_time_seconds=args.wall_time_seconds,
            cost_usd=args.cost_usd,
            tokens=args.tokens,
            consecutive_no_progress=args.consecutive_no_progress,
            evaluator_pass=args.evaluator_pass,
            approval_escape=args.approval_escape,
        )
    elif args.action == "asset-usage":
        telemetry = Path(args.telemetry).resolve() if args.telemetry else None
        value = asset_usage_report(manifest, contract, telemetry)
    elif args.action == "aci":
        value = aci_benchmark(contract, Path(args.metrics).resolve())
    elif args.action == "target-conformance":
        if args.commands:
            value = run_target_conformance(
                manifest,
                contract,
                args.target,
                args.profile,
                Path(args.commands).resolve(),
                args.timeout_seconds,
            )
        else:
            value = target_conformance_plan(manifest, contract, args.target, args.profile)
    else:
        value = hooks_report(contract)
    return _emit(value, getattr(args, "output", None))


if __name__ == "__main__":
    raise SystemExit(main())
