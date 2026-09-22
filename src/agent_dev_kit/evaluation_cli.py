"""Evaluation CLI bounded context: deterministic/runtime eval, repository certification and campaigns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .campaign import campaign_markdown, campaign_plan, check_campaign, run_campaign
from .cli_runtime import DEFAULT_TASKS, ROOT, _json, _manifest, _write_json
from .effect_evaluation import run_effect_eval
from .evaluation import (
    compare_runtime_reports,
    eval_markdown,
    load_tasks,
    run_deterministic,
    run_runtime,
    runtime_plan,
)
from .repository_evaluation import certify_repository_report
from .repository_evaluation_contract import repository_plan

DEFAULT_CAMPAIGN_CONTRACT = (ROOT / "manifests" / "software_m5_eval_contract.json").resolve()


def main(argv: Sequence[str] | None = None) -> int:
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
        "--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT)
    )
    campaign_plan_parser.add_argument("--output")
    campaign_plan_parser.add_argument("--summary-json", action="store_true")
    campaign_run_parser = campaign_sub.add_parser("run")
    campaign_run_parser.add_argument(
        "--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT)
    )
    campaign_run_parser.add_argument("--state-dir", required=True)
    campaign_run_parser.add_argument("--execute", action="store_true")
    campaign_run_parser.add_argument("--resume", action="store_true")
    campaign_run_parser.add_argument("--approve-budget-usd", type=float)
    campaign_run_parser.add_argument("--output")
    campaign_run_parser.add_argument("--summary-json", action="store_true")
    campaign_check_parser = campaign_sub.add_parser("check")
    campaign_check_parser.add_argument(
        "--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT)
    )
    campaign_check_parser.add_argument("--state-dir", required=True)
    campaign_check_parser.add_argument("--certify", action="store_true")
    campaign_check_parser.add_argument("--output")
    campaign_check_parser.add_argument("--summary-json", action="store_true")
    campaign_report_parser = campaign_sub.add_parser("report")
    campaign_report_parser.add_argument("--input", required=True)
    campaign_report_parser.add_argument("--output")
    certify = sub.add_parser("certify")
    certify.add_argument("--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT))
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



if __name__ == "__main__":
    raise SystemExit(main())
