"""Native target campaign orchestration and receipt finalization."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import Manifest, ManifestError
from .native_campaign_contract import (
    AUTH_MODES,
    BACKENDS,
    EVIDENCE_SCHEMA,
    FINALIZE_SCHEMA,
    PLAN_SCHEMA,
    STAGES,
    _load_json,
    _validate_commands,
    _validate_schema,
    _write_json,
    prepare_campaign as prepare_campaign,
)
from .native_campaign_execution import run_campaign as run_campaign
from .target_contracts import _authority_digest, _native_contract_digest


def finalize_campaign(
    manifest: Manifest,
    plan: Mapping[str, Any],
    candidate_contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
    receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if plan.get("schema") != PLAN_SCHEMA or evidence.get("schema") != EVIDENCE_SCHEMA:
        raise ManifestError("native_campaign_finalize_input_schema_invalid")
    if evidence.get("status") != "complete":
        raise ManifestError("native_campaign_finalize_requires_complete_campaign")
    if evidence.get("campaign_id") != plan.get("campaign_id"):
        raise ManifestError("native_campaign_finalize_campaign_mismatch")
    from .model import canonical_json_bytes, sha256_bytes

    if sha256_bytes(canonical_json_bytes(candidate_contract)) != plan[
        "candidate_contract_sha256"
    ]:
        raise ManifestError("native_campaign_finalize_candidate_drift")
    contract_digest = _native_contract_digest(candidate_contract)
    if contract_digest != plan["candidate_contract_normalized_sha256"]:
        raise ManifestError("native_campaign_finalize_contract_digest_mismatch")
    try:
        receipt_relative = (
            receipt_path.resolve().relative_to(manifest.root.resolve()).as_posix()
        )
    except ValueError as exc:
        raise ManifestError("native_campaign_finalize_receipt_must_be_within_root") from exc
    if receipt_relative != plan["receipt_path"]:
        raise ManifestError("native_campaign_finalize_receipt_path_mismatch")

    stages = evidence.get("stages")
    if (
        not isinstance(stages, list)
        or [item.get("stage") for item in stages] != list(STAGES)
    ):
        raise ManifestError("native_campaign_finalize_stage_set_invalid")
    receipt_stages = []
    for item in stages:
        if item.get("status") != "pass" or item.get("exit_code") != 0:
            raise ManifestError("native_campaign_finalize_stage_not_passed")
        authority = {
            "execution_authority": plan["authority"]["execution_authority"],
            "authority_id": plan["authority"]["authority_id"],
            "scope": item["stage"],
        }
        authority["attestation_sha256"] = _authority_digest(authority)
        environment = dict(item["environment"])
        environment["contract_sha256"] = contract_digest
        receipt_stages.append(
            {
                "stage": item["stage"],
                "command_sha256": item["command_sha256"],
                "result_sha256": item["result_sha256"],
                "exit_code": 0,
                "started_at": item["started_at"],
                "completed_at": item["completed_at"],
                "duration_ms": item["duration_ms"],
                "environment": environment,
                "privacy": dict(item["privacy"]),
                "authority": authority,
            }
        )
    verified_at = max(item["completed_at"] for item in receipt_stages)
    body = {
        "schema": "adk-native-target-conformance-receipt/v1",
        "target": plan["target"],
        "runtime": dict(plan["runtime"]),
        "bundle_sha256": plan["bundle_sha256"],
        "contract_sha256": contract_digest,
        "verified_at": verified_at,
        "stages": receipt_stages,
    }
    receipt = dict(body)
    receipt["receipt_id"] = "native-{}-{}".format(
        plan["target"], sha256_bytes(canonical_json_bytes(body))[:20]
    )
    _validate_schema(
        receipt,
        manifest.root
        / "schemas"
        / "native-target-conformance-receipt-v1.schema.json",
        "native target conformance receipt",
    )

    final_contract = copy.deepcopy(candidate_contract)
    conformance = final_contract["adapter"]["conformance"]
    receipt_payload = (
        json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        + b"\n"
    )
    receipt_sha = hashlib.sha256(receipt_payload).hexdigest()
    conformance["last_verified_at"] = receipt["verified_at"]
    conformance["evidence"] = [
        {
            "receipt_schema": receipt["schema"],
            "path": receipt_relative,
            "sha256": receipt_sha,
            "target": plan["target"],
            "runtime_version": plan["runtime"]["version"],
            "bundle_sha256": plan["bundle_sha256"],
            "contract_sha256": contract_digest,
            "layer": "runtime",
        }
    ]
    _validate_schema(
        final_contract,
        manifest.root / "manifests" / "target-contract.schema.json",
        "final target contract",
    )
    result = {
        "schema": FINALIZE_SCHEMA,
        "status": "ready-for-signature-and-registry",
        "campaign_id": plan["campaign_id"],
        "target": plan["target"],
        "receipt_id": receipt["receipt_id"],
        "receipt_path": receipt_relative,
        "receipt_sha256": receipt_sha,
        "contract_sha256": contract_digest,
        "bundle_sha256": plan["bundle_sha256"],
        "next_required_evidence": [
            "sigstore-or-reviewed-external-signature-bundle",
            "managed-trust-registry-receipt-binding",
            "production-loader-verification",
            "owner-reviewed-target-contract-promotion",
        ],
        "lifecycle_authority": "none-candidate-only",
        "release_authorized": False,
    }
    return result, receipt, final_contract


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, run and finalize native target campaigns"
    )
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="action", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--target", required=True)
    prepare.add_argument("--profile", default="core")
    prepare.add_argument("--runtime-binary", required=True)
    prepare.add_argument("--runtime-version", required=True)
    prepare.add_argument("--authority-id", required=True)
    prepare.add_argument(
        "--execution-authority",
        choices=("human-approved", "ci-approved"),
        required=True,
    )
    prepare.add_argument("--verification-backend", choices=BACKENDS, required=True)
    prepare.add_argument("--auth-mode", choices=AUTH_MODES, default="none")
    prepare.add_argument("--timeout-seconds", type=int, default=120)
    prepare.add_argument("--commands-json", required=True)
    prepare.add_argument("--receipt-path", required=True)
    prepare.add_argument("--plan-out", required=True)
    prepare.add_argument("--candidate-contract-out", required=True)
    prepare.add_argument("--summary-json", action="store_true")

    run = sub.add_parser("run")
    run.add_argument("--plan", required=True)
    run.add_argument("--candidate-contract", required=True)
    run.add_argument("--commands-json", required=True)
    run.add_argument("--runtime-binary", required=True)
    run.add_argument("--evidence-out", required=True)
    run.add_argument("--summary-json", action="store_true")

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--plan", required=True)
    finalize.add_argument("--candidate-contract", required=True)
    finalize.add_argument("--evidence", required=True)
    finalize.add_argument("--receipt-out", required=True)
    finalize.add_argument("--final-contract-out", required=True)
    finalize.add_argument("--summary-json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        manifest = Manifest.load(Path(args.root).resolve())
        if args.action == "prepare":
            commands = _validate_commands(
                _load_json(Path(args.commands_json), "native campaign commands")
            )
            plan, candidate = prepare_campaign(
                manifest,
                target=args.target,
                profile=args.profile,
                runtime_binary=Path(args.runtime_binary),
                runtime_version=args.runtime_version,
                authority_id=args.authority_id,
                execution_authority=args.execution_authority,
                backend=args.verification_backend,
                auth_mode=args.auth_mode,
                timeout_seconds=args.timeout_seconds,
                commands=commands,
                receipt_path=args.receipt_path,
            )
            _validate_schema(
                plan,
                manifest.root
                / "schemas"
                / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            _write_json(Path(args.plan_out), plan)
            _write_json(Path(args.candidate_contract_out), candidate)
            result = {
                "schema": PLAN_SCHEMA,
                "status": "ready",
                "campaign_id": plan["campaign_id"],
                "plan": str(Path(args.plan_out).resolve()),
                "candidate_contract": str(
                    Path(args.candidate_contract_out).resolve()
                ),
                "candidate_contract_normalized_sha256": plan[
                    "candidate_contract_normalized_sha256"
                ],
                "release_authorized": False,
            }
        elif args.action == "run":
            plan = _load_json(Path(args.plan), "native campaign plan")
            candidate = _load_json(
                Path(args.candidate_contract), "native candidate contract"
            )
            commands = _validate_commands(
                _load_json(Path(args.commands_json), "native campaign commands")
            )
            if not isinstance(plan, dict) or not isinstance(candidate, dict):
                raise ManifestError("native_campaign_run_inputs_must_be_objects")
            _validate_schema(
                plan,
                manifest.root
                / "schemas"
                / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            result = run_campaign(
                manifest,
                plan,
                candidate,
                commands,
                Path(args.runtime_binary),
            )
            _validate_schema(
                result,
                manifest.root
                / "schemas"
                / "native-target-campaign-evidence-v1.schema.json",
                "native campaign evidence",
            )
            _write_json(Path(args.evidence_out), result)
        else:
            plan = _load_json(Path(args.plan), "native campaign plan")
            candidate = _load_json(
                Path(args.candidate_contract), "native candidate contract"
            )
            evidence = _load_json(Path(args.evidence), "native campaign evidence")
            if not all(
                isinstance(value, dict) for value in (plan, candidate, evidence)
            ):
                raise ManifestError(
                    "native_campaign_finalize_inputs_must_be_objects"
                )
            _validate_schema(
                plan,
                manifest.root
                / "schemas"
                / "native-target-campaign-plan-v1.schema.json",
                "native campaign plan",
            )
            _validate_schema(
                evidence,
                manifest.root
                / "schemas"
                / "native-target-campaign-evidence-v1.schema.json",
                "native campaign evidence",
            )
            receipt_path = Path(args.receipt_out)
            active_contract = (
                manifest.root
                / "manifests"
                / "target-contracts"
                / f"{plan['target']}.json"
            )
            if Path(args.final_contract_out).resolve() == active_contract.resolve():
                raise ManifestError(
                    "native_campaign_finalize_must_not_overwrite_active_contract"
                )
            result, receipt, final_contract = finalize_campaign(
                manifest,
                plan,
                candidate,
                evidence,
                receipt_path,
            )
            _write_json(receipt_path, receipt)
            _write_json(Path(args.final_contract_out), final_contract)

        if args.summary_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.action == "run" and result["status"] != "complete":
            return 2
        return 0
    except (ManifestError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "schema": "adk-native-target-campaign-error/v1",
            "status": "fail",
            "error": str(exc),
            "release_authorized": False,
        }
        if getattr(args, "summary_json", False):
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
