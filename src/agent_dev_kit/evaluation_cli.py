"""Evaluation CLI bounded context: deterministic/runtime eval, repository certification and campaigns."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

from .campaign import campaign_plan, check_campaign, run_campaign
from .campaign_model import campaign_markdown
from .cli_runtime import DEFAULT_TASKS, ROOT, _json, _manifest, _write_json
from .effect_campaign_materializer import materialize_effect_campaign
from .effect_evaluation import run_effect_eval
from .effect_trials import compare_effect_trial_file
from .model import ManifestError
from .evaluation import eval_markdown, run_runtime, runtime_plan
from .evaluation_runtime import compare_runtime_reports, load_tasks, run_deterministic
from .repository_evaluation import certify_repository_report
from .repository_evaluation_contract import repository_plan
from .strict_json import read as read_json
from .boundary_rehearsal import rehearse
from .task_evidence import import_task_evidence
from .task_trials import compare_task_trials

DEFAULT_CAMPAIGN_CONTRACT = (ROOT / "manifests" / "software_m5_eval_contract.json").resolve()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="devkit.sh eval")
    sub = parser.add_subparsers(dest="action", required=True)
    boundaries = sub.add_parser("boundaries", help="Run deterministic, non-executing tool/MCP fault rehearsals")
    boundaries.add_argument("--summary-json", action="store_true")
    run = sub.add_parser("run")
    run.add_argument("--suite", choices=("deterministic", "runtime"), default="deterministic")
    run.add_argument("--tasks", default=str(DEFAULT_TASKS))
    run.add_argument("--limit", type=int)
    run.add_argument("--runtime", choices=("codex", "claude"))
    run.add_argument("--model")
    run.add_argument("--condition", choices=("baseline", "adk"), default="adk")
    run.add_argument("--execute", action="store_true")
    run.add_argument("--approve-budget-usd", type=float)
    run.add_argument("--approve-unknown-cost", action="store_true")
    run.add_argument("--max-new-results", type=int)
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
    trials = sub.add_parser("compare-trials")
    trials.add_argument("--input", required=True)
    trials.add_argument("--output")
    trials.add_argument("--summary-json", action="store_true")
    task_import = sub.add_parser("import-task", help="Import bounded local task observations without execution")
    task_import.add_argument("--input", required=True)
    task_import.add_argument("--output")
    task_import.add_argument("--summary-json", action="store_true")
    task_trials = sub.add_parser("compare-task-trials", help="Check task input/state/assignment, then compare complete trials")
    task_trials.add_argument("--input", required=True)
    task_trials.add_argument("--output")
    task_trials.add_argument("--summary-json", action="store_true")
    task_grade = sub.add_parser("grade-task", help="Check development task artifacts without executing candidates")
    task_grade.add_argument("--case", required=True)
    task_grade.add_argument("--workspace", required=True)
    task_grade.add_argument("--output", required=True)
    task_grade.add_argument("--run-id", required=True)
    task_grade.add_argument("--executor-id", required=True)
    task_grade.add_argument("--grader-id", required=True)
    task_grade.add_argument("--summary-json", action="store_true")
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
    campaign_plan_parser.add_argument("--campaign-root")
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
    campaign_run_parser.add_argument("--max-new-results", type=int)
    campaign_run_parser.add_argument("--campaign-root")
    campaign_run_parser.add_argument("--output")
    campaign_run_parser.add_argument("--summary-json", action="store_true")
    campaign_check_parser = campaign_sub.add_parser("check")
    campaign_check_parser.add_argument(
        "--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT)
    )
    campaign_check_parser.add_argument("--state-dir", required=True)
    campaign_check_parser.add_argument("--certify", action="store_true")
    campaign_check_parser.add_argument("--campaign-root")
    campaign_check_parser.add_argument("--output")
    campaign_check_parser.add_argument("--summary-json", action="store_true")
    campaign_materialize_parser = campaign_sub.add_parser("materialize-effect")
    campaign_materialize_parser.add_argument(
        "--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT)
    )
    campaign_materialize_parser.add_argument("--state-dir", required=True)
    campaign_materialize_parser.add_argument("--effect-plan", required=True)
    campaign_materialize_parser.add_argument("--runtime", choices=("codex", "claude"), required=True)
    campaign_materialize_parser.add_argument("--campaign-root")
    campaign_materialize_parser.add_argument("--output")
    campaign_materialize_parser.add_argument("--summary-json", action="store_true")
    campaign_report_parser = campaign_sub.add_parser("report")
    campaign_report_parser.add_argument("--input", required=True)
    campaign_report_parser.add_argument("--output")
    certify = sub.add_parser("certify")
    certify.add_argument("--contract", default=str(DEFAULT_CAMPAIGN_CONTRACT))
    certify.add_argument("--state-dir", required=True)
    certify.add_argument("--campaign-root")
    certify.add_argument("--output")
    certify.add_argument("--summary-json", action="store_true")
    args = parser.parse_args(argv)
    if args.action in {"import-task", "grade-task", "compare-task-trials"}:
        try:
            if args.action == "import-task":
                value = import_task_evidence(Path(args.input), _manifest(),
                                             output_path=Path(args.output) if args.output else None)
            elif args.action == "compare-task-trials":
                value = compare_task_trials(Path(args.input), _manifest(),
                                            output_path=Path(args.output) if args.output else None)
            else:
                from .task_acceptance import grade_task_artifacts

                value = grade_task_artifacts(
                    Path(args.case), Path(args.workspace), Path(args.output),
                    run_id=args.run_id, executor_id=args.executor_id, grader_id=args.grader_id,
                )
        except (ManifestError, OSError, ValueError, RecursionError, OverflowError):
            # Never echo raw paths, event text, or invalid JSON from an untrusted package.
            value = {
                "schema_version": {"import-task": "adk-task-evidence-import/v1",
                                   "compare-task-trials": "adk-task-trial-comparison/v1",
                                   "grade-task": "adk-task-acceptance-error/v1"}[args.action],
                "status": "invalid", "reason": "invalid-input-or-evidence",
                "trust": "caller-observed", "evidence_scope": "test-only",
                "quality_evidence_eligible": False, "release_authorized": False, "raw_content_stored": False,
            }
        if args.summary_json or not args.output or value["status"] == "invalid":
            _json(value)
        if args.action == "compare-task-trials" and value["status"] == "compared":
            return {"improved": 0, "non-inferior": 0, "regressed": 1}.get(value["verdict"], 2)
        return 0 if value["status"] in {"imported", "passed"} else 2 if value["status"] == "invalid" else 1
    if args.action == "boundaries":
        value = rehearse()
        _json(value)
        return 0 if value["status"] == "pass" else 1
    if args.action == "compare-trials":
        try:
            value = compare_effect_trial_file(Path(args.input), _manifest())
        except (ManifestError, OSError, ValueError, RecursionError):
            value = {
                "schema_version": "adk-effect-trial-comparison/v1",
                "verdict": "invalid", "reason": "invalid-input-or-evidence",
                "evidence_scope": "test-only", "quality_evidence_eligible": False,
                "owner_review_required": True, "lifecycle_authority": "none-evidence-only",
                "release_authorized": False, "raw_content_stored": False,
            }
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return {"improved": 0, "non-inferior": 0, "regressed": 1}.get(value["verdict"], 2)
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
            value = read_json(Path(args.input))
            text = campaign_markdown(value)
            if args.output:
                Path(args.output).write_text(text, encoding="utf-8")
            else:
                print(text, end="")
            return 0
        campaign_root = (
            Path(args.campaign_root).expanduser()
            if getattr(args, "campaign_root", None)
            else None
        )
        raw_contract = Path(args.contract).expanduser()
        contract = (
            (campaign_root / raw_contract).resolve()
            if campaign_root is not None and not raw_contract.is_absolute()
            else raw_contract.resolve()
        )
        if args.campaign_action == "materialize-effect":
            value = materialize_effect_campaign(
                _manifest(),
                contract,
                Path(args.state_dir),
                Path(args.effect_plan),
                args.runtime,
                campaign_root=campaign_root,
            )
            if args.output:
                _write_json(Path(args.output), value)
            if args.summary_json or not args.output:
                _json(value)
            return 0
        if args.campaign_action == "plan":
            value = campaign_plan(_manifest(), contract, campaign_root)
        elif args.campaign_action == "run":
            if args.max_new_results is not None and not args.execute:
                parser.error("--max-new-results requires campaign run --execute")
            if args.execute:
                if args.approve_budget_usd is None:
                    parser.error("--approve-budget-usd is required with campaign run --execute")
                value = run_campaign(
                    _manifest(),
                    contract,
                    Path(args.state_dir),
                    args.approve_budget_usd,
                    args.resume,
                    args.max_new_results,
                    campaign_root=campaign_root,
                )
            else:
                value = campaign_plan(_manifest(), contract, campaign_root)
        else:
            value = check_campaign(
                _manifest(),
                contract,
                Path(args.state_dir),
                certify=args.certify,
                campaign_root=campaign_root,
            )
        if getattr(args, "output", None):
            _write_json(Path(args.output), value)
        if getattr(args, "summary_json", False) or not getattr(args, "output", None):
            _json(value)
        return 0 if value.get("status") in ("ready", "checkpointed", "complete", "pass") else 1
    if args.action == "certify":
        campaign_root = (
            Path(args.campaign_root).expanduser()
            if args.campaign_root
            else None
        )
        raw_contract = Path(args.contract).expanduser()
        contract = (
            (campaign_root / raw_contract).resolve()
            if campaign_root is not None and not raw_contract.is_absolute()
            else raw_contract.resolve()
        )
        value = check_campaign(
            _manifest(),
            contract,
            Path(args.state_dir),
            certify=True,
            campaign_root=campaign_root,
        )
        if args.output:
            _write_json(Path(args.output), value)
        if args.summary_json or not args.output:
            _json(value)
        return 0 if value.get("status") == "pass" else 1
    if args.action == "report":
        value = read_json(Path(args.input))
        text = eval_markdown(value)
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.action == "compare":
        baseline = read_json(Path(args.baseline))
        candidate = read_json(Path(args.candidate))
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
        if args.execute:
            if args.max_new_results is None or not 0 < args.max_new_results <= len(tasks):
                parser.error("runtime --execute requires --max-new-results between 1 and the task count")
            if not args.model:
                parser.error("runtime --execute requires --model for comparable reports")
            if args.runtime == "claude":
                if (args.approve_budget_usd is None or not math.isfinite(args.approve_budget_usd)
                        or args.approve_budget_usd < args.max_new_results * 0.25):
                    parser.error("Claude runtime requires a budget covering 0.25 USD per selected result")
            elif not args.approve_unknown_cost:
                parser.error("Codex runtime requires --approve-unknown-cost with a result count cap")
            tasks = tasks[:args.max_new_results]
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
