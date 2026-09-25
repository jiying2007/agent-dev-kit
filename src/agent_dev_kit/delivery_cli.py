"""Delivery lifecycle CLI bounded context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

from .cli_runtime import _json, _manifest, _write_json
from .compiler import export_assets
from .installation_plan import create_plan, write_plan
from .installation_transaction import apply_plan, rollback
from .locking import clear_target_lock, target_lock_status
from .native_conformance_campaign import run_native_candidate
from .release import (
    build_release,
    build_runtime_bundle,
    check_release,
    publish_release,
    rehearse_release,
)
from .targets import TargetUsageError, check_targets, run_target_smoke


DELIVERY_COMMANDS = frozenset({"export", "target", "install", "lock", "release"})


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
        print(
            "Export {}: {} agents, {} skills -> {}".format(
                result["status"],
                result["agents"],
                result["skills"],
                result["output"],
            )
        )
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
            print(
                "Install plan {}: {} operations, {} conflicts -> {}".format(
                    result["status"],
                    len(result["operations"]),
                    len(result["conflicts"]),
                    args.output,
                )
            )
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
    smoke.add_argument(
        "--stage",
        choices=("discovery", "load", "trigger", "permission"),
        required=True,
    )
    smoke.add_argument("--profile")
    smoke.add_argument("--asset-kind", choices=("agent", "skill"))
    smoke.add_argument("--timeout-seconds", type=int, default=120)
    smoke.add_argument("--summary-json", action="store_true")
    smoke.add_argument("--runtime-command", nargs=argparse.REMAINDER, default=[])
    native = sub.add_parser("native-campaign")
    native.add_argument("--target", required=True)
    native.add_argument("--profile")
    native.add_argument("--runtime-binary", required=True)
    native.add_argument("--runtime-name", required=True)
    native.add_argument("--runtime-version", required=True)
    native.add_argument("--commands", required=True)
    native.add_argument("--authority-id", required=True)
    native.add_argument("--execution-authority", choices=("human-approved", "ci-approved"), required=True)
    native.add_argument(
        "--verification-backend",
        choices=("external-signature-verifier", "ci-provenance-verifier"),
        required=True,
    )
    native.add_argument("--output", required=True)
    native.add_argument("--timeout-seconds", type=int, default=120)
    native.add_argument("--max-output-bytes", type=int, default=1024 * 1024)
    native.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    manifest = _manifest()
    if args.action == "check":
        result = check_targets(manifest, None if args.all else args.target)
    elif args.action == "smoke":
        result = run_target_smoke(
            manifest,
            args.target,
            args.stage,
            args.runtime_command,
            profile=args.profile,
            asset_kind=args.asset_kind,
            timeout_seconds=args.timeout_seconds,
        )
    else:
        result = run_native_candidate(
            manifest,
            target=args.target,
            profile=args.profile or manifest.default_profile,
            runtime_binary=Path(args.runtime_binary),
            runtime_name=args.runtime_name,
            runtime_version=args.runtime_version,
            commands_path=Path(args.commands),
            authority_id=args.authority_id,
            execution_authority=args.execution_authority,
            verification_backend=args.verification_backend,
            output=Path(args.output),
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
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


def _cmd_release(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh release")
    sub = parser.add_subparsers(dest="action", required=True)
    check = sub.add_parser("check")
    check.add_argument("--summary-json", action="store_true")
    build = sub.add_parser("build")
    build.add_argument("--version")
    build.add_argument("--out", default="dist")
    build.add_argument("--allow-unbound-snapshot", action="store_true")
    build.add_argument("--summary-json", action="store_true")
    runtime_build = sub.add_parser("runtime-build")
    runtime_build.add_argument("--version")
    runtime_build.add_argument("--profile", default="team-core")
    runtime_build.add_argument("--with-optional-skill", action="append", default=[])
    runtime_build.add_argument("--out", default="dist")
    runtime_build.add_argument("--summary-json", action="store_true")
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
        result = build_release(
            _manifest(),
            Path(args.out),
            args.version,
            args.allow_unbound_snapshot,
        )
    elif args.action == "runtime-build":
        result = build_runtime_bundle(
            _manifest(),
            Path(args.out),
            args.profile,
            args.version,
            args.with_optional_skill,
        )
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in DELIVERY_COMMANDS:
        raise ValueError(
            "delivery CLI requires one of: " + ", ".join(sorted(DELIVERY_COMMANDS))
        )
    command, rest = args[0], args[1:]
    try:
        if command == "export":
            return _cmd_export(rest)
        if command == "target":
            return _cmd_target(rest)
        if command == "install":
            return _cmd_install(rest)
        if command == "lock":
            return _cmd_lock(rest)
        return _cmd_release(rest)
    except TargetUsageError as exc:
        print("[USAGE] {}".format(exc), file=sys.stderr)
        return 2
